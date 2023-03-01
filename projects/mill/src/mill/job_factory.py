import logging
from io import StringIO
from typing import Union, Dict, List

import pandas as pd

from mill.erd_entities import ErdJobModel
from mill.erd_job import ErdJob
from mill.logbook_db import LogBookDb
from mill.recipe_meta import RecipeMeta
from waspy.iba.erd_setup import ErdSetup
from mill.rbs_entities import RbsJobModel
from mill.rbs_job import RbsJob
from waspy.iba.file_handler import FileHandler
from waspy.iba.rbs_entities import PositionCoordinates, CoordinateRange
from waspy.iba.rbs_setup import RbsSetup


class JobFactory:
    def __init__(self, rbs_setup: RbsSetup, rbs_file_handler: FileHandler, erd_setup: ErdSetup,
                 erd_file_handler: FileHandler, db: LogBookDb, recipe_meta: RecipeMeta):
        self._rbs_setup = rbs_setup
        self._rbs_file_writer = rbs_file_handler
        self._rbs_metadata = {}
        self._erd_setup = erd_setup
        self._erd_file_writer = erd_file_handler
        self._erd_metadata = {}
        self._db = db
        self._recipe_meta = recipe_meta

    def make_rbs_job(self, job_model: RbsJobModel):
        return RbsJob(job_model, self._rbs_setup, self._rbs_file_writer, self._db, self._recipe_meta)

    def set_rbs_metadata_template(self, keys: Dict):
        self._rbs_metadata = keys

    def set_erd_metadata_template(self, keys: Dict):
        self._erd_metadata = keys

    def make_erd_job(self, job_model: ErdJobModel):
        return ErdJob(job_model, self._erd_setup, self._erd_file_writer, self._db, self._recipe_meta)

    def make_job_model_from_csv(self, contents) -> Union[RbsJobModel, ErdJobModel]:
        sections = get_sections(contents)
        top_section = sections[0][0]
        settings = top_section

        if settings["job_type"] == "erd":
            recipes_section = sections[1]
            print(recipes_section)
            settings["recipes"] = parse_erd_recipes(recipes_section)
            return ErdJobModel.parse_obj(settings)

        elif settings["job_type"] == "rbs":
            recipes_section = sections[1]
            settings["recipes"] = parse_rbs_recipes(recipes_section, self._rbs_setup)
            return RbsJobModel.parse_obj(settings)


def convert_csv_to_dict(csv) -> Dict:
    dataframe = pd.read_csv(StringIO(csv))
    dataframe = dataframe.dropna(how='all', axis='columns')
    data = dataframe.to_dict('records')
    return data


def get_sections(csv_text: str) -> List:
    section_text = ""
    sections = []
    for line in csv_text.splitlines(keepends=True):
        if not line.startswith(",,"):
            section_text += line
        else:
            sections.append(convert_csv_to_dict(section_text))
            section_text = ""

    sections.append(convert_csv_to_dict(section_text))

    return sections


def drop_nan(data: Dict) -> Dict:
    return {k: v for k, v in data.items() if pd.notnull(v)}


def parse_erd_recipes(recipes_section):
    recipes = []
    for recipe in recipes_section:
        recipes.append(drop_nan(recipe))
    return recipes


def parse_rbs_recipes(recipes_section, rbs_setup: RbsSetup):
    recipes = []

    for input_recipe in recipes_section:
        if input_recipe["type"] == "rbs_random":
            recipes.append(parse_random_recipe(input_recipe))
        elif input_recipe["type"] == "rbs_channeling":
            recipe = parse_channeling_recipe(input_recipe)
            rbs_setup.get_detector(recipe["yield_optimize_detector_identifier"])
            recipes.append(recipe)
        elif input_recipe["type"] == "rbs_channeling_map":
            recipe = parse_channeling_map_recipe(input_recipe)
            recipes.append(recipe)
    return recipes


def parse_random_recipe(recipe_section: Dict) -> Dict:
    setting = drop_nan(recipe_section)
    convert_coordinates_to_position("start_position", setting)
    setting["coordinate_range"] = CoordinateRange(name="phi", start=0, end=30, increment=2).dict()
    return setting


def parse_channeling_recipe(recipe_section: Dict) -> Dict:
    setting = drop_nan(recipe_section)
    convert_coordinates_to_position("start_position", setting)
    setting["compare_charge_total"] = setting['charge_total']
    setting.pop("charge_total")
    setting["yield_coordinate_ranges"] = [
        {"name": "zeta", "start": -2, "end": 2, "increment": 0.2},
        {"name": "theta", "start": -2, "end": 2, "increment": 0.2},
        {"name": "zeta", "start": -2, "end": 2, "increment": 0.2},
        {"name": "theta", "start": -2, "end": 2, "increment": 0.2},
    ]
    setting["yield_charge_total"] = setting["ays_charge"]
    setting.pop("ays_charge")
    setting["yield_optimize_detector_identifier"] = setting["ays_detector_identifier"]
    setting.pop("ays_detector_identifier")
    setting["random_coordinate_range"] = {"name": "phi", "start": 0, "end": 30, "increment": 2}
    setting["yield_integration_window"] = {}
    setting["yield_integration_window"]["start"] = setting["ays_window_start"]
    setting.pop("ays_window_start")
    setting["yield_integration_window"]["end"] = setting["ays_window_end"]
    setting.pop("ays_window_end")
    try:
        setting["fit_algorithm_type"] = setting["fit_algorithm_type"]
    except KeyError:
        setting["fit_algorithm_type"] = "lower_fit"

    return setting


def parse_channeling_map_recipe(recipe_section: Dict) -> Dict:
    setting = drop_nan(recipe_section)
    convert_coordinates_to_position("start_position", setting)
    setting["zeta_coordinate_range"] = {"name": "zeta", "start": setting["zeta_start"], "end": setting["zeta_end"],
                                        "increment": setting["zeta_increment"]}
    setting["theta_coordinate_range"] = {"name": "theta", "start": setting["theta_start"], "end": setting["theta_end"],
                                         "increment": setting["theta_increment"]}
    setting.pop("zeta_start")
    setting.pop("theta_start")
    setting.pop("zeta_end")
    setting.pop("theta_end")
    setting.pop("zeta_increment")
    setting.pop("theta_increment")
    setting["yield_integration_window"] = {"start": setting["yield_window_start"], "end": setting["yield_window_end"]}
    setting.pop("yield_window_start")
    setting.pop("yield_window_end")
    return setting


def convert_coordinates_to_position(position_key, setting):
    setting[position_key] = PositionCoordinates.parse_obj(setting).dict()
    setting.pop("x", None)
    setting.pop("y", None)
    setting.pop("phi", None)
    setting.pop("zeta", None)
    setting.pop("det", None)
    setting.pop("theta", None)
