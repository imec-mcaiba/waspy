import math

import app.hardware_controllers.daemon_comm as comm
from app.rbs_experiment.entities import PositionCoordinates, VaryCoordinate, CoordinateEnum, CaenDetectorModel, Window
from app.setup.config import daemons
from typing import List

import logging
import numpy as np


async def move_to_position(identifier: str, position: PositionCoordinates):
    logging.info("Moving rbs system to '" + str(position) + "'")
    print("Moving rbs system to '" + str(position) + "'")

    if position.x is not None:
        await comm.move_aml_first(identifier, daemons.aml_x_y.url, position.x)
    if position.y is not None:
        await comm.move_aml_second(identifier, daemons.aml_x_y.url, position.y)
    if position.phi is not None:
        await comm.move_aml_first(identifier, daemons.aml_phi_zeta.url, position.phi)
    if position.zeta is not None:
        await comm.move_aml_second(identifier, daemons.aml_phi_zeta.url, position.zeta)
    if position.detector is not None:
        await comm.move_aml_first(identifier, daemons.aml_det_theta.url, position.detector)
    if position.theta is not None:
        await comm.move_aml_second(identifier, daemons.aml_det_theta.url, position.theta)


async def move_to_angle(identifier: str, coordinate: CoordinateEnum, value):
    if coordinate == CoordinateEnum.zeta:
        await move_to_position(identifier, PositionCoordinates(zeta=value))
    if coordinate == CoordinateEnum.theta:
        await move_to_position(identifier, PositionCoordinates(theta=value))


async def move_to_angle_then_acquire_till_target(identifier: str, coordinate: CoordinateEnum, value):
    logging.info("moving then acquiring till target")
    print("moving then acquiring till target")
    await move_to_angle(identifier, coordinate, value)
    await comm.clear_and_arm_caen_acquisition(identifier, daemons.caen_charles_evans.url)
    await comm.clear_start_motrona_count(identifier, daemons.motrona_rbs.url)
    await comm.motrona_counting_done(daemons.motrona_rbs.url)


async def counting_pause_and_set_target(identifier: str, target):
    logging.info("pause counting and set target")
    print("pause counting and set target")
    await comm.pause_motrona_count(identifier + "_pause", daemons.motrona_rbs.url)
    await comm.set_motrona_target_charge(identifier + "_set_target_charge", daemons.motrona_rbs.url, target)


def make_coordinate_range(vary_coordinate: VaryCoordinate) -> List[float]:
    coordinate_range = np.arange(vary_coordinate.start, vary_coordinate.end + vary_coordinate.increment,
                                 vary_coordinate.increment)
    return np.around(coordinate_range, decimals=2)


async def get_packed_histogram(detector: CaenDetectorModel):
    data = await comm.get_caen_histogram(daemons.caen_charles_evans.url, detector.board, detector.channel)
    packed = pack(data, detector.bins_min, detector.bins_max, detector.bins_width)
    return packed


def get_sum(data: List[int], window: Window):
    return sum(data[window.start:window.end])


def pack(data: List[int], channel_min, channel_max, channel_width) -> List[int]:
    subset = data[channel_min:channel_max]
    samples_to_group_in_bin = math.floor(len(subset) / channel_width)
    packed_data = []
    for index in range(0, samples_to_group_in_bin * channel_width, samples_to_group_in_bin):
        bin_sum = sum(subset[index:index + samples_to_group_in_bin])
        packed_data.append(bin_sum)
    return packed_data
