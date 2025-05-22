import asyncio, json
from datetime import timedelta
from typing import Any, Callable, Coroutine, Dict, List, Sequence, Type

from application_sdk.activities import ActivitiesInterface
from application_sdk.workflows import WorkflowInterface
from temporalio import workflow

from app.activities import PokemonCrawlerActivities


@workflow.defn
class PokemonCrawlerWorkflow(WorkflowInterface):
    activities_cls: Type[PokemonCrawlerActivities] = (
        PokemonCrawlerActivities
    )

    @workflow.run
    async def run(self, workflow_config: Dict[str, Any]) -> None:
        workflow_id = workflow_config["workflow_id"]

        workflow_args: Dict[str, Any] = await workflow.execute_activity(
            self.activities_cls.get_workflow_args,
            workflow_id,
            start_to_close_timeout=timedelta(seconds=1000),
        )

        include_filter : str = workflow_args.get("metadata", {}).get("include_filter", "")
        exclude_filter : str = workflow_args.get("metadata", {}).get("exclude_filter", "")
        filters = {
            "include_filter": include_filter,
            "exclude_filter": exclude_filter
        }
        workflow.logger.info("Starting hello world workflow")

        activities: List[Coroutine[Any, Any, Any]] = [
            workflow.execute_activity(
                self.activities_cls.extract_pokemons,
                filters,
                start_to_close_timeout=timedelta(seconds=1000),
            )
        ]

        # Wait for all activities to complete
        await asyncio.gather(*activities)
        workflow.logger.info("Hello world workflow completed")

    @staticmethod
    def get_activities(activities: ActivitiesInterface) -> Sequence[Callable[..., Any]]:
        """Get the sequence of activities to be executed by the workflow.

        Args:
            activities (ActivitiesInterface): The activities instance
                containing the hello world operations.

        Returns:
            Sequence[Callable[..., Any]]: A sequence of activity methods to be executed
                in order.
        """
        if not isinstance(activities, PokemonCrawlerActivities):
            raise TypeError("Activities must be an instance of PokemonCrawlerActivities")

        return [
            activities.get_workflow_args,
            activities.extract_pokemons
        ]
