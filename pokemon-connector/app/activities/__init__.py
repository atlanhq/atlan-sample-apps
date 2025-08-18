import json
from typing import Any, Dict

from application_sdk.activities import ActivitiesInterface
from application_sdk.inputs.statestore import StateStore
from temporalio import activity
from application_sdk.handlers import HandlerInterface


class PokemonCrawlerActivities(ActivitiesInterface):
    def __init__(self, handler: HandlerInterface):
        self.handler = handler
        super().__init__()

    @activity.defn
    async def say_hello(self, name: str) -> str:
        activity.logger.info(f"Saying hello to {name}")
        return f"Hello, {name}!"

    @activity.defn
    async def extract_pokemons(self, filters: Dict[Any, Any]) -> Any:
        activity.logger.info(f"Extraction with following params {filters}")
        include_filter = filters["include_filter"]
        exclude_filter = filters["exclude_filter"]

        results = await self.handler.fetch_metadata(metadata_type="All", include_filter=include_filter, exclude_filter=exclude_filter)
        with open("/tmp/raw", "w") as f:
            for result in results:
                data = json.dumps(result)
                f.write(data + "\n")

        return True

    @activity.defn
    async def get_workflow_args(self, workflow_id: str) -> Dict[str, Any]:
        workflow_args = StateStore.extract_configuration(workflow_id)
        return workflow_args
