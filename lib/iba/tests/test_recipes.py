import unittest

from waspy.iba.rbs_entities import RbsChanneling, RecipeType, CoordinateRange, Window, \
    RbsRandom, RbsData, PositionCoordinates, RbsChannelingMap
from waspy.iba.rbs_recipes import run_channeling, run_random, run_channeling_map
from waspy.iba.rbs_setup import RbsSetup
from unittest.mock import MagicMock, call
import logging

logging.basicConfig(
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
    level=logging.INFO,
    datefmt='%Y.%m.%d__%H:%M__%S')


class TestRecipes(unittest.TestCase):
    def setUp(self):
        self.rbs = MagicMock(spec=RbsSetup)
        rbs_data = RbsData(
            aml_x_y={"motor_1_position": 5, "motor_2_position": 10},
            aml_phi_zeta={"motor_1_position": 6, "motor_2_position": 11},
            aml_det_theta={"motor_1_position": 7, "motor_2_position": 12},
            caen={}, motrona={},
            histograms={"d01": [0, 1, 2, 3], "d02": [1, 2, 3, 4]}, measuring_time_sec=0, accumulated_charge=0
        )
        self.rbs.get_status.return_value = rbs_data
        self.rbs.cancelled.return_value = False

    def test_random(self):
        recipe = RbsRandom(
            type=RecipeType.RANDOM, sample="sample_001", name="recipe_001",
            charge_total=50000, coordinate_range=CoordinateRange(start=0, end=30, increment=2, name="phi")
        )
        run_random(recipe, self.rbs)

    def test_channeling(self):
        recipe = RbsChanneling(
            type=RecipeType.CHANNELING, sample="sample_001", name="recipe_001",
            yield_charge_total=5000, yield_coordinate_ranges=
            [
                CoordinateRange(start=-2, end=2, increment=0.2, name="zeta"),
                CoordinateRange(start=-2, end=2, increment=0.2, name="theta"),
                CoordinateRange(start=-2, end=2, increment=0.2, name="zeta"),
                CoordinateRange(start=-2, end=2, increment=0.2, name="theta"),
            ],
            yield_integration_window=Window(start=550, end=650),
            yield_optimize_detector_identifier="d01",
            compare_charge_total=60000,
            random_coordinate_range=CoordinateRange(start=0, end=30, increment=0.2, name="phi")
        )
        run_channeling(recipe, self.rbs)

    def test_channeling_map(self):
        recipe = RbsChannelingMap(
            type=RecipeType.CHANNELING_MAP,
            sample="sample_001",
            name="recipe_001",
            charge_total=2000,
            zeta_coordinate_range=CoordinateRange(start=-2, end=2, increment=0.2, name="zeta"),
            theta_coordinate_range=CoordinateRange(start=-2, end=2, increment=0.2, name="theta"),
            yield_integration_window=Window(start=550, end=650),
            optimize_detector_identifier="d01",
        )
        run_channeling_map(recipe, self.rbs)

    def test_run_random(self):
        recipe = RbsRandom(
            type="rbs_random", sample="AE007607_D02_A", name="RBS21_071_01B_A",
            start_position=PositionCoordinates(x=10, y=22, phi=0), charge_total=45000,
            coordinate_range=CoordinateRange(name="phi", start=0, end=30, increment=2)
        )

        run_random(recipe, self.rbs)

        call_list = [call.move(PositionCoordinates(x=10, y=22, phi=0))]
        for phi in range(0, 31, 2):
            call_list.append(call.move(PositionCoordinates(phi=phi)))
            call_list.append(call.acquire_data(45000 / 16))

        self.rbs.assert_has_calls(call_list)

