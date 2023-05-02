import logging
import copy
from datetime import datetime, timedelta
from typing import List, Dict

from mill.erd_entities import ErdJobModel, ErdRecipe, make_erd_status
from mill.logbook_db import LogBookDb
from mill.recipe_meta import RecipeMeta
from waspy.iba.erd_recipes import run_erd_recipe, save_erd_journal
from waspy.iba.erd_setup import ErdSetup
from waspy.iba.file_handler import FileHandler

from mill.job import Job

empty_erd_recipe = ErdRecipe(measuring_time_sec=0, type="erd", sample="", name="", theta=0, z_start=0, z_end=0,
                             z_increment=0, z_repeat=0)


class ErdJob(Job):
    _erd_setup: ErdSetup
    _job_model: ErdJobModel
    _active_recipe: ErdRecipe
    _recipe_start_time: datetime
    _finished_recipes: List
    _running: bool
    _file_handler: FileHandler
    _db: LogBookDb
    _time_loaded: datetime
    _cancelled: bool
    _recipe_meta: RecipeMeta

    def __init__(self, job_model: ErdJobModel, erd_setup: ErdSetup, file_handler: FileHandler, log_book_db: LogBookDb,
                 recipe_meta: RecipeMeta):
        self._job_model = job_model
        self._erd_setup = erd_setup
        self._run_time = timedelta(0)
        self._active_recipe = copy.deepcopy(empty_erd_recipe)
        self._finished_recipes = []
        self._running = False
        self._file_handler = file_handler
        self._recipe_start_time = datetime.now()
        self._db = log_book_db
        self._cancelled = False
        self._recipe_meta = recipe_meta

    def setup(self) -> None:
        self._file_handler.set_base_folder(self._job_model.name)
        self._db.job_start(self._job_model)
        self._erd_setup.resume()
        self._erd_setup.reupload_cnf()

    def exec(self):
        """ Can raise: AbortedError, HardwareError"""
        self._time_loaded = datetime.now()
        for recipe in self._job_model.recipes:
            self._run_recipe(recipe)
            self._finish_recipe()

    def teardown(self):
        trends = self._db.get_trends(self._time_loaded, datetime.now(), "erd")
        self._file_handler.write_csv_panda_to_disk("erd_trends.csv", trends)
        trends = self._db.get_trends(self._time_loaded, datetime.now(), "any")
        self._file_handler.write_csv_panda_to_disk("any_trends.csv", trends)
        self._file_handler.write_json_to_disk("job.json", self.serialize())
        self._db.job_finish(self._job_model)
        self._erd_setup.resume()

    def terminate(self, message: str) -> None:
        self._db.job_terminate(self._job_model.name, message)

    def serialize(self):
        active_recipe_status = make_erd_status(self._active_recipe, self.get_recipe_progress(), self._recipe_start_time)
        status = {"job": self._job_model.dict(), "active_recipe": active_recipe_status.dict(),
                  "finished_recipes": self._finished_recipes}
        return status

    def get_recipe_progress(self):
        measuring_time = int(float(self._erd_setup.get_measuring_time()))
        total_time = int(self._active_recipe.measuring_time_sec)
        progress = round(measuring_time / total_time * 100, 2) if self._running else 0
        return f'{progress:02}'

    def cancel(self):
        logging.info("[WASPY.MILL.RBS_JOB] cancelled during recipe {" + str(self._active_recipe) + "}")
        self._erd_setup.cancel()
        self._cancelled = True

    def _run_recipe(self, recipe):
        self._active_recipe = recipe
        self._recipe_start_time = datetime.now()
        self._running = True

        erd_journal = run_erd_recipe(recipe, self._erd_setup)
        extra = self._recipe_meta.fill_erd_recipe_meta()
        save_erd_journal(self._file_handler, recipe, erd_journal, extra)
        self._running = False

    def _finish_recipe(self):
        finished_recipe_status = make_erd_status(self._active_recipe, 100, self._recipe_start_time)
        self._finished_recipes.append(finished_recipe_status.dict())
        self._active_recipe = empty_erd_recipe
