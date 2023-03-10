#!/bin/bash
export config_file="./vdg_lab_config.toml"
export faker=false
export env_state="prod"
export logbook_url="https://db.capitan.imec.be"

source ../../venv/bin/activate
uvicorn --factory src.mill.main_vdg:create_app --log-level warning --host="0.0.0.0" --port=8000
