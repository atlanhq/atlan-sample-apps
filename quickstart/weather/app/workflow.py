from datetime import timedelta
from typing import Any, Callable, Dict, Sequence

from app.activities import WeatherActivities
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

logger = get_logger(__name__)
workflow.logger = logger


@workflow.defn
class WeatherWorkflow(WorkflowInterface):
    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        """
        Orchestrate the weather summary flow:

        1. Read workflow args (supports username, city, units with defaults)
        2. Fetch and format current weather via activities
        3. Log the summary

        Args:
            workflow_config (Dict[str, Any]): Workflow configuration from the server.
        """
        activities_instance = WeatherActivities()

        # Merge any provided args (from frontend POST body or server config)
        workflow_args: Dict[str, Any] = await workflow.execute_activity_method(
            activities_instance.get_workflow_args,
            workflow_config,
            start_to_close_timeout=timedelta(seconds=10),
        )

        username: str = workflow_args.get("username", "Friend")
        city: str = workflow_args.get("city", "London")
        units: str = workflow_args.get("units", "celsius")

        # Build the summary (single activity handles geocoding + fetch + formatting)
        summary: str = await workflow.execute_activity(
            activities_instance.get_weather_summary,
            {"username": username, "city": city, "units": units},
            start_to_close_timeout=timedelta(seconds=20),
        )

        # Emit the result to logs; UI can be checked via Temporal Web
        logger.info(f"Weather summary ready: {summary}")

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        """
        Declare which activity methods are part of this workflow for the worker.
        """
        if not isinstance(activities, WeatherActivities):
            raise TypeError("Activities must be an instance of WeatherActivities")

        return [
            activities.get_weather_summary,
            activities.get_workflow_args,
            activities.test_weather_connectivity,
            activities.perform_preflight_check,
        ] 