import math
from typing import List

from pydantic import BaseModel, Field

from waspy.drivers.http_helper import generate_request_id, post_request, get_json, get_text_with_response_code, \
    DriverError


class DetectorMetadata(BaseModel):
    board: str
    channel: int
    bins_min: int
    bins_max: int
    bins_width: int = Field(
        description="The range between min and max will be rescaled to this value, The bins are combined with integer "
                    "sized bin intervals. values on the maximum side are potentially discarded")


class Caen:
    """A data acquisition system"""
    _url: str

    def __init__(self, url: str):
        self._url = url

    def clear(self):
        post_request(self._url, {'request_id': generate_request_id(), 'clear': True})

    def start(self):
        post_request(self._url, {'request_id': generate_request_id(), 'start': True})

    def stop(self):
        post_request(self._url, {'request_id': generate_request_id(), 'stop': True})

    def read_register(self, board_id: str, hex_register_address: str) -> str:
        request = {
            "request_id": generate_request_id(),
            "read_register": {
                "board_id": board_id,
                "register_address": hex_register_address
            }
        }
        post_request(self._url, request)
        response = get_json(self._url)
        return response["boards"][board_id]["register_value"]

    def do_detectors_exist(self, detectors: List[DetectorMetadata]):
        boards = self.get_status()["boards"]
        for detector in detectors:
            board = boards.get(detector.board)
            if board is None:
                return False
            nr_of_channels = len(board["channels"])
            if not detector.channel < nr_of_channels:
                return False
        return True

    def set_registry(self, board_id: str, registry_filename: str):
        post_request(self._url, {'request_id': generate_request_id(), 'stop': True})
        request = {
            "request_id": generate_request_id(),
            "upload_registry": {
                "board_id": board_id,
                "filename": registry_filename
            }
        }
        post_request(self._url, request)

    def get_raw_histogram(self, board, channel):
        url = self._url + f"/histogram?board={board}&channel={channel}"
        http_code, data = get_text_with_response_code(url)
        if http_code == 404:
            url = self._url + f"/histogram/{board}/{channel}"
            http_code, data = get_text_with_response_code(url)
            if http_code == 404:
                raise DriverError(f'Could not retrieve histogram. Does this detector: '
                              f'({board},{channel}) exist?')
        return data

    def get_histogram(self, meta_data: DetectorMetadata) -> List[int]:
        data = self.get_raw_histogram(meta_data.board, meta_data.channel)
        data = data.split(";")
        data.pop()
        data = [int(x.replace("\"", "")) for x in data]
        packed_data = _pack(data, meta_data.bins_min, meta_data.bins_max, meta_data.bins_width)
        return packed_data

    def get_status(self):
        return get_json(self._url)


def _pack(data: List[int], index_min, index_max, width) -> List[int]:
    subset = data[index_min:index_max]
    samples_to_group_in_bin = math.floor(len(subset) / width)
    packed_data = []
    for index in range(0, samples_to_group_in_bin * width, samples_to_group_in_bin):
        bin_sum = sum(subset[index:index + samples_to_group_in_bin])
        packed_data.append(bin_sum)
    return packed_data
