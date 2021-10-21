from pathlib import Path
from typing import Optional, Dict

from pydantic import BaseSettings, BaseModel
from app.hardware_controllers.entities import HwControllerConfig
from app.rbs_experiment.entities import RbsConfig
import logging
import tomli

logging.basicConfig(
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
    level=logging.INFO,
    datefmt='%Y.%m.%d__%H:%M__%S')


class HiveConfig(BaseModel):
    hw_config: HwControllerConfig
    rbs_config: RbsConfig


class GlobalConfig(BaseSettings):
    CONFIG_FILE: Optional[str]
    FAKER = False
    ENV_STATE = "dev"


def make_rbs_config(config_dict: Dict) -> RbsConfig:
    rbs_config = config_dict["rbs"]
    for key, value in config_dict["rbs"]["hardware"].items():
        rbs_config["hardware"][key] = config_dict["generic"]["hardware"][value]
    return RbsConfig.parse_obj(rbs_config)


def make_hardware_config(config_dict: Dict) -> HwControllerConfig:
    hw_config = {"controllers": config_dict["generic"]["hardware"]}
    return HwControllerConfig.parse_obj(hw_config)


def make_hive_config(config_file):
    with open(config_file, "rb") as f:
        conf_from_file = tomli.load(f)
        return HiveConfig(hw_config=make_hardware_config(conf_from_file), rbs_config=make_rbs_config(conf_from_file))
