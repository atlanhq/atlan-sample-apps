"""LakehouseBatchProcessor — v3 SDK sample app.

Demo pipeline (does nothing useful — just demonstrates the v3 SDK pattern):

  1. Read events from an Iceberg table.
  2. POST each event to a public hello-world API (httpbin.org/anything).
  3. Randomly classify the outcome as SUCCESS / RETRY / FAILED.
  4. Write outcomes to an Iceberg results table partitioned by status.

Modeled after the reverse-sync description workflow in the Databricks
connector, but trimmed down for sample/learning use.
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
    outcomes_namespace: str = "samples"
    outcomes_table: str = "lakehouse_batch_outcomes"
    fetch_limit: int = 100


class BatchProcessorOutput(Output):
    processed: int = 0
    success: int = 0
    retry: int = 0
    failed: int = 0
    outcomes_table: str = ""


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
    outcomes: list[Any] = []


class WriteOutcomesInput(Input, allow_unbounded_fields=True):
    outcomes_namespace: str = ""
    outcomes_table: str = ""
    outcomes: list[Any] = []


class WriteOutcomesOutput(Output):
    rows_written: int = 0


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


class LakehouseBatchProcessorApp(App):
    """Sample app: lakehouse → API → random outcome → lakehouse."""

    name = "lakehouse-batch-processor"
    version = "0.1.0"
    description = (
        "Demo app that reads events from an Iceberg lakehouse, calls a public "
        "hello-world API, and writes randomly-classified batch outcomes back."
    )

    # --- Tasks (I/O work happens here) ---

    @task(timeout_seconds=120)
    async def fetch_events(self, input: FetchEventsInput) -> FetchEventsOutput:
        from app.lakehouse import IcebergReader, load_catalog_from_env

        reader = IcebergReader(load_catalog_from_env())
        events = reader.read_events(
            input.events_namespace, input.events_table, input.fetch_limit
        )
        return FetchEventsOutput(events=[_event_to_dict(e) for e in events])

    @task(timeout_seconds=600, heartbeat_timeout_seconds=60)
    async def process_events(self, input: ProcessEventsInput) -> ProcessEventsOutput:
        from app.api_client import HelloApiCaller
        from app.models import RandomClassifier

        caller = HelloApiCaller()
        classifier = RandomClassifier()
        outcomes = []
        for raw in input.events:
            event_id = raw["event_id"]
            payload = raw.get("payload", "")
            try:
                status_code = await caller.call(event_id, payload)
            except Exception as exc:
                outcomes.append(
                    {
                        "event_id": event_id,
                        "status": "FAILED",
                        "api_status_code": None,
                        "error_message": f"api error: {exc}",
                    }
                )
                continue

            outcome = classifier.classify(event_id, status_code)
            outcomes.append(
                {
                    "event_id": outcome.event_id,
                    "status": outcome.status,
                    "api_status_code": outcome.api_status_code,
                    "error_message": outcome.error_message,
                }
            )
        return ProcessEventsOutput(outcomes=outcomes)

    @task(timeout_seconds=120)
    async def write_outcomes(self, input: WriteOutcomesInput) -> WriteOutcomesOutput:
        from app.lakehouse import IcebergWriter, load_catalog_from_env
        from app.models import OutcomeRecord

        writer = IcebergWriter(load_catalog_from_env())
        records = [
            OutcomeRecord(
                event_id=o["event_id"],
                status=o["status"],
                api_status_code=o.get("api_status_code"),
                error_message=o.get("error_message"),
            )
            for o in input.outcomes
        ]
        rows = writer.write_outcomes(
            input.outcomes_namespace, input.outcomes_table, records
        )
        return WriteOutcomesOutput(rows_written=rows)

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
        if not events:
            return BatchProcessorOutput(
                outcomes_table=f"{input.outcomes_namespace}.{input.outcomes_table}"
            )

        process_result = await self.process_events(ProcessEventsInput(events=events))
        outcomes = process_result.outcomes

        await self.write_outcomes(
            WriteOutcomesInput(
                outcomes_namespace=input.outcomes_namespace,
                outcomes_table=input.outcomes_table,
                outcomes=outcomes,
            )
        )

        success = sum(1 for o in outcomes if o.get("status") == "SUCCESS")
        retry = sum(1 for o in outcomes if o.get("status") == "RETRY")
        failed = sum(1 for o in outcomes if o.get("status") == "FAILED")
        return BatchProcessorOutput(
            processed=len(events),
            success=success,
            retry=retry,
            failed=failed,
            outcomes_table=f"{input.outcomes_namespace}.{input.outcomes_table}",
        )


def _event_to_dict(event: Any) -> dict[str, Any]:
    return {"event_id": event.event_id, "payload": event.payload}
