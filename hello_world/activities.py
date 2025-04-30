from typing import Any, Dict

from application_sdk.activities import ActivitiesInterface
from application_sdk.common.logger_adaptors import get_logger
from application_sdk.inputs.statestore import StateStoreInput
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class HelloWorldActivities(ActivitiesInterface):
    @activity.defn
    async def say_hello(self, name: str) -> str:
        activity.logger.info(f"Saying hello to {name}")
        return f"Hello, {name}!"

    @activity.defn
    async def get_workflow_args(self, workflow_id: str) -> Dict[str, Any]:
        workflow_args = StateStoreInput.extract_configuration(workflow_id)
        return workflow_args
