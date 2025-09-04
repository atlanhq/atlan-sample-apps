import pytest
from app.activities import HelloWorldActivities
from app.workflow import HelloWorldWorkflow


class TestHelloWorldWorkflowWorker:
    @pytest.fixture()
    def workflow(self) -> HelloWorldWorkflow:
        return HelloWorldWorkflow()

    @pytest.fixture()
    def activities(self) -> HelloWorldActivities:
        return HelloWorldActivities()

    @staticmethod
    @pytest.mark.asyncio
    async def test_say_hello(activities: HelloWorldActivities):
        result = await activities.say_hello("John Doe")
        assert result == "Hello, John Doe!"

        result = activities.say_hello_sync("John Doe")
        assert result == "Hello, John Doe!"
