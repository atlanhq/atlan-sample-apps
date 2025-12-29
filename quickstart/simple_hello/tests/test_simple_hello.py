"""Tests for simple hello world workflow."""

import pytest
from app.activities import SimpleHelloActivities
from app.workflow import SimpleHelloWorkflow


class TestSimpleHelloWorkflow:
    """Test suite for SimpleHelloWorkflow."""

    @pytest.fixture()
    def workflow(self) -> SimpleHelloWorkflow:
        """Create a SimpleHelloWorkflow instance for testing."""
        return SimpleHelloWorkflow()

    @pytest.fixture()
    def activities(self) -> SimpleHelloActivities:
        """Create a SimpleHelloActivities instance for testing."""
        return SimpleHelloActivities()

    @staticmethod
    @pytest.mark.asyncio
    async def test_output_hello_world(activities: SimpleHelloActivities):
        """Test that the activity outputs Hello World !!."""
        result = await activities.output_hello_world()
        assert result == "Hello World !!"

