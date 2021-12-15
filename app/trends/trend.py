import json
from threading import Thread
from app.http_routes.http_helper import get_text
from pathlib import Path
import time
from datetime import datetime, timedelta
import pandas as pd
from threading import Lock


BASE_PATH = Path("/tmp/trends")


def get_path(today):
    return BASE_PATH / str("trends_" + today + ".txt")


class Trend(Thread):
    _lock: Lock

    def __init__(self):
        Thread.__init__(self)
        self._lock = Lock()
        self.data = None

    def run(self):
        Path.mkdir(Path("/tmp/trends/"), parents=True, exist_ok=True)

        while True:
            time.sleep(1)
            value = get_text("http://localhost:8000/api/some_number")
            today = datetime.now().strftime("%Y-%m-%d")
            with self._lock:
                if not Path(get_path(today)).is_file():
                    print("file does not exist")
                    with open(get_path(today), 'a') as f:
                        line = "timestamp,value\n"
                        f.write(line)

                with open(get_path(today), 'a') as f:
                    line = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "," + value + "\n"
                    f.write(line)

                self.data = pd.read_csv(get_path(today))
                self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])

    def get_last_10_minutes(self):
        right_now = datetime.now()
        before = right_now - timedelta(minutes=10)
        idx = pd.date_range(before.strftime("%Y-%m-%d %H:%M:%S"), right_now.strftime("%Y-%m-%d %H:%M:%S"), freq='1S')
        with self._lock:
            return self.data.loc[self.data['timestamp'].isin(idx)].to_dict(orient='list')

    def get_last_hour(self):
        right_now = datetime.now()
        before = right_now - timedelta(hours=1)
        idx = pd.date_range(before.strftime("%Y-%m-%d %H:%M:%S"), right_now.strftime("%Y-%m-%d %H:%M:%S"), freq='1S')
        with self._lock:
            return self.data.loc[self.data['timestamp'].isin(idx)].to_dict(orient='list')

    def get_last_day(self):
        right_now = datetime.now()
        before = right_now - timedelta(days=1)
        idx = pd.date_range(before.strftime("%Y-%m-%d %H:%M:%S"), right_now.strftime("%Y-%m-%d %H:%M:%S"), freq='1S')
        with self._lock:
            return self.data.loc[self.data['timestamp'].isin(idx)].to_dict(orient='list')


    def get_values(self):
        today = datetime.now().strftime("%Y-%m-%d")
        with self._lock:
            data = pd.read_csv(get_path(today))

        data = data.head(10000)
        return data.to_dict(orient='list')


