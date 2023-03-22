from pathlib import Path
from enum import Enum
from pydantic.generics import BaseModel

from mill.entities import SimpleConfig, AmlConfig, CaenConfig
from waspy.iba.pellicle_entities import PellicleDriverUrls


class PellicleDriverGroup(BaseModel):
    #aml_x_y: AmlConfig
    #aml_phi_zeta: AmlConfig
    #aml_det_theta: AmlConfig
    caen: CaenConfig
    motrona_charge: SimpleConfig
    motrona_terminal_voltage: SimpleConfig

class PellicleConfig(BaseModel):
    #local_dir: Path
    #remote_dir: Path
    drivers: PellicleDriverGroup

    def get_driver_urls(self) -> PellicleDriverUrls:
        return PellicleDriverUrls(
            #aml_x_y=self.drivers.aml_x_y.url,
            #aml_phi_zeta=self.drivers.aml_phi_zeta.url,
            #aml_det_theta=self.drivers.aml_det_theta.url,
            caen=self.drivers.caen.url,
            motrona_charge=self.drivers.motrona_charge.url,
            motrona_terminal_voltage=self.drivers.motrona_terminal_voltage.url
        )


class StatusModel(str, Enum):
    Idle = "Idle"
    Running = "Running"

