from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class DqPocActivities(ActivitiesInterface):
    @activity.defn
    def run_dq_poc_sync(self) -> None:
        logger.info("Running dq poc sample application sync")
        logger.info("BROBROBROBRORBRO")
