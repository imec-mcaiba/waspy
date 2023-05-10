import math
import os
import logging
from datetime import datetime
from pathlib import Path

from matplotlib import pyplot as plt

from mill.logbook_db import LogBookDb
from mill.recipe_meta import RecipeMeta
from waspy.iba.file_handler import FileHandler
from waspy.iba.iba_error import CancelError
from waspy.iba.rbs_entities import RbsChannelingMap, RbsRandom, CoordinateRange, Window, PositionCoordinates, \
    ChannelingMapJournal, \
    get_positions_as_float, get_rbs_journal, ChannelingMapYield, RecipeType, Plot, Graph, GraphGroup, RbsChannelingSlope
from waspy.iba.rbs_plot import plot_graph_group
from waspy.iba.rbs_recipes import save_channeling_map_to_disk, get_sum, save_channeling_map_journal, run_random, \
    save_rbs_journal, save_channeling_graphs_to_disk
from waspy.iba.rbs_setup import RbsSetup
from mill.config import make_mill_config

log_label = "[WASPY.SCRIPTS.CHANNELING_MAP_MEASUREMENT]"


def shortest_path(coordinate_start, coordinate_end, steps):
    zeta_angles = []
    theta_angles = []

    for s in range(steps+1):
        zeta_angles.append(round(coordinate_start.zeta + (coordinate_end.zeta - coordinate_start.zeta)/(steps)*s, 1))
        theta_angles.append(round(coordinate_start.theta + (coordinate_end.theta - coordinate_start.theta)/(steps)*s, 1))
    return zeta_angles, theta_angles


def save_channeling_slope(file_handler, journal, title):
    data = []
    x_labels = []

    for channelingmap in journal.cms_yields:
        data.append(channelingmap.energy_yield)
        x_labels.append(f"({channelingmap.zeta}, {channelingmap.theta})")
    fig, ax = plt.subplots()
    ax.plot(x_labels, data)
    ax.set_title(title)
    plt.xticks(rotation=90)
    ax.tick_params(axis='both', which='major', labelsize=6)
    ax.tick_params(axis='both', which='minor', labelsize=4)

    file_handler.write_matplotlib_fig_to_disk(f'{title}.png', fig)


def run_channeling_slope() -> ChannelingMapJournal:
    """
    Moves sample to correct position.
    Measures for each theta and zeta the yield.
    All data is saved in data files after each measurement.
    All yield data within given energy window is stored and returned as a ChannelingMapJournal.
    """
    start_time = datetime.now()
    rbs_setup.move(recipe.start_position)

    zeta_angles, theta_angles = shortest_path(recipe.coordinate_start, recipe.coordinate_end, recipe.steps)

    rbs_journals = []
    cms_yields = []
    rbs_index = 0

    for zeta, theta in zip(zeta_angles, theta_angles):
        logging.info(f"{log_label} Measurement {rbs_index + 1}/{recipe.steps+1}")
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
    recipes = [
        RbsChannelingSlope(
            type=RecipeType.CHANNELING_SLOPE,
            sample="sample2",
            name="RBS23_001_A",
            start_position=PositionCoordinates(x=10, y=10, phi=10, detector=170),
            charge_total=400,
            coordinate_start=PositionCoordinates(zeta=-1, theta=-7),
            coordinate_end=PositionCoordinates(zeta=3, theta=7),
            steps=10,
            yield_integration_window=Window(start=0, end=10),
            optimize_detector_identifier="d01"
        ),
    ]

    """
    ===================================================================================
    ===================================================================================
    """

    rbs_setup = RbsSetup(mill_config.rbs.get_driver_urls())
    rbs_setup.configure_detectors(mill_config.rbs.drivers.caen.detectors)
    file_handler = FileHandler(local_dir, remote_dir)

    recipe_meta_data = RecipeMeta(logbook_db, recipe_meta_dir)
    recipe_meta_data = recipe_meta_data.fill_rbs_recipe_meta()

    for recipe in recipes:
        logging.info(f"{log_label} =========== Running {recipe.name} ===========")
        file_handler.set_base_folder(recipe.name)
        logging.info(
            f"{log_label} Files are saved in {os.path.join(local_dir, recipe.name)} and {os.path.join(remote_dir, recipe.name)}")

        journal = run_channeling_slope()
        title = f"{recipe.name}_{recipe.yield_integration_window.start}_{recipe.yield_integration_window.end}_" \
                f"{recipe.optimize_detector_identifier}"
        save_channeling_slope(file_handler, journal, title)

        logging.info(f"{log_label} All measurements completed!")
