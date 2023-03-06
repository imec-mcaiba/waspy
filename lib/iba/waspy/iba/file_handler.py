import traceback
from datetime import datetime
from pathlib import Path
from shutil import move, copy2, copytree
from typing import Dict, Union
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

import io
import logging
import pandas as pd
import json


class FileHandler:
    _local: Path
    _remote: Union[Path, None]
    _base_folder: Path
    _sub_folder: Path
    _remote_enable: bool

    def __init__(self, local_dir: Path, remote_dir: Union[Path, None] = None):
        self._local = local_dir
        self._remote = remote_dir
        self._sub_folder = Path("")
        self._base_folder = Path("")
        self._make_folders()

    def set_base_folder(self, folder: str):
        self._base_folder = Path(folder)
        self._sub_folder = Path("")
        subdir = "old_" + datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

        Path.mkdir(self._local / self._base_folder, exist_ok=True)
        self._move_files(self._local, subdir)

        if self._remote:
            Path.mkdir(self._remote / self._base_folder, exist_ok=True)
            self._move_files(self._remote, subdir)

    def cd_folder(self, folder: str):
        self._sub_folder = self._sub_folder / Path(folder)
        Path.mkdir(self._local / self._base_folder / self._sub_folder, exist_ok=True)

        if self._remote:
            Path.mkdir(self._remote / self._base_folder / self._sub_folder, exist_ok=True)

    def cd_folder_up(self):
        self._sub_folder = self._sub_folder.parent

    def clear_sub_folder(self):
        self._sub_folder = Path("")

    def write_matplotlib_fig_to_disk(self, filename: str, fig: Figure):
        plt.subplots_adjust(hspace=0.5)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        self.write_bytes_to_disk(filename, buf)
        plt.close(fig)
        plt.clf()

    def write_bytes_to_disk(self, filename: str, content: io.BytesIO):
        content.seek(0)
        with open(self._in_local_path(filename), "wb") as f:
            f.write(content.getbuffer().tobytes())
        if self._remote:
            _try_copy(self._in_local_path(filename), self._in_remote_path(filename))
        content.close()

    def write_text_to_disk(self, filename: str, content: str):
        with open(self._in_local_path(filename), 'w+') as f:
            f.write(content)
        if self._remote:
            _try_copy(self._in_local_path(filename), self._in_remote_path(filename))

    def read_text_from_disk(self, filename: str):
        with open(self._in_local_path(filename), 'r') as f:
            return f.read()

    def read_json_from_disk(self, filename: str):
        with open(self._in_local_path(filename), 'r') as f:
            return json.load(f)

    def write_csv_panda_to_disk(self, filename: str, content: Dict):
        df = pd.DataFrame.from_dict(content)
        self.write_text_to_disk(filename, df.to_csv(index=False))

    def write_json_to_disk(self, filename, content: Dict):
        json_content = json.dumps(content, indent=4, default=str)
        self.write_text_to_disk(filename, json_content)

    def get_local_dir(self):
        return self._local

    def _in_local_path(self, file_stem: str):
        return self._local / self._base_folder / self._sub_folder / file_stem

    def _in_remote_path(self, file_stem: str):
        return self._remote / self._base_folder / self._sub_folder / file_stem

    def _make_folders(self):
        Path.mkdir(self._local, parents=True, exist_ok=True)
        if self._remote:
            Path.mkdir(self._remote, parents=True, exist_ok=True)

    def _move_files(self, base, subdir):
        files_to_move = [x for x in (base / self._base_folder).iterdir() if not x.stem.startswith("old_")]
        if files_to_move:
            full_subdir = base / self._base_folder / subdir
            logging.info("[WASPY.IBA.FILE_WRITER] Existing files found, moving them to: '" + str(full_subdir) + "'.")
            Path.mkdir(full_subdir, exist_ok=True)
            for file in files_to_move:
                move(file, full_subdir)

    def copy_folder_to_base(self, source, sub_folder):
        destination = self._local / self._base_folder / sub_folder
        logging.info(f"[WASPY.IBA.FILE_WRITER] copying {source} to {destination}")
        copytree(source, destination)


def _try_copy(source, destination):
    logging.info(
        "[WASPY.IBA.FILE_WRITER] copying {source} to {destination}".format(source=source, destination=destination))
    try:
        Path.mkdir(destination.parent, exist_ok=True)
        copy2(source, destination)
    except:
        logging.error(traceback.format_exc())
