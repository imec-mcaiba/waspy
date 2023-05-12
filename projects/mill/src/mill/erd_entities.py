from datetime import timedelta, datetime
from pathlib import Path
from typing import List, Literal
from pydantic import BaseModel, Field

from mill.entities import SimpleConfig
from waspy.iba.erd_entities import ErdDriverUrls, ErdRecipe


class ErdDriverGroup(BaseModel):
    mdrive_z: SimpleConfig
    mdrive_theta: SimpleConfig
    motrona_z_encoder: SimpleConfig
    motrona_theta_encoder: SimpleConfig
    mpa3: SimpleConfig


class ErdConfig(BaseModel):
    drivers: ErdDriverGroup
    local_dir: Path
    remote_dir: Path

    def get_driver_urls(self) -> ErdDriverUrls:
        return ErdDriverUrls(
            mdrive_z=self.drivers.mdrive_z.url,
            mdrive_theta=self.drivers.mdrive_theta.url,
            motrona_z_encoder=self.drivers.motrona_z_encoder.url,
            motrona_theta_encoder=self.drivers.motrona_theta_encoder.url,
            mpa3=self.drivers.mpa3.url
        )


class ErdStatus(BaseModel):
    progress: str
    run_time: float
    name: str
    type: str
    sample: str


def make_erd_status(recipe: ErdRecipe, progress, start_time):
    return ErdStatus(progress=progress, run_time=(datetime.now() - start_time).total_seconds(),
                     name=recipe.name, type=recipe.type, sample=recipe.sample)


class ErdJobModel(BaseModel):
    name: str
    beam_type: str
    sample_tilt_degrees: float
    beam_energy_MeV: float
    recipes: List[ErdRecipe]
    type: Literal["erd"] = "erd"

    class Config:
        use_enum_value = True

        schema_extra = {
            'example':
                {
                    "name": "ERD22_020", "beam_type": "35Cl4+", "beam_energy_MeV": 8, "sample_tilt_degrees": 15,
                    "recipes": [
                        {
                            "name": "test_1",
                            "measuring_time_sec": 30,
                            "sample": "test_001",
                            "theta": 40,
                            "z_start": 1,
                            "z_end": 5,
                            "z_increment": 0.5,
                            "z_repeat": 2
                        },
                        {
                            "name": "test_2",
                            "measuring_time_sec": 30,
                            "sample": "test_002",
                            "recipe": "something_2",
                            "theta": 70.05,
                            "z_start": 5,
                            "z_end": 50,
                            "z_increment": 1
                        }
                    ]
                }
        }


empty_erd_rqm = ErdJobModel(recipes=[], name="", beam_energy_MeV=0.0, beam_type="", sample_tilt_degrees=0.0)


class ActiveRecipe(BaseModel):
    recipe_id: str
    run_time: timedelta
    run_time_target: float


class ErdRqmStatus(BaseModel):
    run_status: str
    active_rqm_status: List[ActiveRecipe]


empty_erd_status = ErdRqmStatus(run_status="idle", active_rqm_status=[])
