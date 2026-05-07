"""Smoke tests for the AE-triggered ingestion app."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.application import IngestionInput, IngestionOutput, SampleEventProcessorApp


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _mock_workflow_module():
    """Build a mock that mimics ``temporalio.workflow`` for unit tests."""
    wf = MagicMock()
    wf.logger = MagicMock()
    return wf


class TestApp(unittest.TestCase):
    def test_app_metadata(self):
        self.assertEqual(SampleEventProcessorApp.name, "sample-event-processor-app")
        self.assertEqual(SampleEventProcessorApp.version, "0.1.0")

    def test_run_with_no_iceberg_table_name_returns_zero(self):
        """Trigger payload missing iceberg_table_name → clean no-op."""
        app = SampleEventProcessorApp()
        with patch("app.application.workflow", _mock_workflow_module()):
            with patch.object(app, "handle_events", new=AsyncMock()) as handle:
                result = _run(app.run(IngestionInput()))
                self.assertEqual(result.processed, 0)
                handle.assert_not_called()

    def test_run_delegates_to_handle_events(self):
        """When iceberg_table_name is set, run() invokes handle_events with the input."""
        app = SampleEventProcessorApp()
        expected = IngestionOutput(
            processed=3,
            success=1,
            retry=1,
            failed=1,
            ack_path="artifacts/.../events_ack.parquet",
        )
        with patch("app.application.workflow", _mock_workflow_module()):
            with patch.object(
                app, "handle_events", new=AsyncMock(return_value=expected)
            ) as handle:
                input_ = IngestionInput(iceberg_table_name="reverse_sync_events")
                result = _run(app.run(input_))
                self.assertEqual(result.processed, 3)
                self.assertEqual(result.success, 1)
                self.assertEqual(result.retry, 1)
                self.assertEqual(result.failed, 1)
                self.assertIn("events_ack.parquet", result.ack_path)
                handle.assert_awaited_once_with(input_)


if __name__ == "__main__":
    unittest.main()
