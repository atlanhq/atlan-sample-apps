import asyncio

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity


logger = get_logger(__name__)
activity.logger = logger


class SampleActivities(ActivitiesInterface):
    @activity.defn
    async def activity_1(self):
        logger.info("Activity 1")

        await asyncio.sleep(5)

        return

    @activity.defn
    async def activity_2(self):
        logger.info("Activity 2")

        await asyncio.sleep(5)

        return

