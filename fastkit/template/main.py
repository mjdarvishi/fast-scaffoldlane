from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import router
from app.core.exception.exception_handling import register_exception_handlers
from app.core.logging.logging_config import LogConfig
from app.core.project import get_app_name, get_app_version
from app.core.service_manager import ServiceManager

services = ServiceManager(logger_name=LogConfig.API_LOGGER_NAME, log_file="api.log")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await services.start_runtime_services()
    try:
        yield
    finally:
        await services.stop_runtime_services()


app = FastAPI(title=get_app_name(), version=get_app_version(), lifespan=lifespan)
services.bootstrap(app=app)
register_exception_handlers(app)
app.include_router(router)
