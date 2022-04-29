import os
import time
import logging
from pathlib import Path

from matplotlib import pyplot as plt

from hive.hardware_control.data_serializer import DataSerializer
from hive.hardware_control.hw_action import format_caen_histogram
from hive.hardware_control.plot import plot_rbs_histograms
from hive.hardware_control.rbs_entities import RbsHardwareRoute, CaenDetectorModel, RbsHistogramGraphData
from hive.hardware_control.rbs_setup import RbsSetup

log_format = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename="logfile.log",
                    filemode="w",
                    format=log_format,
                    level=logging.ERROR)


def setup_rbs() -> RbsSetup:
    config = {
        "aml_x_y": {"url": "http://localhost:20000/api/latest"},
        "aml_phi_zeta": {"url": "http://localhost:20000/api/latest"},
        "aml_det_theta": {"url": "http://localhost:20000/api/latest"},
        "caen": {"url": "http://localhost:20200/api/latest"},
        "motrona_charge": {"url": "http://localhost:20100/api/latest"},
    }

    detectors = [
        CaenDetectorModel(board="33", channel=0, identifier="c0", bins_min=0, bins_max=24576, bins_width=24576),
        CaenDetectorModel(board="33", channel=1, identifier="c1", bins_min=0, bins_max=24576, bins_width=24576),
        CaenDetectorModel(board="33", channel=2, identifier="c2", bins_min=0, bins_max=24576, bins_width=24576),
        CaenDetectorModel(board="33", channel=3, identifier="c3", bins_min=0, bins_max=24576, bins_width=24576),
        CaenDetectorModel(board="33", channel=4, identifier="c4", bins_min=0, bins_max=24576, bins_width=24576),
        CaenDetectorModel(board="33", channel=5, identifier="c5", bins_min=0, bins_max=24576, bins_width=24576),
        CaenDetectorModel(board="33", channel=6, identifier="c6", bins_min=0, bins_max=24576, bins_width=24576),
        CaenDetectorModel(board="33", channel=7, identifier="c7", bins_min=0, bins_max=24576, bins_width=24576),
    ]

    rbs_hw = RbsHardwareRoute.parse_obj(config)
    rbs_setup = RbsSetup(rbs_hw)
    rbs_setup.initialize(detectors)
    rbs_setup.fake()
    return rbs_setup


if __name__ == "__main__":
    rbs = setup_rbs()
    data_serializer = DataSerializer(Path(os.getcwd()), None)
    data_serializer.set_base_folder("caen_tuning_data")

    registry_list = [
        "2022.03.23_b1782_33_FWHM_ft0.36_rt1.0.dmp",
        "2022.03.23_b1782_33_FWHM_ft0.36_rt1.2.dmp",
        "2022.03.23_b1782_33_FWHM_ft0.36_rt1.4.dmp",
        "2022.03.23_b1782_33_FWHM_ft0.36_rt1.6.dmp",
        "2022.03.23_b1782_33_FWHM_ft0.36_rt1.8.dmp",
        "2022.03.23_b1782_33_FWHM_ft0.36_rt2.0.dmp",
        "2022.03.23_b1782_33_FWHM_ft0.4_rt1.0.dmp",
        "2022.03.23_b1782_33_FWHM_ft0.4_rt1.2.dmp",
        "2022.03.23_b1782_33_FWHM_ft0.4_rt1.4.dmp",
        "2022.03.23_b1782_33_FWHM_ft0.4_rt1.6.dmp",
        "2022.03.23_b1782_33_FWHM_ft0.4_rt1.8.dmp",
        "2022.03.23_b1782_33_FWHM_ft0.4_rt2.0.dmp"
    ]
    rbs.stop_data_acquisition()

    for registry in registry_list:
        rbs.set_registry("33", registry)
        rbs.prepare_counting_with_target(10000)
        rbs.start_data_acquisition()
        rbs.count()
        time.sleep(5)
        rbs.stop_data_acquisition()
        rbs_data = rbs.get_status(get_histograms=True)

        logging.info("------")
        logging.info("Testing registry: " + registry)
        logging.info("Status: " + str(rbs_data))
        logging.info("------")
        logging.info("")

        for histogram_data in rbs_data.histograms:
            text_filename = Path(registry).stem + "_" + histogram_data.title + ".txt"
            fig_filename = Path(registry).stem + "_" + histogram_data.title + ".png"
            data_serializer.write_text_to_disk(text_filename, format_caen_histogram(histogram_data.data))
            fig = plot_rbs_histograms(RbsHistogramGraphData(graph_title=registry, histograms=[histogram_data]))
            data_serializer.write_matplotlib_fig_to_disk(fig_filename, fig)