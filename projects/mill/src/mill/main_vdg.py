import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from mill import mill_routes, pellicle_routes
from mill.recipe_meta import RecipeMeta
from waspy.iba.file_handler import FileHandler
from mill.systemd_routes import build_systemd_endpoints
from mill.logbook_db import LogBookDb
from mill.job_runner import JobRunner
from waspy.iba import pellicle_setup as pellicle_lib
from mill.config import GlobalConfig, make_mill_config, MillConfig


def create_app():
    env_conf = GlobalConfig()
    logging.info("[WASPY.MILL.MAIN] Loaded config: " + env_conf.json())
    mill_config = make_mill_config(env_conf.CONFIG_FILE)

    if env_conf.ENV_STATE == "dev":
        origins = ['http://localhost:3000']
    else:
        origins = ['http://localhost']
    app = FastAPI(docs_url=None, redoc_url=None, swagger_ui_parameters={"syntaxHighlight": False})
    app.mount("/static", StaticFiles(directory="static"), name="static")

    mill_routes.build_conf_endpoint(app, mill_config)
    mill_routes.build_api_endpoints(app, mill_config.any.drivers)

    logbook_db = LogBookDb(env_conf.LOGBOOK_URL)

    build_job_and_hw_routes(app, mill_config, logbook_db)

    build_systemd_endpoints(app, mill_config)

    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                       allow_methods=['*'], allow_headers=['*'])

    @app.get("/", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="openapi.json",
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="static/swagger-ui-bundle.js",
            swagger_css_url="static/swagger-ui.css",
            swagger_ui_parameters={"syntaxHighlight": False}
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/favicon.ico")
    def favicon():
        return FileResponse('static/favicon.png')

    return app


def build_job_and_hw_routes(router, mill_config: MillConfig, logbook_db: LogBookDb):
    if mill_config.pellicle:
        job_runner = JobRunner()

        pellicle_setup = pellicle_lib.PellicleSetup(mill_config.pellicle.get_driver_urls())
        pellicle_file_writer = FileHandler(mill_config.pellicle.local_dir, mill_config.pellicle.remote_dir)
        pellicle_setup.configure_detectors(mill_config.pellicle.drivers.caen.detectors)

        recipe_meta = RecipeMeta(logbook_db, Path('./recipe_meta'))

        pellicle_routes.build_driver_endpoints(router, mill_config.pellicle.drivers)
        pellicle_routes.build_setup_endpoints(router, pellicle_setup)
        pellicle_routes.build_meta_endpoints(router, recipe_meta)

        env_conf = GlobalConfig()
        if env_conf.FAKER:
            pellicle_setup.fake()

        job_runner.daemon = True
        job_runner.start()
