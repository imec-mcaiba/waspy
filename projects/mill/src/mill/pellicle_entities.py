from pathlib import Path
from enum import Enum
from pydantic.generics import BaseModel

from mill.entities import SimpleConfig, AmlConfig, CaenConfig
from waspy.iba.pellicle_entities import PellicleDriverUrls


class PellicleDriverGroup(BaseModel):
    caen: CaenConfig
    motrona_charge: SimpleConfig


class PellicleConfig(BaseModel):
    drivers: PellicleDriverGroup

    def get_driver_urls(self) -> PellicleDriverUrls:
        return PellicleDriverUrls(
            caen=self.drivers.caen.url,
            motrona_charge=self.drivers.motrona_charge.url
        )


class StatusModel(str, Enum):
    Idle = "Idle"
    Running = "Running"

