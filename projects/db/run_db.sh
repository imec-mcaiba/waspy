#!/bin/bash

export DB_FILE="imec.db"
export DAYBOOK_FILE="daybook.toml"
source ../../venv/bin/activate
uvicorn --factory src.db.main:main --log-level warning --host="0.0.0.0" --port=8001
