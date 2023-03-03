import os
import sys
import glob
import re
from pathlib import Path
from matplotlib import pyplot as plt

sys.path.insert(1, '../../dev/waspy')
from waspy.iba.file_handler import FileHandler


def plot_graph(recipe_name, yields, energies):
    fig, ax = plt.subplots(1)
    ax.plot(energies, yields)
    ax.set_title(recipe_name)
    ax.set_xlabel("Energy [keV]")
    ax.set_ylabel("Yield [C]")
    return fig


def plot_yield():
    unknown_recipe_str = "unknown_recipe"
    recipe_name = unknown_recipe_str

    file_search_str = data_files_dir + f"/*_{optimize_detector_identifier}.txt"
    assert glob.glob(file_search_str), f"Files do not exist, {file_search_str}. Check if detector name is correct."

    for file in glob.glob(file_search_str):
        reg_exp_file = f"{data_files_dir}\/?(\S*)_{optimize_detector_identifier}\.txt"

        recipe_name = re.search(reg_exp_file, file)
        if recipe_name:
            recipe_name = recipe_name.group(1)
            title = f'{recipe_name}_{optimize_detector_identifier}'
            yields = []
            energies = []
            with open(file) as f:
                lines = f.readlines()
                for line in lines:
                    reg_exp_line = "(\d*), (\d*)"
                    re_data = re.search(reg_exp_line, line)
                    if re_data:
                        energies.append(int(re_data.group(1)))
                        yields.append(int(re_data.group(2)))
            figure = plot_graph(title, yields, energies)
            print(f"Saving {title}")
            file_handler.write_matplotlib_fig_to_disk(f'{title}.png', figure)


    assert recipe_name is not unknown_recipe_str, f"No recipe name found in {data_files_dir}."


if __name__ == "__main__":
    usage = """
    Usage:
    ======

    $ venv/bin/python projects/analysis/src/analysis/plot_yield.py [optimize_detector_identifier: str]

    Example:
    $ venv/bin/python projects/analysis/src/analysis/plot_yield.py d01 

    """

    assert len(sys.argv) == 2, f"Not enough arguments given. \n {usage}"

    optimize_detector_identifier = sys.argv[1]
    data_files_dir = "../"

    plot_dir = f"plots_{optimize_detector_identifier}"
    file_handler = FileHandler(Path(data_files_dir))
    file_handler.set_base_folder(plot_dir)
    plot_yield()
