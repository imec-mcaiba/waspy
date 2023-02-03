import os
import sys
import glob
import re
from pathlib import Path

from waspy.iba.rbs_entities import Window, ChannelingMapYield
from waspy.iba.rbs_recipes import get_sum, save_channeling_map_to_disk
from waspy.iba.file_handler import FileHandler

window = Window(start=sys.argv[1], end=sys.argv[2])
optimize_detector_identifier = sys.argv[3]

recipe_name = sys.argv[4]
directory = "/tmp/ACQ/5_data/RBS22_084/old_2023-02-03_08.31.20/"
data_files_dir = os.path.join(directory, recipe_name)

cms_yields = []

for file in glob.glob(data_files_dir + f"/*_{optimize_detector_identifier}.txt"):
    print(file)
    reg_exp_file = f"{data_files_dir}/\d*_{recipe_name}_zeta(\S*)_theta(\S*)_{optimize_detector_identifier}\.txt"

    zeta, theta = re.search(reg_exp_file, file).groups()
    # print(f"zeta={zeta}, theta={theta}")

    data = []
    with open(file) as f:
        lines = f.readlines()
        for line in lines:
            reg_exp_line = "\d*, (\d*)"
            yield_data = re.search(reg_exp_line, line)
            if yield_data:
                data.append(int(yield_data.group(1)))

    energy_yield = get_sum(data, window)

    cms_yields.append(ChannelingMapYield(zeta=zeta, theta=theta, energy_yield=energy_yield))

file_handler = FileHandler(Path('/tmp/ACQ/channeling_map/'))
save_channeling_map_to_disk(file_handler, cms_yields, f"{recipe_name}_{window.start}_{window.end}_{optimize_detector_identifier}")
print(window.start, window.end, optimize_detector_identifier, data_files_dir)
