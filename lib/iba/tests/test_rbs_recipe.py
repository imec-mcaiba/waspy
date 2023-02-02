import unittest
from unittest.mock import MagicMock

from waspy.iba.rbs_entities import PositionCoordinates, Window, RbsRandom, RbsData, CoordinateRange, RbsChannelingMap, \
    RecipeType
from waspy.iba.rbs_recipes import run_random, run_channeling_map
from waspy.iba.rbs_setup import RbsSetup


class TestDbTables(unittest.TestCase):
    def setUp(self):
        self.rbs_setup = MagicMock(spec=RbsSetup)
        rbs_data = RbsData(
            aml_x_y={"motor_1_position": 10, "motor_2_position": 20},
            aml_phi_zeta={"motor_1_position": 30, "motor_2_position": 40},
            aml_det_theta={"motor_1_position": 50, "motor_2_position": 60},
            caen={}, motrona={}, histograms={"d01": [1, 2, 3], "d02": [3, 4, 5]},
            measuring_time_sec=12000, accumulated_charge=45000
        )
        self.rbs_setup.get_status.return_value = rbs_data
        self.rbs_setup.cancelled.return_value = False

    def tearDown(self):
        pass

    def test_run_random(self):
        recipe = RbsRandom(
            type=RecipeType.RANDOM, sample="HS12_02", name="RBS22_082_01A", charge_total=45000,
            start_position=PositionCoordinates(x=10, y=22, phi=0),
            coordinate_range=CoordinateRange(name="phi", start=0, end=30, increment=2)
        )

        journal = run_random(recipe, self.rbs_setup)

        self.assertTrue(self.rbs_setup.move.called)
        self.assertEqual(journal.x, 10)
        self.assertEqual(journal.y, 20)
        self.assertEqual(journal.phi, 30)
        self.assertEqual(journal.zeta, 40)
        self.assertEqual(journal.det, 50)
        self.assertEqual(journal.theta, 60)
        self.assertEqual(journal.measuring_time_sec, 12000)
        self.assertAlmostEqual(journal.accumulated_charge, 45000)
        self.assertEqual(journal.histograms, {"d01": [1, 2, 3], "d02": [3, 4, 5]})

    def test_run_channeling_map(self):
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
        self.rbs_setup.acquire_data = MagicMock()
        journal = run_channeling_map(recipe, self.rbs_setup)

        self.assertEqual(self.rbs_setup.move.call_count, 442)  # 21 rows, 21 columns = 441   +1 move to start_position
        self.assertEqual(self.rbs_setup.acquire_data.call_count, 441)  # 21 rows, 21 columns = 441
        self.assertEqual(len(journal.cms_yields), 441)  # 21 rows, 21 columns = 441

