import time

import logging
from threading import Lock

from waspy.drivers.fastcom_mpa3 import FastcomMpa3
from waspy.drivers.ims_mdrive import ImsMDrive
from waspy.drivers.motrona_dx350 import MotronaDx350
from waspy.iba.erd_entities import ErdDriverUrls, PositionCoordinates, ErdData
from waspy.iba.preempt import preemptive



class ErdSetup:
    _fake: bool
    _fake_count: int
    _cancel: bool

    def __init__(self, erd_driver_urls: ErdDriverUrls):
        self.mdrive_z = ImsMDrive(erd_driver_urls.mdrive_z)
        self.mdrive_theta = ImsMDrive(erd_driver_urls.mdrive_theta)
        self.mpa3 = FastcomMpa3(erd_driver_urls.mpa3)
        self.motrona_z_encoder = MotronaDx350(erd_driver_urls.motrona_z_encoder)
        self.motrona_theta_encoder = MotronaDx350(erd_driver_urls.motrona_theta_encoder)
        self._lock = Lock()
        self._abort = False
        self._fake = False
        self._fake_count = 0
        self._cancel = False

    def cancel(self):
        self._cancel = True

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
        logging.info("[WASPY.IBA.ERD_SETUP] moving erd system to '" + str(position) + "'")
        self.mdrive_z.move(position.z)
        self.mdrive_theta.move(position.theta)

    @preemptive
    def load(self):
        self.mdrive_z.load()
        self.mdrive_theta.load()

    def get_status(self, get_histogram=False) -> ErdData:
        status_mdrive_z = self.mdrive_z.get_status()
        status_mdrive_theta = self.mdrive_theta.get_status()
        status_mpa3 = self.mpa3.get_status()
        status_motrona_z_encoder = self.motrona_z_encoder.get_status()
        status_motrona_theta_encoder = self.motrona_theta_encoder.get_status()

        histogram = ""
        if get_histogram:
            histogram = self.get_histogram()
        return ErdData.parse_obj(
            {"mdrive_z": status_mdrive_z, "mdrive_theta": status_mdrive_theta, "mpa3": status_mpa3,
             "motrona_z_encoder": status_motrona_z_encoder,
             "motrona_theta_encoder": status_motrona_theta_encoder,
             "histogram": histogram, "measuring_time_sec": self.get_measuring_time()})

    @preemptive
    def wait_for_arrival(self):
        self.mdrive_theta.wait_for_move_done()
        self.mdrive_z.wait_for_move_done()
        logging.info("[WASPY.IBA.ERD_SETUP] Motors have arrived")

    @preemptive
    def wait_for(self, seconds):
        sleep_time = 0
        while sleep_time < seconds:
            yield
            time.sleep(1)
            sleep_time += 1

    @preemptive
    def wait_for_acquisition_done(self):
        logging.info("[WASPY.IBA.ERD_SETUP] Wait for acquisition completed")
        self._acquisition_done()
        logging.info("[WASPY.IBA.ERD_SETUP] Acquisition completed")

    @preemptive
    def wait_for_acquisition_started(self):
        self._acquisition_started()
        logging.info("[WASPY.IBA.ERD_SETUP] Acquisition Started")

    def get_histogram(self):
        logging.info("[WASPY.IBA.ERD_SETUP] get histogram")
        if self._cancel:
            return ""
        return self.mpa3.get_histogram()

    @preemptive
    def configure_acquisition(self, measuring_time_sec: int, spectrum_filename: str):
        self.mpa3.stop_and_clear()
        self.mpa3.configure(measuring_time_sec, spectrum_filename)

    @preemptive
    def reupload_cnf(self):
        self.mpa3.reupload_mpa3_cnf()

    def initialize(self):
        self.reupload_cnf()

    @preemptive
    def start_acquisition(self):
        self.mpa3.start()

    @preemptive
    def convert_data_to_ascii(self):
        logging.info("[WASPY.IBA.ERD_SETUP] Request conversion to ascii")
        self.mpa3.convert_data_to_ascii()
        logging.info("[WASPY.IBA.ERD_SETUP] Conversion to ascii done")

    def get_measuring_time(self):
        return self.mpa3.get_measurement_time()

    @preemptive
    def _acquisition_done(self):
        while True:
            time.sleep(1)
            yield
            if not self.mpa3.acquiring():
                logging.info("[WASPY.IBA.ERD_SETUP] Acquisition has completed")
                break

    @preemptive
    def _acquisition_started(self):
        while True:
            time.sleep(1)
            yield
            if self.mpa3.acquiring():
                logging.info("[WASPY.IBA.ERD_SETUP] Acquisition has started")
                break
