from typing import Any, Dict

from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

from app.handler.handler import HandlerClass

logger = get_logger(__name__)
activity.logger = logger


class ActivitiesClass(ActivitiesInterface):
    """
    Activities for the Weather app using the handler/client pattern.
    
    This class now delegates to WeatherHandler for all weather operations,
    following the proper separation of concerns.
    """

    def __init__(self, handler: HandlerClass | None = None):
        """Initialize WeatherActivities with a WeatherHandler.

        Args:
            weather_handler (Optional[WeatherHandler]): Optional WeatherHandler instance
        """
        self.weather_handler = handler or HandlerClass()

    #Define activities here