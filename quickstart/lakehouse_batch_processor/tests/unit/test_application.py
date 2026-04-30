"""Smoke tests for the App: tasks exist + run() orchestration on stubs."""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.application import BatchProcessorInput, LakehouseBatchProcessorApp


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


class TestApp(unittest.TestCase):
    def test_app_metadata(self):
        self.assertEqual(LakehouseBatchProcessorApp.name, "lakehouse-batch-processor")
        self.assertEqual(LakehouseBatchProcessorApp.version, "0.1.0")

    def test_run_with_no_events_returns_zero(self):
        app = LakehouseBatchProcessorApp()
        # Patch tasks to bypass real Iceberg / API access.
        with (
            patch.object(
                app, "fetch_events", new=AsyncMock(return_value=_StubFetch(events=[]))
            ),
            patch.object(app, "process_events", new=AsyncMock()) as proc,
            patch.object(app, "write_results", new=AsyncMock()) as write,
        ):
            result = _run(app.run(BatchProcessorInput()))
            self.assertEqual(result.processed, 0)
            self.assertEqual(result.success, 0)
            self.assertEqual(result.retry, 0)
            self.assertEqual(result.failed, 0)
            proc.assert_not_called()
            write.assert_not_called()

    def test_run_with_events_aggregates_counts(self):
        app = LakehouseBatchProcessorApp()
        events = [
            {"event_id": "e1", "payload": "p1"},
            {"event_id": "e2", "payload": "p2"},
            {"event_id": "e3", "payload": "p3"},
        ]
        results = [
            {
                "event_id": "e1",
                "status": "SUCCESS",
                "api_status_code": 200,
                "error_message": None,
            },
            {
                "event_id": "e2",
                "status": "RETRY",
                "api_status_code": 200,
                "error_message": "x",
            },
            {
                "event_id": "e3",
                "status": "FAILED",
                "api_status_code": 200,
                "error_message": "y",
            },
        ]
        with (
            patch.object(
                app,
                "fetch_events",
                new=AsyncMock(return_value=_StubFetch(events=events)),
            ),
            patch.object(
                app,
                "process_events",
                new=AsyncMock(return_value=_StubProcess(results=results)),
            ),
            patch.object(
                app,
                "write_results",
                new=AsyncMock(return_value=_StubWrite(rows_written=3)),
            ),
        ):
            result = _run(app.run(BatchProcessorInput()))
            self.assertEqual(result.processed, 3)
            self.assertEqual(result.success, 1)
            self.assertEqual(result.retry, 1)
            self.assertEqual(result.failed, 1)
            self.assertIn("samples.lakehouse_batch_results", result.results_table)


class _StubFetch:
    def __init__(self, events):
        self.events = events


class _StubProcess:
    def __init__(self, results):
        self.results = results


class _StubWrite:
    def __init__(self, rows_written):
        self.rows_written = rows_written


if __name__ == "__main__":
    unittest.main()
