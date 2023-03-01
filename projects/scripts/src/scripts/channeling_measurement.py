import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List

from mill.logbook_db import LogBookDb
from mill.recipe_meta import RecipeMeta
from waspy.iba.file_handler import FileHandler
from waspy.iba.rbs_entities import CoordinateRange, Window, PositionCoordinates, \
    get_positions_as_float, get_rbs_journal, RecipeType, RbsChanneling, \
    ChannelingJournal, AysJournal, AysFitResult
from waspy.iba.rbs_recipes import get_sum, \
    save_channeling_graphs_to_disk, save_rbs_journal_with_file_stem, run_rbs_recipe, find_minimum, \
    convert_float_to_coordinate, save_ays_journal
from waspy.iba.rbs_setup import RbsSetup
from mill.config import make_mill_config


log_label = "[WASPY.SCRIPTS.CHANNELING_MEASUREMENT]"


def ays_report_cb(ays_result: AysJournal):
    if not ays_result.fit.success:
        logging.error(f"{log_label} Fit failure")


def user_interaction(fit_result: AysFitResult, coordinate_range: CoordinateRange):
    if fit_result.success:
        logging.info(f"{log_label} Minimum found at {coordinate_range.name}={fit_result.minimum}")
        agree = input(f"Agree with minimum {coordinate_range.name}={fit_result.minimum}? [Y/N]")
        if agree == 'N':
            new_minimum = float(input("What should be the minimum?"))
            fit_result.minimum = new_minimum
    else:
        new_minimum = float(input("What should be the minimum?"))
        fit_result.minimum = new_minimum
    rbs_setup.move(convert_float_to_coordinate(coordinate_range.name, fit_result.minimum))


def run_ays() -> List[AysJournal]:
    """ays: angular yield scan"""
    start_time = datetime.now()
    result = []
    logging.info(f"{log_label} YIELD COORD RANGES {recipe.yield_coordinate_ranges}")
    for ays_index, coordinate_range in enumerate(recipe.yield_coordinate_ranges):
        rbs_journals = []
        yields = []
        angles = get_positions_as_float(coordinate_range)
        for angle in angles:
            single = CoordinateRange.init_single(coordinate_range.name, angle)
            ays_step_start_time = datetime.now()
            rbs_data = run_rbs_recipe(single, recipe.yield_charge_total, rbs_setup)
            rbs_journal = get_rbs_journal(rbs_data, ays_step_start_time)
            rbs_journals.append(rbs_journal)
            yields.append(get_sum(rbs_journal.histograms[recipe.yield_optimize_detector_identifier],
                                  recipe.yield_integration_window))
        fit_result = find_minimum(angles, yields)

        user_interaction(fit_result, coordinate_range)

        ays_journal = AysJournal(start_time=start_time, end_time=datetime.now(), rbs_journals=rbs_journals,
                                 fit=fit_result)
        result.append(ays_journal)
        if ays_report_cb:
            ays_report_cb(result[-1])
        save_ays_journal(file_handler, recipe, ays_journal, ays_index, recipe_meta_data)

    return result


def run_channeling() -> ChannelingJournal:
    rbs_setup.move(recipe.start_position)

    logging.info(f"{log_label} Start ays")
    ays = run_ays()

    logging.info(f"{log_label} Start Fixed")
    start_time = datetime.now()
    rbs_setup.prepare_acquisition()
    fixed_data = rbs_setup.acquire_data(recipe.compare_charge_total)
    fixed = get_rbs_journal(fixed_data, start_time)
    save_rbs_journal_with_file_stem(file_handler, recipe.name + "_fixed", recipe, fixed, recipe_meta_data)

    logging.info(f"{log_label} Start Random")
    rbs_setup.move(PositionCoordinates(theta=-2))
    start_time = datetime.now()
    random_data = run_rbs_recipe(recipe.random_coordinate_range, recipe.compare_charge_total, rbs_setup)
    random = get_rbs_journal(random_data, start_time)
    save_rbs_journal_with_file_stem(file_handler, recipe.name + "_random", recipe, random, recipe_meta_data)

    return ChannelingJournal(random=random, fixed=fixed, ays=ays, title=recipe.name)


if __name__ == "__main__":
    """
    =============================== EDITABLE ==========================================
    Configuration of measurement

    * config_file:      File with URLs of drivers and directories
    * logbook_url:      URL of logbook (required for recipe meta data)
    * recipe_meta_dir:  Path to rbs_recipe_meta_template.txt, where meta data is stored
    * local_dir:        Local directory to save data files in
    * remote_dir:       Remote directory to save data files in
    * base_folder:      Sub-folder in local_dir and remote_dir
    """
    development_mode = 1  # 0: lab measurements, 1: development
    if development_mode:
        logging.info(
            f"{log_label} You are running this script in development mode!")
        config_file = "../../../mill/default_config.toml"
        logbook_url = "http://127.0.0.1:8001"
        mill_config = make_mill_config(config_file)  # Do not modify!
        local_dir = mill_config.rbs.local_dir  # Linux
        remote_dir = mill_config.rbs.remote_dir  # Linux
    else:
        config_file = "../../../mill/lab_config_win.toml"  # Windows PC
        logbook_url = "https://db.capitan.imec.be"
        local_dir = Path(r"C:\git\data")
        remote_dir = Path(r"\\winbe.imec.be\wasp\transfer_RBS")
        mill_config = make_mill_config(config_file)  # Do not modify!

    recipe_meta_dir = Path('../../../mill/recipe_meta')
    logbook_db = LogBookDb(logbook_url)  # Do not modify!

    """
    Recipe parameters

    Following fields are optional, i.e. you can leave them out if they don't need to change
     - start_position
     - all coordinates in PositionCoordinates
    """
    recipe = RbsChanneling(
        type=RecipeType.CHANNELING,
        sample="sample1",
        name="name1",
        start_position=PositionCoordinates(x=9, y=14, phi=0, zeta=0.15, detector=170, theta=11),
        yield_charge_total=6000,
        yield_coordinate_ranges=[
            CoordinateRange(name="zeta", start=-2, end=2, increment=0.5),
            CoordinateRange(name="theta", start=-2, end=2, increment=0.5),
            CoordinateRange(name="zeta", start=-2, end=2, increment=0.5),
            CoordinateRange(name="theta", start=-2, end=2, increment=0.5)
        ],
        yield_integration_window=Window(start=700, end=750),
        yield_optimize_detector_identifier="d01",
        compare_charge_total=10000,
        random_coordinate_range=CoordinateRange(name="phi", start=-2, end=2, increment=0.2),
        fit_algorithm_type="minimum_yield"
    )
    """
    ===================================================================================
    ===================================================================================
    """

    rbs_setup = RbsSetup(mill_config.rbs.get_driver_urls())
    rbs_setup.configure_detectors(mill_config.rbs.drivers.caen.detectors)
    file_handler = FileHandler(local_dir, remote_dir)
    file_handler.set_base_folder(recipe.name)
    recipe_meta_data = RecipeMeta(logbook_db, recipe_meta_dir)
    logging.info(
        f"{log_label} Files are saved in {os.path.join(local_dir, recipe.name)} and {os.path.join(remote_dir, recipe.name)}")

    recipe_meta_data = recipe_meta_data.fill_rbs_recipe_meta()
    journal = run_channeling()
    save_channeling_graphs_to_disk(file_handler, journal, recipe.name)
