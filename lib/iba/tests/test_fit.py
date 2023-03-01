from pathlib import Path
from typing import List

import numpy as np

from waspy.iba.file_handler import FileHandler
from waspy.iba.rbs_entities import AysFitResult
from waspy.iba.rbs_plot import plot_energy_yields
from waspy.iba.rbs_yield_angle_fit import fit_and_smooth

import unittest


def fit_and_smooth_for_each(angles, yields_set) -> List[float]:
    fit_results = []
    for energy_yields in yields_set:
        fit_func, min_angle = fit_and_smooth(angles, energy_yields)
        fit_results.append(min_angle)
        fit_result = AysFitResult(success=True, minimum=min_angle, discrete_angles=angles,
                                  discrete_yields=energy_yields,
                                  fit_func=fit_func)
        fig = plot_energy_yields("test1", fit_result)

        file_writer = FileHandler(Path("."), remote_dir=None)
        file_writer.write_matplotlib_fig_to_disk(f'plot_{min_angle}.png', fig)

    return fit_results


class TestStringMethods(unittest.TestCase):

    def test_fit(self):
        angles = np.arange(-2, 2.1, 0.2)
        angles = list(np.around(angles, decimals=2))

        yields = [
            [2443.0, 2497.0, 2547.0, 2614.0, 2597.0, 2680.0, 1966.0, 725.0, 1001.0, 2269.0, 2393.0, 2272.0, 2226.0,
             2215.0, 2208.0, 2196.0, 2025.0, 2246.0, 2486.0, 2524.0, 2551.0],
            [252.0, 230.0, 260.0, 288.0, 276.0, 279.0, 254.0, 295.0, 331.0, 281.0, 203.0, 65.0, 45.0, 91.0, 220.0,
             273.0, 283.0, 273.0, 280.0, 246.0, 271.0],
            [1127.0, 1152.0, 1101.0, 1133.0, 1085.0, 1105.0, 1112.0, 1088.0, 1073.0, 1023.0, 1038.0, 850.0, 524.0,
             260.0, 265.0, 397.0, 717.0, 844.0, 949.0, 901.0, 943.0],
            [1057.0, 1059.0, 1083.0, 1086.0, 1006.0, 1096.0, 1132.0, 1047.0, 1045.0, 973.0, 792.0, 596.0, 416.0, 378.0,
             434.0, 599.0, 827.0, 990.0, 1033.0, 1057.0, 1124.0],
            [1216.0, 1230.0, 1193.0, 1168.0, 1162.0, 1193.0, 1172.0, 1085.0, 1082.0, 1139.0, 1041.0, 1119.0, 1091.0,
             1129.0, 1119.0, 1242.0, 1195.0, 1293.0, 1242.0, 1243.0, 1301.0],
            [1876.0, 1869.0, 1809.0, 1680.0, 1895.0, 1874.0, 1978.0, 1912.0, 1468.0, 630.0, 1017.0, 1816.0, 1872.0,
             1861.0, 1862.0, 1761.0, 1906.0, 1925.0, 1832.0, 1754.0, 1355.0],
            [613.0, 647.0, 596.0, 587.0, 626.0, 634.0, 645.0, 659.0, 634.0, 301.0, 304.0, 547.0, 555.0, 573.0, 576.0,
             562.0, 525.0, 527.0, 603.0, 564.0, 631.0],
            [269.0, 243.0, 229.0, 253.0, 263.0, 224.0, 233.0, 252.0, 301.0, 296.0, 237.0, 288.0, 274.0, 254.0, 226.0,
             86.0, 46.0, 53.0, 141.0, 257.0, 267.0],
            [260.0, 249.0, 225.0, 241.0, 258.0, 217.0, 230.0, 251.0, 249.0, 250.0, 236.0, 250.0, 270.0, 232.0, 91.0,
             36.0, 52.0, 106.0, 213.0, 220.0, 263.0],
            [1354, 1630, 1664, 1775, 1775, 1819, 1708, 660, 502, 1342, 1600, 1569, 1511, 1537, 1459, 1192, 1420, 1620,
             1621, 1689, 1704],
            [3806, 3754, 3546, 3309, 3018, 2642, 2157, 1956, 1617, 1358, 1391, 1354, 1441, 1481, 1605, 2156, 2620, 3040,
             3349, 3462, 3431],
            [2811, 3076, 2976, 2641, 2249, 1930, 1462, 1177, 1238, 1032, 1022, 1017, 1030, 1148, 1210, 1346, 1692, 2073,
             2520, 3013, 3198],
            [2970, 2890, 3022, 2803, 2643, 2215, 1812, 1448, 1292, 1215, 1176, 1134, 1167, 1450, 1593, 1972, 2422, 2727,
             3026, 3155, 3227],
            [3713, 3629, 3638, 3433, 2775, 2142, 2147, 1601, 1290, 1039, 935, 880, 991, 1092, 1327, 1634, 1954, 2781,
             3290, 3523, 3624],
            [3565, 3559, 3558, 3217, 2831, 2454, 1890, 1405, 1221, 1200, 985, 996, 1092, 1155, 1362, 1386, 2000, 2614,
             3069, 3295, 3379],
            [3644, 3616, 3422, 3197, 2806, 2345, 2058, 1427, 1331, 1237, 1067, 958, 880, 1001, 1042, 1080, 1316, 1521,
             1594, 1769, 2538]
        ]
        expected_results = [-0.53, 0.38, 0.73, 0.59, 0.0, -0.15, -0.1, 1.26, 1.1, -0.48, 0.07, 0.11, 0.04, 0.11, 0.1, 0.36]

        index = 0
        for expected_result, energy_yields in zip(expected_results, yields):
            fit_func, min_angle = fit_and_smooth(angles, energy_yields)
            fit_result = AysFitResult(success=True, minimum=min_angle, discrete_angles=angles,
                                      discrete_yields=energy_yields,
                                      fit_func=fit_func)

            fig = plot_energy_yields("test1", fit_result)

            file_handler = FileHandler(Path("./tests/out"), remote_dir=None)
            file_handler.write_matplotlib_fig_to_disk(f'{index:02d}_plot_{min_angle}.png', fig)

            self.assertAlmostEqual(expected_result, min_angle, 2)
            index += 1
