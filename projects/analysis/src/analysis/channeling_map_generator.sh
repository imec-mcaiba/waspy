#!/bin/bash

echo "Running channeling_map_generator.py"
echo "Choose minimum energy: "
read e_min
echo "Choose maximum energy: "
read e_max
echo "Choose detector: "
read detector

/home/mca/dev/waspy/venv/bin/python channeling_map_generator.py $e_min $e_max $detector ".."
