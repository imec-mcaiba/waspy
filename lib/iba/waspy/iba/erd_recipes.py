import logging
from datetime import datetime
from typing import List

import numpy as np

from waspy.iba.erd_entities import ErdRecipe, PositionCoordinates, ErdJournal, get_erd_journal
from waspy.iba.erd_setup import ErdSetup
from waspy.iba.file_handler import FileHandler
from waspy.iba.iba_error import RangeError, CancelError


def run_erd_recipe(recipe: ErdRecipe, erd_setup: ErdSetup) -> ErdJournal:
    start_time = datetime.now()
    erd_setup.move(PositionCoordinates(z=recipe.z_start, theta=recipe.theta))
    erd_setup.wait_for_arrival()
    erd_setup.configure_acquisition(recipe.measuring_time_sec, recipe.name)
    erd_setup.start_acquisition()
    erd_setup.wait_for_acquisition_started()
    z_range = get_z_range(recipe.z_start, recipe.z_end, recipe.z_increment, recipe.z_repeat)
    if len(z_range) == 0:
        raise RangeError("Invalid z range")
    wait_time = recipe.measuring_time_sec / len(z_range)
    _log_recipe(recipe, wait_time, z_range)
    for z in z_range:
        erd_setup.move(z)
        erd_setup.wait_for(wait_time)
        if erd_setup._cancel:
            raise CancelError("ERD Recipe was cancelled")

    erd_setup.wait_for_acquisition_done()
    erd_setup.convert_data_to_ascii()

    erd_setup.get_measuring_time()

    return get_erd_journal(erd_setup.get_status(get_histogram=True), start_time)


def get_z_range(start, end, increment, repeat=1) -> List[PositionCoordinates]:
    if increment == 0:
        positions = [PositionCoordinates(z=start)]
    else:
        coordinate_range = np.arange(start, end + increment, increment)
        logging.info("[WASPY.IBA.ERD_RECIPES] start: " + str(start) + ", end: " + str(end) + ", inc: " + str(increment))
        numpy_z_steps = np.around(coordinate_range, decimals=2)
        positions = [PositionCoordinates(z=float(z_step)) for z_step in numpy_z_steps]

    repeated_positions = []
    [repeated_positions.extend(positions) for _ in range(repeat)]
    return repeated_positions


def _log_recipe(recipe, wait_time, z_range):
    position_list = "("
    position_list += "; ".join([str(position.z) for position in z_range])
    position_list += ")"
    logging.info("[WASPY.IBA.ERD_RECIPES] Recipe: " + recipe.name + ", wait_time_sec between steps: " + str(wait_time) +
                 ", total measurement time: " + str(recipe.measuring_time_sec) +
                 ", z-positions: \n\t" + position_list)


def save_erd_journal(file_handler: FileHandler, recipe: ErdRecipe, erd_journal: ErdJournal, extra):
    file_handler.write_text_to_disk(f'{recipe.name}.flt', erd_journal.histogram)
    meta = _serialize_meta(erd_journal, recipe, extra)
    file_handler.write_text_to_disk(f'{recipe.name}.meta', meta)


def _serialize_meta(journal: ErdJournal, recipe: ErdRecipe, extra):
    now = datetime.utcnow().strftime("%Y.%m.%d__%H:%M__%S.%f")[:-3]

    header = f""" % Comments
 % Title                 := {recipe.name}
 % Section := <raw_data>
 *
 * Recipe name           := {recipe.name}
 * DATE/Time             := {now}
 * MEASURING TIME[sec]   := {journal.measuring_time_sec}
 *
 * Sample ID             := {recipe.sample}
 * Sample Z              := {journal.z}
 * Sample Theta          := {journal.theta}
 * Z Start               := {recipe.z_start}
 * Z End                 := {recipe.z_end}
 * Z Increment           := {recipe.z_increment}
 * Z Repeat              := {recipe.z_repeat}
 *
 * Theta encoder counts  := {journal.theta_encoder}
 *
 * Start time            := {journal.start_time}
 * End time              := {journal.end_time}
 *
 """
    if extra:
        header += "\n" + extra

    header += f""" % Section :=  </raw_data>
 % End comments"""
    return header
