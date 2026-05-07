from app.contracts import HelloInput, HelloOutput
from application_sdk.app.base import App
from application_sdk.app.task import task
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


class HelloWorldApp(App):
    @task(timeout_seconds=10, heartbeat_timeout_seconds=10)
    async def say_hello(self, input: HelloInput) -> HelloOutput:
        logger.info("Saying hello to %s", input.name)
        return HelloOutput(message=f"Hello, {input.name}!")

    async def run(self, input: HelloInput) -> HelloOutput:  # type: ignore[override]
        return await self.say_hello(input)
