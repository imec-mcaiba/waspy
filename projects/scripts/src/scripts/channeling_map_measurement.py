import os
import logging
from datetime import datetime
from pathlib import Path

from mill.logbook_db import LogBookDb
from mill.recipe_meta import RecipeMeta
from waspy.iba.file_handler import FileHandler
from waspy.iba.iba_error import CancelError
from waspy.iba.rbs_entities import RbsChannelingMap, CoordinateRange, Window, PositionCoordinates, ChannelingMapJournal, \
    get_positions_as_float, get_rbs_journal, ChannelingMapYield, RecipeType
from waspy.iba.rbs_recipes import save_channeling_map_to_disk, get_sum, save_channeling_map_journal
from waspy.iba.rbs_setup import RbsSetup
from mill.config import make_mill_config

log_label = "[WASPY.SCRIPTS.CHANNELING_MAP_MEASUREMENT]"


def run_channeling_map() -> ChannelingMapJournal:
    """
    Moves sample to correct position.
    Measures for each theta and zeta the yield.
    All data is saved in data files after each measurement.
    All yield data within given energy window is stored and returned as a ChannelingMapJournal.
    """
    start_time = datetime.now()
    rbs_setup.move(recipe.start_position)

    zeta_angles = get_positions_as_float(recipe.zeta_coordinate_range)
    theta_angles = get_positions_as_float(recipe.theta_coordinate_range)
    rbs_journals = []
    cms_yields = []
    rbs_index = 0

    for zeta in zeta_angles:
        for theta in theta_angles:
            rbs_setup.move(PositionCoordinates(zeta=zeta, theta=theta))
            cms_step_start_time = datetime.now()

            rbs_setup.prepare_acquisition()
            rbs_data = rbs_setup.acquire_data(recipe.charge_total)
            if rbs_setup.cancelled():
                raise CancelError("RBS Recipe was cancelled")
            rbs_setup.finalize_acquisition()

            histogram_data = rbs_data.histograms[recipe.optimize_detector_identifier]
            rbs_journal = get_rbs_journal(rbs_data, cms_step_start_time)
            rbs_journals.append(rbs_journal)
            energy_yield = get_sum(histogram_data, recipe.yield_integration_window)
            cms_yields.append(ChannelingMapYield(zeta=zeta, theta=theta, energy_yield=energy_yield))
            save_channeling_map_journal(file_handler, recipe, rbs_journal, zeta, theta, rbs_index, recipe_meta_data)
            rbs_index += 1

    end_time = datetime.now()

    return ChannelingMapJournal(start_time=start_time, end_time=end_time, rbs_journals=rbs_journals,
                                cms_yields=cms_yields)


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
    recipe = RbsChannelingMap(
        type=RecipeType.CHANNELING_MAP,
        sample="sample2",
        name="RBS23_00X",
        start_position=PositionCoordinates(x=10, y=10, phi=10, zeta=-2, detector=170, theta=-2),
        charge_total=400,
        zeta_coordinate_range=CoordinateRange(name="zeta", start=-2, end=2, increment=2),
        theta_coordinate_range=CoordinateRange(name="theta", start=-2, end=2, increment=2),
        yield_integration_window=Window(start=400, end=430),
        optimize_detector_identifier="d01"
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
    journal = run_channeling_map()
    title = f"{recipe.name}_{recipe.yield_integration_window.start}_{recipe.yield_integration_window.end}_" \
            f"{recipe.optimize_detector_identifier}"
    save_channeling_map_to_disk(file_handler, recipe.name, journal.cms_yields, title)
