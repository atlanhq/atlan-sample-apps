"""Smoke tests for the AE-triggered ingestion app."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.application import (
    HandleEventsOutput,
    IngestionInput,
    LakehouseBatchProcessorApp,
    WriteAckOutput,
)


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _mock_workflow_module(run_id: str = "run-1"):
    """Build a mock that mimics ``temporalio.workflow`` for unit tests."""
    info = MagicMock()
    info.run_id = run_id
    wf = MagicMock()
    wf.info.return_value = info
    wf.logger = MagicMock()
    return wf


class TestApp(unittest.TestCase):
    def test_app_metadata(self):
        self.assertEqual(LakehouseBatchProcessorApp.name, "lakehouse-batch-processor")
        self.assertEqual(LakehouseBatchProcessorApp.version, "0.1.0")

    def test_run_with_no_iceberg_table_name_returns_zero(self):
        """Trigger payload missing iceberg_table_name → clean no-op."""
        app = LakehouseBatchProcessorApp()
        with patch("app.application.workflow", _mock_workflow_module()):
            with (
                patch.object(app, "handle_events", new=AsyncMock()) as handle,
                patch.object(app, "write_ack", new=AsyncMock()) as write,
            ):
                result = _run(app.run(IngestionInput()))
                self.assertEqual(result.processed, 0)
                handle.assert_not_called()
                write.assert_not_called()

    def test_run_with_empty_events_skips_ack(self):
        app = LakehouseBatchProcessorApp()
        with patch("app.application.workflow", _mock_workflow_module()):
            with (
                patch.object(
                    app,
                    "handle_events",
                    new=AsyncMock(
                        return_value=HandleEventsOutput(events=[], results=[])
                    ),
                ),
                patch.object(app, "write_ack", new=AsyncMock()) as write,
            ):
                result = _run(
                    app.run(IngestionInput(iceberg_table_name="events_table"))
                )
                self.assertEqual(result.processed, 0)
                write.assert_not_called()

    def test_run_with_events_aggregates_counts(self):
        app = LakehouseBatchProcessorApp()
        events = [
            {"event_id": "e1", "payload": "p1"},
            {"event_id": "e2", "payload": "p2"},
            {"event_id": "e3", "payload": "p3"},
        ]
        results = [
            {"status": "SUCCESS", "error_message": None},
            {"status": "RETRY", "error_message": "x"},
            {"status": "FAILED", "error_message": "y"},
        ]
        with patch("app.application.workflow", _mock_workflow_module(run_id="run-99")):
            with (
                patch.object(
                    app,
                    "handle_events",
                    new=AsyncMock(
                        return_value=HandleEventsOutput(events=events, results=results)
                    ),
                ),
                patch.object(
                    app,
                    "write_ack",
                    new=AsyncMock(
                        return_value=WriteAckOutput(
                            ack_path="artifacts/.../events_ack.parquet",
                            rows_written=3,
                        )
                    ),
                ),
            ):
                result = _run(
                    app.run(IngestionInput(iceberg_table_name="reverse_sync_events"))
                )
                self.assertEqual(result.processed, 3)
                self.assertEqual(result.success, 1)
                self.assertEqual(result.retry, 1)
                self.assertEqual(result.failed, 1)
                self.assertIn("events_ack.parquet", result.ack_path)


if __name__ == "__main__":
    unittest.main()
