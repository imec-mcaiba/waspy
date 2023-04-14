from typing import Optional
from pydantic import BaseSettings, BaseModel

from mill.erd_entities import ErdConfig
from mill.entities import AnyDriverConfig
from mill.rbs_entities import RbsConfig
import logging
import tomli

logging.basicConfig(
    format='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
    level=logging.INFO,
    datefmt='%Y.%m.%d__%H:%M__%S')


class MillConfig(BaseModel):
    any: Optional[AnyDriverConfig]
    rbs: Optional[RbsConfig]
    erd: Optional[ErdConfig]


class GlobalConfig(BaseSettings):
    CONFIG_FILE: Optional[str]
    FAKER = False
    ENV_STATE = "dev"
    TREND_STORE = "/root/trends/"
    LOGBOOK_URL = ""


def make_mill_config(config_file) -> MillConfig:
    with open(config_file, "rb") as f:
        conf_from_file = tomli.load(f)
        logging.info("[WASPY.MILL.CONFIG] Loaded: " + str(conf_from_file))

        for setup_key, setup_item in conf_from_file.items():
            for hardware_key, hardware_item in setup_item["drivers"].items():
                hardware_item["proxy"] = "/api/" + setup_key + "/" + hardware_key

        return MillConfig.parse_obj(conf_from_file)
