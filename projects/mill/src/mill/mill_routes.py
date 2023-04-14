import os
from typing import Dict, List

import requests
from fastapi import status, Response
from pydantic import create_model
from pydantic.generics import GenericModel

from mill.entities import AnyDriverGroup
from mill.config import MillConfig
from starlette.requests import Request

from waspy.drivers.caen import Caen, DetectorMetadata
from waspy.drivers.http_helper import get_text_with_response_code, post_dictionary, get_json_with_response_code
from waspy.iba.rbs_entities import Detector


def build_api_endpoints(http_router, any_hardware: AnyDriverGroup):
    for key, daemon in any_hardware.__root__.items():
        build_get_redirect(http_router, daemon.proxy, daemon.url, ["ANY API"])
        build_post_redirect(http_router, daemon.proxy, daemon.url, ["ANY API"])
        if daemon.type == 'caen':
            build_histogram_redirect(http_router, daemon.proxy, daemon.url, ["ANY API"])
            build_packed_histogram(http_router, daemon.proxy, daemon.url, ["ANY API"])
        if daemon.type == 'mpa3':
            build_mpa3_histogram_redirect(http_router, daemon.proxy, daemon.url, ["ANY API"])


def build_conf_endpoint(http_router, mill_config: MillConfig):
    @http_router.get("/api/config")
    async def api_get_mill_config():
        return mill_config


def build_histogram_redirect(some_router, from_url, to_url, tags):
    @some_router.get(from_url + "/histogram/{board_id}/{channel}", tags=tags)
    async def histogram(board_id: str, channel: int):
        caen = Caen(to_url)
        data = caen.get_raw_histogram(board_id, channel)
        return data


def histogram(response: Response, to_url, board: str, channel: int, start: int, end: int, width: int):
    if width > end - start:
        response.status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        return {}
    caen = Caen(to_url)
    detector = DetectorMetadata(board=board, channel=channel, bins_min=start, bins_max=end, bins_width=width)
    return caen.get_histogram(detector)


def build_packed_histogram(some_router, from_url, to_url, tags):
    @some_router.get(from_url + "/histogram/{board}/{channel}/pack/{start}-{end}-{width}", tags=tags)
    async def get_any_histogram(response: Response, board: str, channel: int, start: int, end: int, width: int):
        return histogram(response, to_url, board, channel, start, end, width)


def build_detector_endpoints(some_router, from_url, to_url, detectors: List[Detector], tags):
    for detector in detectors:
        @some_router.get(from_url + "/detector/" + detector.identifier, tags=tags)
        async def get_histogram(request: Request, response: Response):
            path = str(request.url.path)
            last_part = path.split("/")[-1]

            active_detector = next(some_detector for some_detector in detectors
                                   if some_detector.identifier == last_part)

            return histogram(response, to_url, active_detector.board, active_detector.channel,
                             active_detector.bins_min, active_detector.bins_max, active_detector.bins_width)

        @some_router.get(from_url + "/detector/" + detector.identifier + "_compressed", tags=tags)
        async def get_histogram(request: Request, response: Response):
            path = str(request.url.path)
            last_part = path.split("/")[-1]

            active_detector = next(some_detector for some_detector in detectors
                                   if some_detector.identifier == last_part)

            return histogram(response, to_url, active_detector.board, active_detector.channel,
                             active_detector.bins_min, active_detector.bins_max, 1024)


def _make_driver_schema(class_name, url):
    values = {}

    class BaseSchema(GenericModel):
        __root__: Dict

        class Config:
            try:
                schema_extra = requests.get(url + "/caps", timeout=5).json()
            except:
                pass

    return create_model(class_name, **values, __base__=BaseSchema)


def _convert_snakecase_to_camelcase(text):
    return ''.join(word.title() for word in text.split('_'))


def build_post_redirect(some_router, from_url, to_url, tags):
    hw_schema = _make_driver_schema(_convert_snakecase_to_camelcase(from_url), to_url)

    @some_router.post(from_url, tags=tags)
    async def api_key_post(response: Response, hardware_command: hw_schema):  # type: ignore
        code, body = post_dictionary(to_url, hardware_command.__root__)
        response.status_code = code
        return body


def build_get_redirect(some_router, from_url, to_url, tags):
    @some_router.get(from_url, tags=tags)
    async def api_key_get(response: Response):  # type: ignore
        try:
            response.status_code, resp = get_json_with_response_code(to_url)
        except Exception as e:
            response.status_code = status.HTTP_404_NOT_FOUND
            resp = str(e)
        return resp


def build_mpa3_histogram_redirect(some_router, from_url, to_url, tags):
    @some_router.get(from_url + "/histogram", tags=tags)
    async def histogram(response: Response):
        print(to_url)
        url = to_url + "/histogram"
        response.status_code, resp = get_text_with_response_code(url)
        return resp
