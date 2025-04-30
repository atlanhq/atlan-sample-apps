import pytest
from activities import HelloWorldActivities
from workflow import HelloWorldWorkflow


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
        result = await activities.say_hello("John Doe2")
        assert result == "Hello, John Doe2!"
