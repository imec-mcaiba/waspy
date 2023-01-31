from datetime import timedelta, datetime
from pathlib import Path
from enum import Enum
from typing import List, Union, Annotated

from pydantic import Field, validator
from pydantic.generics import BaseModel

from mill.entities import SimpleConfig, AmlConfig, CaenConfig
from waspy.iba.rbs_entities import RbsChanneling, RbsRandom, RbsDriverUrls, RbsChannelingMap


class RbsDriverGroup(BaseModel):
    aml_x_y: AmlConfig
    aml_phi_zeta: AmlConfig
    aml_det_theta: AmlConfig
    caen: CaenConfig
    motrona_charge: SimpleConfig


class RbsConfig(BaseModel):
    local_dir: Path
    remote_dir: Path
    drivers: RbsDriverGroup

    def get_driver_urls(self) -> RbsDriverUrls:
        return RbsDriverUrls(
            aml_x_y=self.drivers.aml_x_y.url,
            aml_phi_zeta=self.drivers.aml_phi_zeta.url,
            aml_det_theta=self.drivers.aml_det_theta.url,
            caen=self.drivers.caen.url,
            motrona_charge=self.drivers.motrona_charge.url
        )


class RbsStatus(BaseModel):
    progress: str
    run_time: float
    name: str
    type: str
    sample: str


def make_rbs_status(recipe: RbsRandom | RbsChanneling, progress, start_time):
    return RbsStatus(progress=progress, run_time=(datetime.now() - start_time).total_seconds(),
                     name=recipe.name, type=recipe.type, sample=recipe.sample)


class StatusModel(str, Enum):
    Idle = "Idle"
    Running = "Running"


class RbsJobModel(BaseModel):
    recipes: List[Annotated[Union[RbsChanneling, RbsRandom, RbsChannelingMap], Field(discriminator='type')]]
    name: str
    type = "rbs"

    class Config:
        use_enum_values = True

        schema_extra = {
            'example':
                {
                    "name": "RBS21_071", "type": "rbs",
                    "recipes": [
                        {"type": "rbs_random", "sample": "AE007607_D02_A", "name": "RBS21_071_01B_A",
                         "start_position": {"x": 10, "y": 22, "phi": 0}, "charge_total": 45000,
                         "vary_coordinate": {"name": "phi", "start": 0, "end": 30, "increment": 2}
                         },
                        {"type": "rbs_random", "sample": "AE007607_D02_B", "name": "RBS21_071_08B_A",
                         "start_position": {"x": 10, "y": 22, "phi": 0}, "charge_total": 45000,
                         "vary_coordinate": {"name": "phi", "start": 0, "end": 30, "increment": 2}
                         },
                        {
                            "type": "rbs_channeling", "sample": "AE007607_D02_A", "name": "RBS21_071_01B_A",
                            "start_position": {"x": 10, "y": 22, "phi": 0}, "yield_charge_total": 2100,
                            "yield_vary_coordinates": [
                                {"name": "zeta", "start": -2, "end": 2, "increment": 0.2},
                                {"name": "theta", "start": -2, "end": 2, "increment": 0.2},
                                {"name": "zeta", "start": -2, "end": 2, "increment": 0.2},
                                {"name": "theta", "start": -2, "end": 2, "increment": 0.2}
                            ],
                            "yield_integration_window": {"start": 22, "end": 53},
                            "optimize_detector_identifier": "d01",
                            "random_fixed_charge_total": 1000,
                            "random_vary_coordinate": {"name": "phi", "start": 0, "end": 30, "increment": 2},

                        },
                        {
                            "type": "rbs_channeling_map", "sample": "AE007607_D02_A", "name": "RBS21_071_01B_A",
                            "start_position": {"x": 10, "y": 22, "phi": 0}, "charge_total": 2000,
                            "zeta_coordinate_range": {"name": "zeta", "start": -2, "end": 2, "increment": 0.2},
                            "theta_coordinate_range": {"name": "theta", "start": -2, "end": 2, "increment": 0.2},
                            "yield_integration_window": {"start": 0, "end": 100},
                            "optimize_detector_identifier": "d01",
                        }
                    ]
                }
        }


empty_rbs_job = RbsJobModel(recipes=[], name="", detectors=[])


class ActiveRecipe(BaseModel):
    recipe_id: str
    run_time: timedelta
    accumulated_charge_corrected: float
    accumulated_charge_target: float


class RbsRqmStatus(BaseModel):
    run_status: StatusModel
    active_rqm_status: List[ActiveRecipe]


empty_rqm_status = RbsRqmStatus(run_status=StatusModel.Idle, active_rqm_status=[])


class ExperimentStateModel(BaseModel):
    status: StatusModel
    experiment: RbsJobModel

    class Config:
        use_enum_values = True
