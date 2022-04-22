from enum import Enum
from typing import Union, Dict, Optional, List

from pydantic.generics import BaseModel
from pathlib import Path


class HwControllerType(str, Enum):
    aml = 'aml'
    motrona_dx350 = 'motrona_dx350'
    caen = 'caen'
    mdrive = 'mdrive'
    mpa3 = 'mpa3'
    motrona_ax350 = 'motrona_ax350'
    mirion_g64 = 'mirion_g64'


class SimpleConfig(BaseModel):
    type: HwControllerType
    title: Optional[str]
    url: str
    proxy: Optional[str]

    class Config:
        use_enum_values = True


class AnyHardware(BaseModel):
    __root__: Dict[str, SimpleConfig]

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]


class AnyConfig(BaseModel):
    hardware: AnyHardware
