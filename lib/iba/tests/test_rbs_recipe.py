import unittest
from unittest.mock import MagicMock, create_autospec, Mock, call, patch

from waspy.iba.rbs_entities import PositionCoordinates, RbsRandom, RbsData, CoordinateRange
from waspy.iba.rbs_recipes import run_random
from waspy.iba.rbs_setup import RbsSetup
from mill.job import execute


class TestDbTables(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_run_random(self):
        recipe = RbsRandom(
            type="rbs_random", sample="HS12_02", name="RBS22_082_01A", charge_total=45000,
            start_position=PositionCoordinates(x=10, y=22, phi=0),
            coordinate_range=CoordinateRange(name="phi", start=0, end=30, increment=2)
        )

        rbs_setup = MagicMock(spec=RbsSetup)

        rbs_data = RbsData(
            aml_x_y={"motor_1_position": 10, "motor_2_position": 20},
            aml_phi_zeta={"motor_1_position": 30, "motor_2_position": 40},
            aml_det_theta={"motor_1_position": 50, "motor_2_position": 60},
            caen={}, motrona={}, histograms={"d01": [1, 2, 3], "d02": [3, 4, 5]},
            measuring_time_sec=12000, accumulated_charge=45000
        )

        rbs_setup.get_status = Mock(return_value=rbs_data)

        journal = run_random(recipe, rbs_setup)

        self.assertEqual(journal.x, 10)
        self.assertEqual(journal.y, 20)
        self.assertEqual(journal.phi, 30)
        self.assertEqual(journal.zeta, 40)
        self.assertEqual(journal.det, 50)
        self.assertEqual(journal.theta, 60)
        self.assertEqual(journal.measuring_time_sec, 12000)
        self.assertAlmostEqual(journal.accumulated_charge, 45000)
        self.assertEqual(journal.histograms, {"d01": [1, 2, 3], "d02": [3, 4, 5]})
