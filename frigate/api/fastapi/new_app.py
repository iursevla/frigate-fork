import logging

from fastapi import FastAPI

from .. import preview
from .routers import logs, test

logger = logging.getLogger(__name__)


# TODO: This should follow the same pattern as the flask app.
def create_fastapi_app(frigate_config, flask_app):
    logger.info("Starting FastAPI app")
    app = FastAPI(debug=False)
    app.include_router(test.router)
    app.include_router(logs.router)
    app.include_router(preview.router)
    app.frigate_config = frigate_config

    return app
