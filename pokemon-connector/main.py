import asyncio
import logging
import os

from application_sdk.application.fastapi import FastAPIApplication, HttpWorkflowTrigger
from application_sdk.clients.temporal import TemporalClient
from application_sdk.common.logger_adaptors import AtlanLoggerAdapter
from application_sdk.worker import Worker
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.activities import PokemonCrawlerActivities
from app.handlers.handlers import PokeHandler
from app.workflows import PokemonCrawlerWorkflow

logger = AtlanLoggerAdapter(logging.getLogger(__name__))

APPLICATION_NAME = "hello-world"
APP_PORT = int(os.getenv("ATLAN_APP_HTTP_PORT", 8000))
APP_HOST = os.getenv("ATLAN_APP_HTTP_HOST", "0.0.0.0")
APP_DASHBOARD_PORT = int(os.getenv("ATLAN_APP_DASHBOARD_HTTP_PORT", 8233))
APP_DASHBOARD_HOST = os.getenv("ATLAN_APP_DASHBOARD_HTTP_HOST", "0.0.0.0")


# Set up templates
templates = Jinja2Templates(directory="frontend/templates")


async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_dashboard_http_port": APP_DASHBOARD_PORT,
            "app_dashboard_http_host": APP_DASHBOARD_HOST,
            "app_http_port": APP_PORT,
            "app_http_host": APP_HOST,
        },
    )


def setup_routes(app: FastAPIApplication):
    app.app.get("/")(home)
    app.app.mount("/", StaticFiles(directory="frontend/static"), name="static")


async def initialize_and_start():
    temporal_client = TemporalClient(
        application_name=APPLICATION_NAME,
    )
    await temporal_client.load()

    handler = PokeHandler()
    activities = PokemonCrawlerActivities(
        handler=handler
    )

    # Creating workflow
    worker: Worker = Worker(
        temporal_client=temporal_client,
        workflow_classes=[PokemonCrawlerWorkflow],
        temporal_activities=PokemonCrawlerWorkflow.get_activities(activities),
    )

    # Creating FastAPI application
    fast_api_app = FastAPIApplication(
        temporal_client=temporal_client,
        handler=handler
    )

    fast_api_app.register_workflow(
        PokemonCrawlerWorkflow,
        [
            HttpWorkflowTrigger(
                endpoint="/start",
                methods=["POST"],
                workflow_class=PokemonCrawlerWorkflow,
            )
        ],
    )

    # Setup routes
    setup_routes(fast_api_app)

    # Start worker in background
    await worker.start(daemon=True)
    # Starting FastAPI application
    await fast_api_app.start()


if __name__ == "__main__":
    asyncio.run(initialize_and_start())
    # atlan_app_builder.configure_open_telemetry()
