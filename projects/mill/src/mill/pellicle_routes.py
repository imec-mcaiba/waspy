import logging
import traceback

from fastapi import Body, File, UploadFile
from starlette import status
from starlette.responses import FileResponse, Response

from mill.entities import CaenConfig
from mill.mill_routes import build_get_redirect, build_post_redirect, build_histogram_redirect, \
    build_packed_histogram, build_detector_endpoints
from mill.recipe_meta import RecipeMeta
from waspy.iba.pellicle_entities import PositionCoordinates
from waspy.iba.pellicle_setup import PellicleSetup


def build_driver_endpoints(http_server, pellicle_hardware):
    for key, daemon in pellicle_hardware.dict().items():
        build_get_redirect(http_server, daemon['proxy'], daemon['url'], ["PELLICLE"])
        build_post_redirect(http_server, daemon['proxy'], daemon['url'], ["PELLICLE"])
        if daemon['type'] == 'caen':
            caen_daemon = CaenConfig.parse_obj(daemon)
            build_histogram_redirect(http_server, daemon['proxy'], daemon['url'], ["PELLICLE"])
            build_packed_histogram(http_server, daemon['proxy'], daemon['url'], ["PELLICLE"])
            build_detector_endpoints(http_server, daemon['proxy'], daemon['url'], caen_daemon.detectors, ["PELLICLE"])


def build_setup_endpoints(http_server, pellicle_setup: PellicleSetup):
    @http_server.get("/api/pellicle/status", tags=["PELLICLE"], summary="Retrieves the pellicle status")
    def get_pellicle_status():
        return pellicle_setup.get_status()

    @http_server.post("/api/pellicle/load", tags=["PELLICLE"], summary="Move the pellicle setup to the load/unload position")
    def pellicle_load(load: bool):
        if load:
            pellicle_setup.load()

    @http_server.post("/api/pellicle/position", tags=["PELLICLE"], summary="Move the pellicle setup to a specified position")
    def pellicle_move(position: PositionCoordinates):
        pellicle_setup.move(position)


def build_meta_endpoints(http_server, recipe_meta: RecipeMeta):
    @http_server.post("/api/pellicle/recipe_meta_template", tags=["PELLICLE"], summary="update the experiment metadata template")
    async def upload_pellicle_recipe_meta_template(response: Response, file: UploadFile = File(...)):
        try:
            file_bytes = await file.read()
            contents = file_bytes.decode('utf-8')
            return recipe_meta.write_pellicle_recipe_meta_template(contents)
        except Exception as e:
            logging.error(traceback.format_exc())
            response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            return str(e)

    @http_server.get("/api/pellicle/recipe_meta_template", tags=["PELLICLE"], summary="get the experiment metadata template", response_class=FileResponse)
    async def download_pellicle_recipe_meta_template():
        return recipe_meta.get_pellicle_recipe_meta_template_path()

    @http_server.get("/api/pellicle/recipe_meta", tags=["PELLICLE"], summary="get the experiment metadata")
    def get_pellicle_recipe_meta():
        text = recipe_meta.fill_pellicle_recipe_meta()
        return Response(content=text, media_type="text/plain")



