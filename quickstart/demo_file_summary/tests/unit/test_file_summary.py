import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.activities import FileSummaryActivities


class TestFileSummaryActivities(unittest.IsolatedAsyncioTestCase):
    """Unit tests for File Summary activities."""

    async def test_summarize_status_counts(self):
        """Test the status count summarization activity."""
        # Prepare test data
        test_records = [
            {"id": 1, "status": "completed"},
            {"id": 2, "status": "pending"},
            {"id": 3, "status": "completed"},
            {"id": 4, "status": "failed"},
            {"id": 5, "status": "pending"},
        ]

        workflow_config = {
            "input_file": "input/test.json",
            "output_file": "output/test_summary.json",
        }

        # Mock the ObjectStoreClient
        with patch("app.activities.ObjectStoreClient") as mock_store_class:
            mock_store = MagicMock()
            mock_store_class.return_value = mock_store

            # Mock get to return test data
            mock_store.get = AsyncMock(return_value=json.dumps(test_records))
            # Mock set to capture output
            mock_store.set = AsyncMock()

            # Create activity instance and execute
            activities = FileSummaryActivities()
            result = await activities.summarize_status_counts(workflow_config)

            # Verify the result
            expected_counts = {"completed": 2, "pending": 2, "failed": 1}
            self.assertEqual(result, expected_counts)

            # Verify object store interactions
            mock_store.get.assert_called_once_with("input/test.json")
            mock_store.set.assert_called_once()

            # Verify the output that was written
            call_args = mock_store.set.call_args
            self.assertEqual(call_args[0][0], "output/test_summary.json")

            # Parse and verify the written summary
            written_data = json.loads(call_args[0][1])
            self.assertEqual(written_data["total_records"], 5)
            self.assertEqual(written_data["status_counts"], expected_counts)

    async def test_summarize_with_unknown_status(self):
        """Test handling of records without status field."""
        test_records = [
            {"id": 1, "status": "active"},
            {"id": 2},  # No status field
            {"id": 3, "status": "active"},
        ]

        workflow_config = {
            "input_file": "input/test.json",
            "output_file": "output/test_summary.json",
        }

        with patch("app.activities.ObjectStoreClient") as mock_store_class:
            mock_store = MagicMock()
            mock_store_class.return_value = mock_store
            mock_store.get = AsyncMock(return_value=json.dumps(test_records))
            mock_store.set = AsyncMock()

            activities = FileSummaryActivities()
            result = await activities.summarize_status_counts(workflow_config)

            # Verify unknown status is counted
            self.assertEqual(result["active"], 2)
            self.assertEqual(result["unknown"], 1)


if __name__ == "__main__":
    unittest.main()
