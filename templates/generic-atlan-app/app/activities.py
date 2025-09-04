from app.handler.handler import HandlerClass
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class ActivitiesClass(ActivitiesInterface):
    def __init__(self, handler: HandlerClass | None = None):
        self.handler = handler or HandlerClass()

    # Define activities here
