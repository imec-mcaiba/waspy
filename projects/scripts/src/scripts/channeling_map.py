import os
from datetime import datetime
from pathlib import Path

from mill.logbook_db import LogBookDb
from mill.recipe_meta import RecipeMeta
from waspy.iba.file_handler import FileHandler
from waspy.iba.rbs_entities import RbsChannelingMap, CoordinateRange, Window, PositionCoordinates, ChannelingMapJournal, \
    get_positions_as_float, get_rbs_journal, ChannelingMapYield, RecipeType
from waspy.iba.rbs_recipes import save_channeling_map_to_disk, get_sum, save_channeling_map_journal
from waspy.iba.rbs_setup import RbsSetup
from mill.config import GlobalConfig, make_mill_config, MillConfig


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
            rbs_data = rbs_setup.acquire_data(recipe.charge_total)
            histogram_data = rbs_data.histograms[recipe.optimize_detector_identifier]
            rbs_journal = get_rbs_journal(rbs_data, cms_step_start_time)
            rbs_journals.append(rbs_journal)
            energy_yield = get_sum(histogram_data, recipe.yield_integration_window)
            cms_yields.append(ChannelingMapYield(zeta=zeta, theta=theta, energy_yield=energy_yield))
            save_channeling_map_journal(file_handler, recipe, rbs_journal, zeta, theta, rbs_index, recipe_meta_data)
            rbs_index += 1
        rbs_index += 1

    end_time = datetime.now()

    return ChannelingMapJournal(start_time=start_time, end_time=end_time, rbs_journals=rbs_journals,
                                cms_yields=cms_yields)


if __name__ == "__main__":
    """=============================== EDITABLE ==========================================
    Configuration of measurement
    
    * config_file:      File with URLs of drivers and directories
    * logbook_url:      URL of logbook (required for recipe meta data)
    * recipe_meta_dir:  Path to rbs_recipe_meta_template.txt, where meta data is stored
    * local_dir:        Local directory to save data files in
    * remote_dir:       Remote directory to save data files in
    * base_folder:      Sub-folder in local_dir and remote_dir
    """
    config_file = "../../../mill/default_config.toml"  # Local development
    # config_file = "../../../mill/lab_config.toml"  # Lab measurements
    logbook_url = "http://127.0.0.1:8001"  # Local development
    # logbook_url = "https://db.capitan.imec.be"  # Lab measurements
    recipe_meta_dir = Path('../../../mill/recipe_meta')

    mill_config = make_mill_config(config_file)  # Do not modify!
    logbook_db = LogBookDb(logbook_url)  # Do not modify!

    local_dir = mill_config.rbs.local_dir
    # local_dir = Path("/some/local/dir")
    remote_dir = mill_config.rbs.remote_dir
    # remote_dir = Path("/some/remote/dir")
    base_folder = "channeling_map"

    """===================================================================================
    """

    rbs_setup = RbsSetup(mill_config.rbs.get_driver_urls())
    rbs_setup.configure_detectors(mill_config.rbs.drivers.caen.detectors)
    file_handler = FileHandler(local_dir, remote_dir)
    file_handler.set_base_folder(base_folder)
    recipe_meta_data = RecipeMeta(logbook_db, recipe_meta_dir)
    print(f"FILES ARE SAVED IN {os.path.join(local_dir, base_folder)} AND {os.path.join(remote_dir, base_folder)}")

    """=============================== EDITABLE ==========================================
    Recipe parameters
        
    Following fields are optional, i.e. you can leave them out if they don't need to change
     - start_position
     - all coordinates in PositionCoordinates
    """
    recipe = RbsChannelingMap(
        type=RecipeType.CHANNELING_MAP,
        sample="sample1",
        name="name1",
        start_position=PositionCoordinates(x=0, y=0, phi=0, zeta=-2, detector=0, theta=-2),
        charge_total=2000,
        zeta_coordinate_range=CoordinateRange(name="zeta", start=-2, end=2, increment=1),
        theta_coordinate_range=CoordinateRange(name="theta", start=-2, end=2, increment=1),
        yield_integration_window=Window(start=0, end=200),
        optimize_detector_identifier="d01"
    )
    """===================================================================================
    """

    recipe_meta_data = recipe_meta_data.fill_rbs_recipe_meta()
    journal = run_channeling_map()
    title = f"{recipe.name}_{recipe.yield_integration_window.start}_{recipe.yield_integration_window.end}_" \
            f"{recipe.optimize_detector_identifier}"
    save_channeling_map_to_disk(file_handler, recipe.name, journal.cms_yields, title)
