#!/bin/bash
export config_file="./default_config.toml"
export faker=false
export env_state="dev"
export trend_store="/tmp/trends/"
export logbook_url="http://127.0.0.1:8001"

source ../../venv/bin/activate
#uvicorn --reload --factory mill:create_app --log-level warning --host="localhost" --port=8000
uvicorn --factory src.mill.main:create_app --log-level warning --host="localhost" --port=8000 --reload
