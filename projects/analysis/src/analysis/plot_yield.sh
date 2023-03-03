#!/bin/bash

echo "Running plot_yield.py"
echo "Choose detector: "
read detector

/home/mca/dev/waspy/venv/bin/python plot_yield.py $detector