import logging
from pathlib import Path

from mill.logbook_db import LogBookDb
from waspy.iba.file_handler import FileHandler


class RecipeMeta:
    _db: LogBookDb
    _file_handler: FileHandler

    def __init__(self, db: LogBookDb, store_folder: Path):
        self._file_handler = FileHandler(local_dir=store_folder)
        self._db = db
        self._RBS_FILENAME = 'rbs_recipe_meta_template.txt'
        self._ERD_FILENAME = 'erd_recipe_meta_template.txt'
        self._PELLICLE_FILENAME = 'pellicle_recipe_meta_template.txt'

    def write_rbs_recipe_meta_template(self, content):
        return self._file_handler.write_text_to_disk(self._RBS_FILENAME, content)

    def get_rbs_recipe_meta_template_path(self):
        return self._file_handler.get_local_dir() / self._RBS_FILENAME

    def fill_rbs_recipe_meta(self):
        try:
            content = self._file_handler.read_text_from_disk(self._RBS_FILENAME)
            daybook = self._db.get_daybook()
            return fill_in_meta_template(content, daybook)
        except Exception as e:
            logging.error("Failed to fill in rbs recipe template metadata" + str(e))
            return ""

    def write_erd_recipe_meta_template(self, content):
        return self._file_handler.write_text_to_disk(self._ERD_FILENAME, content)

    def get_erd_recipe_meta_template_path(self):
        return self._file_handler.get_local_dir() / self._ERD_FILENAME

    def fill_erd_recipe_meta(self):
        try:
            content = self._file_handler.read_text_from_disk(self._ERD_FILENAME)
            daybook = self._db.get_daybook()
            return fill_in_meta_template(content, daybook)
        except:
            logging.error("Failed to fill in erd recipe template metadata" + str(e))
            return ""

    def write_pellicle_recipe_meta_template(self, content):
        return self._file_handler.write_text_to_disk(self._PELLICLE_FILENAME, content)

    def get_pellicle_recipe_meta_template_path(self):
        return self._file_handler.get_local_dir() / self._PELLICLE_FILENAME

    def fill_pellicle_recipe_meta(self):
        try:
            content = self._file_handler.read_text_from_disk(self._PELLICLE_FILENAME)
            daybook = self._db.get_daybook()
            return fill_in_meta_template(content, daybook)
        except Exception as e:
            logging.error("Failed to fill in pellicle recipe template metadata" + str(e))
            return ""


def fill_in_meta_template(content: str, values: dict) -> str:
    filled_in_template = ""
    for line in content.splitlines():
        replace_start_index = line.find("{{")
        replace_end_index = line.find("}}")
        if replace_start_index < replace_end_index:
            db_key = line[replace_start_index + 2:replace_end_index]
            local_value = values
            for nestedKey in db_key.split('.'):
                try:
                    local_value = local_value.get(nestedKey, "NOT FOUND")
                except:
                    local_value = "NOT FOUND"
            line = line.replace("{{" + db_key + "}}", str(local_value))
        filled_in_template += line + "\n"
    return filled_in_template
