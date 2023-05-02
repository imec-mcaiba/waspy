from datetime import datetime
from typing import Optional, Dict, Literal

from pydantic import Field
from pydantic.main import BaseModel


class PositionCoordinates(BaseModel):
    z: Optional[float]
    theta: Optional[float]


class ErdDriverUrls(BaseModel):
    mdrive_z: str
    mdrive_theta: str
    mpa3: str
    motrona_theta_encoder: str


class ErdData(BaseModel):
    mdrive_z: Dict
    mdrive_theta: Dict
    mpa3: Dict
    motrona_theta_encoder: Dict
    histogram: str
    measuring_time_sec: float


class ErdResult(BaseModel):
    erd_data: ErdData
    title: str


class ErdRecipe(BaseModel):
    measuring_time_sec: int
    type: Literal["erd"] = "erd"
    sample: str
    name: str
    theta: float
    z_start: float
    z_end: float
    z_increment: float
    z_repeat: int = Field(1, description="The recipe will run from z_start to z_end, for z_repeat times.")


class ErdJournal(BaseModel):
    start_time: datetime
    end_time: datetime
    measuring_time_sec: int
    z: float
    theta: float
    theta_encoder: float
    histogram: str


def get_erd_journal(erd_data: ErdData, start_time: datetime) -> ErdJournal:
    return ErdJournal(
        start_time=start_time, end_time=datetime.now(), measuring_time_sec=erd_data.measuring_time_sec,
        z=erd_data.mdrive_z["motor_position"], theta=erd_data.mdrive_theta["motor_position"],
        theta_encoder=erd_data.motrona_theta_encoder["counts"],
        histogram=erd_data.histogram)
