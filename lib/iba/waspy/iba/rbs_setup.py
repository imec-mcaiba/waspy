import copy
import logging
import time
from typing import List, Dict


from waspy.drivers.aml_smd2 import AmlSmd2
from waspy.drivers.caen import Caen
from waspy.drivers.motrona_dx350 import MotronaDx350
from waspy.iba.iba_error import IbaError
from waspy.iba.rbs_entities import Detector, RbsData, PositionCoordinates, RbsDriverUrls
from waspy.iba.preempt import preemptive


def fake_counter():
    return


class RbsSetup:
    detectors: List[Detector]
    _acquisition_run_time: float
    _acquisition_accumulated_charge: float
    _counting: bool
    _cancel: bool
    fake: bool

    def __init__(self, rbs_hw: RbsDriverUrls):
        self.hw = rbs_hw

        self.motor_x_y = AmlSmd2(self.hw.aml_x_y)
        self.motor_phi_zeta = AmlSmd2(self.hw.aml_phi_zeta)
        self.motor_det_theta = AmlSmd2(self.hw.aml_det_theta)
        self.charge_counter = MotronaDx350(self.hw.motrona_charge)
        self.data_acquisition = Caen(self.hw.caen)

        self.detectors = []
        self._start_time = time.time()
        self._acquisition_run_time = 0
        self._acquisition_accumulated_charge = 0
        self.charge_offset = 0
        self._counting = False
        self._fake = False
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def cancelled(self):
        return self._cancel

    def resume(self):
        if not self._fake:
            self._cancel = False

    def fake(self):
        self._fake = True
        self._cancel = True

    @preemptive
    def move(self, position: PositionCoordinates):
        if position is None:
            return
        logging.info("[WASPY.IBA.RBS_SETUP] Moving rbs system to '" + str(position) + "'")
        self.motor_x_y.move_both([position.x, position.y])
        self.motor_phi_zeta.move_both([position.phi, position.zeta])
        self.motor_det_theta.move_both([position.det, position.theta])

    def load(self):
        self.motor_x_y.load()
        self.motor_phi_zeta.load()
        self.motor_det_theta.load()

    def finish(self):
        self.resume()
        self.charge_offset = 0

    @preemptive
    def _wait_for_count_finished(self):
        self._counting = True
        while self.charge_counter.is_counting():
            time.sleep(1)
            yield
        self._counting = False

    @preemptive
    def count(self):
        logging.info("[WASPY.IBA.RBS_SETUP] acquiring till target")
        self.charge_counter.start_count_from_zero()
        self._wait_for_count_finished()
        self._acquisition_accumulated_charge += self.charge_counter.get_charge()
        self.charge_offset += self.charge_counter.get_target_charge()

    def move_and_count(self, position: PositionCoordinates):
        self.move(position)
        self.count()

    def get_total_clipped_charge(self):
        increment = 0
        if self._counting:
            actual_charge = self.charge_counter.get_charge()
            charge_bound = self.charge_counter.get_target_charge()
            increment = actual_charge if actual_charge < charge_bound else charge_bound
        return self.charge_offset + increment

    def clear_charge_offset(self):
        self.charge_offset = 0

    def initialize(self):
        self.charge_offset = 0

    def configure_detectors(self, detectors: List[Detector]):
        self.detectors = detectors

    def get_histograms(self) -> Dict[str, List[int]]:
        histograms = {}
        for detector in self.detectors:
            histograms[detector.identifier] = self.get_packed_histogram(detector)
        return histograms

    def get_detectors(self) -> List[Detector]:
        return self.detectors

    def get_detector(self, identifier: str) -> Detector:
        try:
            return next(detector for detector in self.detectors if detector.identifier == identifier)
        except StopIteration:
            detector_names = str([detector.identifier for detector in self.detectors])
            raise IbaError("Detector: '" + str(identifier) + "' Does not exist. Available detectors:" + detector_names)

    def get_status(self, get_histograms=False) -> RbsData:
        status_x_y = self.motor_x_y.get_status()
        status_phi_zeta = self.motor_phi_zeta.get_status()
        status_det_theta = self.motor_det_theta.get_status()

        status_charge_counter = self.charge_counter.get_status()
        status_data_acquisition = self.data_acquisition.get_status()

        histograms = []
        if get_histograms:
            histograms = self.get_histograms()
        return RbsData.parse_obj(
            {"aml_x_y": status_x_y, "aml_phi_zeta": status_phi_zeta, "aml_det_theta": status_det_theta,
             "motrona": status_charge_counter, "caen": status_data_acquisition, "detectors": self.detectors,
             "histograms": histograms, "measuring_time_sec": self._acquisition_run_time,
             "accumulated_charge": self._acquisition_accumulated_charge})

    def acquire_data(self, total_charge) -> RbsData:
        """Warning: this function can take a while ( >1 hour)"""
        self.prepare_counting_with_target(total_charge)
        self.data_acquisition.start()
        self.count()
        self.data_acquisition.stop()
        return self.get_status(True)

    @preemptive
    def prepare_acquisition(self):
        self.data_acquisition.stop()
        self.data_acquisition.clear()
        self._start_time = time.time()
        self._acquisition_accumulated_charge = 0

    @preemptive
    def finalize_acquisition(self):
        self._acquisition_run_time = float(time.time() - self._start_time)

    @preemptive
    def prepare_counting_with_target(self, target):
        self.charge_counter.pause()
        self.charge_counter.set_target_charge(target)

    def get_packed_histogram(self, detector: Detector) -> List[int]:
        return self.data_acquisition.get_histogram(detector)

    def set_registry(self, board_id, registry_file):
        self.data_acquisition.set_registry(board_id, registry_file)

    def get_registry_value(self, board_id: str, hex_register_address: str):
        return self.data_acquisition.read_register(board_id, hex_register_address)

    def verify_detectors(self, detectors: List[Detector]):
        if not self.data_acquisition.do_detectors_exist(detectors):
            raise IbaError(f'The specified detectors({detectors}) do not (all) exist.')
