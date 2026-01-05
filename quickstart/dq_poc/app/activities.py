from typing import Any, Dict

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class DqPocActivities(ActivitiesInterface):
    @activity.defn
    def run_dq_poc_sync(self, workflow_args: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Running dq poc sample application sync")
        logger.info(f"Workflow args is as follows: {workflow_args}")
        # Dummy data returned from the activity (this is what we'll return via
        # the API).
        return {"dummy": True}
