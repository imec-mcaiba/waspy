import logging
import traceback

from fastapi import Body, File, UploadFile
from starlette import status
from starlette.responses import FileResponse, Response

from mill.entities import CaenConfig
from mill.mill_routes import build_get_redirect, build_post_redirect, build_histogram_redirect, \
    build_packed_histogram, build_detector_endpoints
from mill.recipe_meta import RecipeMeta
from waspy.iba.rbs_entities import PositionCoordinates
from waspy.iba.rbs_setup import RbsSetup


def build_driver_endpoints(http_server, rbs_hardware):
    for key, daemon in rbs_hardware.dict().items():
        build_get_redirect(http_server, daemon['proxy'], daemon['url'], ["RBS"])
        build_post_redirect(http_server, daemon['proxy'], daemon['url'], ["RBS"])
        if daemon['type'] == 'caen':
            caen_daemon = CaenConfig.parse_obj(daemon)
            build_histogram_redirect(http_server, daemon['proxy'], daemon['url'], ["RBS"])
            build_packed_histogram(http_server, daemon['proxy'], daemon['url'], ["RBS"])
            build_detector_endpoints(http_server, daemon['proxy'], daemon['url'], caen_daemon.detectors, ["RBS"])


def build_setup_endpoints(http_server, rbs_setup: RbsSetup):
    @http_server.get("/api/rbs/status", tags=["RBS"], summary="Retrieves the rbs status")
    def get_rbs_status():
        return rbs_setup.get_status()

    @http_server.post("/api/rbs/load", tags=["RBS"], summary="Move the rbs setup to the load/unload position")
    def rbs_load(load: bool):
        if load:
            rbs_setup.load()

    @http_server.post("/api/rbs/position", tags=["RBS"], summary="Move the rbs setup to a specified position")
    def rbs_move(position: PositionCoordinates):
        rbs_setup.move(position)


def build_meta_endpoints(http_server, recipe_meta: RecipeMeta):
    @http_server.post("/api/rbs/recipe_meta_template", tags=["RBS"], summary="update the experiment metadata template")
    async def upload_rbs_recipe_meta_template(response: Response, file: UploadFile = File(...)):
        try:
            file_bytes = await file.read()
            contents = file_bytes.decode('utf-8')
            return recipe_meta.write_rbs_recipe_meta_template(contents)
        except Exception as e:
            logging.error(traceback.format_exc())
            response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            return str(e)

    @http_server.get("/api/rbs/recipe_meta_template", tags=["RBS"], summary="get the experiment metadata template", response_class=FileResponse)
    async def download_rbs_recipe_meta_template():
        return recipe_meta.get_rbs_recipe_meta_template_path()

    @http_server.get("/api/rbs/recipe_meta", tags=["RBS"], summary="get the experiment metadata")
    def get_rbs_recipe_meta():
        text = recipe_meta.fill_rbs_recipe_meta()
        return Response(content=text, media_type="text/plain")



