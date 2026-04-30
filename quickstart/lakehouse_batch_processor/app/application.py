"""LakehouseBatchProcessor — v3 SDK sample app.

Demo pipeline (does nothing useful — just demonstrates the v3 SDK pattern
on top of ``application_sdk.lakehouse``):

  1. Read events from an Iceberg table via ``LakehouseReader.from_env``.
  2. POST each event to a public hello-world API (httpbin.org/anything).
  3. Randomly classify the result as SUCCESS / RETRY / FAILED.
  4. Write results to an Iceberg results table via
     ``LakehouseWriter.from_env(app_namespace)`` (auto-creates and
     partitions by status; cross-namespace writes log a warning).
"""

from __future__ import annotations

from typing import Any

from application_sdk.app import App
from application_sdk.app.task import task
from application_sdk.contracts.base import Input, Output

# ---------------------------------------------------------------------------
# Workflow-level Input / Output
# ---------------------------------------------------------------------------


class BatchProcessorInput(Input):
    events_namespace: str = "samples"
    events_table: str = "lakehouse_batch_events"
    results_namespace: str = "samples"
    results_table: str = "lakehouse_batch_results"
    fetch_limit: int = 100


class BatchProcessorOutput(Output):
    processed: int = 0
    success: int = 0
    retry: int = 0
    failed: int = 0
    results_table: str = ""


# ---------------------------------------------------------------------------
# Task-level Input / Output (one pair per @task)
# ---------------------------------------------------------------------------


class FetchEventsInput(Input):
    events_namespace: str = ""
    events_table: str = ""
    fetch_limit: int = 100


class FetchEventsOutput(Output, allow_unbounded_fields=True):
    events: list[Any] = []


class ProcessEventsInput(Input, allow_unbounded_fields=True):
    events: list[Any] = []


class ProcessEventsOutput(Output, allow_unbounded_fields=True):
    results: list[Any] = []


class WriteResultsInput(Input, allow_unbounded_fields=True):
    results_namespace: str = ""
    results_table: str = ""
    results: list[Any] = []


class WriteResultsOutput(Output):
    rows_written: int = 0


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


class LakehouseBatchProcessorApp(App):
    """Sample app: lakehouse → API → random result → lakehouse."""

    name = "lakehouse-batch-processor"
    version = "0.1.0"
    description = (
        "Demo app that reads events from an Iceberg lakehouse via the SDK "
        "LakehouseReader / LakehouseWriter, calls a public hello-world API, "
        "and writes randomly-classified batch results back."
    )

    # --- Tasks (I/O work happens here) ---

    @task(timeout_seconds=120)
    async def fetch_events(self, input: FetchEventsInput) -> FetchEventsOutput:
        from application_sdk.lakehouse import LakehouseReader

        reader = LakehouseReader.from_env()
        records = reader.fetch_records(
            input.events_namespace,
            input.events_table,
            limit=input.fetch_limit,
        )
        events = [
            {"event_id": r["event_id"], "payload": r.get("payload") or ""}
            for r in records
        ]
        return FetchEventsOutput(events=events)

    @task(timeout_seconds=600, heartbeat_timeout_seconds=60)
    async def process_events(self, input: ProcessEventsInput) -> ProcessEventsOutput:
        from app.api_client import HelloApiCaller
        from app.models import RandomClassifier

        caller = HelloApiCaller()
        classifier = RandomClassifier()
        results = []
        for raw in input.events:
            event_id = raw["event_id"]
            payload = raw.get("payload", "")
            try:
                status_code = await caller.call(event_id, payload)
            except Exception as exc:
                results.append(
                    {
                        "event_id": event_id,
                        "status": "FAILED",
                        "api_status_code": None,
                        "error_message": f"api error: {exc}",
                    }
                )
                continue

            result = classifier.classify(event_id, status_code)
            results.append(
                {
                    "event_id": result.event_id,
                    "status": result.status,
                    "api_status_code": result.api_status_code,
                    "error_message": result.error_message,
                }
            )
        return ProcessEventsOutput(results=results)

    @task(timeout_seconds=120)
    async def write_results(self, input: WriteResultsInput) -> WriteResultsOutput:
        from datetime import UTC, datetime

        from app.lakehouse import (
            RESULTS_ARROW_SCHEMA,
            RESULTS_SCHEMA,
            results_partition_spec,
        )
        from application_sdk.lakehouse import LakehouseWriter

        if not input.results:
            return WriteResultsOutput(rows_written=0)

        writer = LakehouseWriter.from_env(app_namespace=input.results_namespace)
        now = datetime.now(UTC).replace(tzinfo=None)
        records = [
            {
                "event_id": r["event_id"],
                "status": r["status"],
                "api_status_code": r.get("api_status_code"),
                "error_message": r.get("error_message"),
                "processed_at": now,
            }
            for r in input.results
        ]
        rows = writer.write_records(
            input.results_table,
            records,
            schema=RESULTS_SCHEMA,
            partition_spec=results_partition_spec(),
            arrow_schema=RESULTS_ARROW_SCHEMA,
            namespace=input.results_namespace,
        )
        return WriteResultsOutput(rows_written=rows)

    # --- Orchestration (deterministic — only call tasks) ---

    async def run(self, input: BatchProcessorInput) -> BatchProcessorOutput:
        fetch_result = await self.fetch_events(
            FetchEventsInput(
                events_namespace=input.events_namespace,
                events_table=input.events_table,
                fetch_limit=input.fetch_limit,
            )
        )
        events = fetch_result.events
        results_table_qn = f"{input.results_namespace}.{input.results_table}"
        if not events:
            return BatchProcessorOutput(results_table=results_table_qn)

        process_result = await self.process_events(ProcessEventsInput(events=events))
        results = process_result.results

        await self.write_results(
            WriteResultsInput(
                results_namespace=input.results_namespace,
                results_table=input.results_table,
                results=results,
            )
        )

        success = sum(1 for r in results if r.get("status") == "SUCCESS")
        retry = sum(1 for r in results if r.get("status") == "RETRY")
        failed = sum(1 for r in results if r.get("status") == "FAILED")
        return BatchProcessorOutput(
            processed=len(events),
            success=success,
            retry=retry,
            failed=failed,
            results_table=results_table_qn,
        )
