import os
import sys
import glob
import re
from pathlib import Path

from waspy.iba.rbs_entities import Window, ChannelingMapYield
from waspy.iba.rbs_recipes import get_sum, save_channeling_map_to_disk
from waspy.iba.file_handler import FileHandler


def create_channeling_map():
    cms_yields = []
    unknown_recipe_str = "unknown_recipe"
    recipe_name = unknown_recipe_str

    file_search_str = data_files_dir + f"/*_{optimize_detector_identifier}.txt"
    assert glob.glob(file_search_str), f"Files do not exist, {file_search_str}. Check if detector name is correct."

    for file in glob.glob(file_search_str):
        if sys.platform == "linux" or sys.platform == "linux2":
            reg_exp_file = f"{data_files_dir}\/?\d*_(\S*)_zeta(\S*)_theta(\S*)_{optimize_detector_identifier}\.txt"
        elif sys.platform == "win32":
            files_dir = data_files_dir.replace("\\", "\\\\")
            reg_exp_file = f"{files_dir}\/?\\\\\d*_(\S*)_zeta(\S*)_theta(\S*)_{optimize_detector_identifier}\.txt"
        found = re.search(reg_exp_file, file)

        if found:
            recipe_name, zeta, theta = found.groups()
            data = []
            with open(file) as f:
                lines = f.readlines()
                for line in lines:
                    reg_exp_line = "\d*, (\d*)"
                    yield_data = re.search(reg_exp_line, line)
                    if yield_data:
                        data.append(int(yield_data.group(1)))

            energy_yield = get_sum(data, energy_window)
            cms_yields.append(ChannelingMapYield(zeta=zeta, theta=theta, energy_yield=energy_yield))


    assert recipe_name is not unknown_recipe_str, f"No recipe name found in {data_files_dir}."

    file_handler = FileHandler(Path(data_files_dir))
    title = f"{recipe_name}_{energy_window.start}_{energy_window.end}_" \
            f"{optimize_detector_identifier}"
    save_channeling_map_to_disk(file_handler, cms_yields, title)


if __name__ == "__main__":
    usage = """
    Usage:
    ======
    
    $ venv/bin/python projects/scripts/src/scripts/channeling_map_generator.py [minimum energy: int] [maximum energy: int] 
        [optimize_detector_identifier: str] [data_files_dir: str] 
    
    Example:
    $ venv/bin/python projects/scripts/src/scripts/channeling_map_generator.py 10 900 d01 /tmp/ACQ/5_data/RBS22_084/AE200856_D07/ 
    
    """

    assert len(sys.argv) == 5, f"Not enough arguments given. \n {usage}"

    energy_window = Window(start=sys.argv[1], end=sys.argv[2])
    optimize_detector_identifier = sys.argv[3]
    data_files_dir = sys.argv[4]

    assert os.path.exists(data_files_dir), f"Folder {data_files_dir} does not exist."

    create_channeling_map()
