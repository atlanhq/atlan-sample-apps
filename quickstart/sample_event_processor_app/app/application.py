"""SampleEventProcessorApp — AE-triggered ingestion sample.

The flow this app demonstrates::

    event-ingestion-app  ─►  AE event-consumer-node  ─►  this workflow

When AE detects a batch of unprocessed rows in its events table, it
triggers this workflow with the events table name. The workflow:

  1. Reads pending events from ``automation_engine.<events_table>`` via
     :class:`application_sdk.lakehouse.EventsConsumer`.
  2. Dispatches them to a ``process_fn`` that POSTs each event to a
     hello-world HTTP API and randomly classifies the result as
     ``SUCCESS`` / ``RETRY`` / ``FAILED``.
  3. Publishes a Parquet ack at
     ``artifacts/sample-event-processor-app/ingestion/<yyyy>/<mm>/<dd>/<run_id>/events_ack.parquet``
     via :class:`application_sdk.lakehouse.EventAckWriter` so AE can mark
     events as acknowledged.

Inputs match the AE event-consumer trigger payload — the workflow does
not expose a UI form. EventsConsumer is the only lakehouse touchpoint;
it talks to PyIceberg internally and the lakehouse stays a blackbox to
this sample.
"""

from __future__ import annotations

import logging
from typing import Any

from application_sdk.app import App
from application_sdk.app.task import task
from application_sdk.contracts.base import Input, Output
from temporalio import workflow

logger = logging.getLogger(__name__)

# Default AE namespace where the event-ingestion-app writes events.
_DEFAULT_EVENTS_NAMESPACE = "automation_engine"

_APP_NAME = "sample-event-processor-app"
_WORKFLOW_NAME = "ingestion"


# ---------------------------------------------------------------------------
# Workflow-level Input / Output (matches AE event-consumer trigger payload)
# ---------------------------------------------------------------------------


class IngestionInput(Input):
    """Payload AE's event-consumer-node passes when triggering this workflow."""

    iceberg_table_name: str = ""
    events_namespace: str = _DEFAULT_EVENTS_NAMESPACE
    workflow_id: str = ""
    triggered_by: str = ""
    trigger_id: str = ""
    trigger_name: str = ""
    event_cleanup_max_retries: int = 5
    event_cleanup_ack_source: str = ""


class IngestionOutput(Output):
    processed: int = 0
    success: int = 0
    retry: int = 0
    failed: int = 0
    ack_path: str = ""


# ---------------------------------------------------------------------------
# Task-level Input / Output (one pair per @task)
# ---------------------------------------------------------------------------


class HandleEventsInput(Input):
    events_namespace: str = ""
    events_table: str = ""


class HandleEventsOutput(Output, allow_unbounded_fields=True):
    events: list[Any] = []
    results: list[Any] = []  # serialised ProcessingResult dicts


class WriteAckInput(Input, allow_unbounded_fields=True):
    events: list[Any] = []
    results: list[Any] = []
    workflow_run_id: str = ""


class WriteAckOutput(Output):
    ack_path: str = ""
    rows_written: int = 0


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


class SampleEventProcessorApp(App):
    """AE-triggered ingestion sample app on top of the SDK lakehouse module."""

    name = _APP_NAME
    version = "0.1.0"
    description = (
        "Sample app demonstrating AE event-driven ingestion via the SDK "
        "EventsConsumer. Reads events from an AE-vended Iceberg table, "
        "POSTs each to a hello-world API, randomly classifies, and writes "
        "the Parquet ack AE expects."
    )

    # --- Task: handle events via SDK EventsConsumer ---

    @task(timeout_seconds=600, heartbeat_timeout_seconds=60)
    async def handle_events(self, input: HandleEventsInput) -> HandleEventsOutput:
        from app.api_client import HelloApiCaller
        from app.models import RandomClassifier
        from application_sdk.lakehouse import EventsConsumer, ProcessingResult

        caller = HelloApiCaller()
        classifier = RandomClassifier()

        async def _process(events: list[dict[str, Any]]) -> list[ProcessingResult]:
            """Per-event: POST to hello API; random classify the result."""
            out: list[ProcessingResult] = []
            for raw in events:
                event_id = raw["event_id"]
                payload = raw.get("payload", "") or ""
                try:
                    status_code = await caller.call(event_id, payload)
                except Exception as exc:
                    out.append(
                        ProcessingResult(
                            status="FAILED", error_message=f"api error: {exc}"
                        )
                    )
                    continue
                result = classifier.classify(event_id, status_code)
                out.append(
                    ProcessingResult(
                        status=result.status,  # type: ignore[arg-type]
                        error_message=result.error_message,
                    )
                )
            return out

        consumer = EventsConsumer(_process)
        events, results = await consumer.handle_events(
            input.events_namespace,
            input.events_table,
        )
        # Serialise ProcessingResult to a plain dict so the Temporal payload
        # stays JSON-serialisable and the workflow keeps deterministic types.
        result_dicts = [
            {"status": r.status, "error_message": r.error_message} for r in results
        ]
        return HandleEventsOutput(events=events, results=result_dicts)

    # --- Task: publish AE ack via SDK EventAckWriter ---

    @task(timeout_seconds=120)
    async def write_ack(self, input: WriteAckInput) -> WriteAckOutput:
        from application_sdk.lakehouse import EventAckWriter, ProcessingResult

        if not input.events:
            return WriteAckOutput()

        ack = EventAckWriter(app_name=_APP_NAME, workflow_name=_WORKFLOW_NAME)
        results = [
            ProcessingResult(
                status=r["status"],  # type: ignore[arg-type]
                error_message=r.get("error_message"),
            )
            for r in input.results
        ]
        ack_path = await ack.write(input.events, results, input.workflow_run_id)
        return WriteAckOutput(ack_path=ack_path, rows_written=len(input.events))

    # --- Orchestration ---

    async def run(self, input: IngestionInput) -> IngestionOutput:
        if not input.iceberg_table_name:
            workflow.logger.error("No iceberg_table_name provided in trigger payload")
            return IngestionOutput()

        run_id = workflow.info().run_id

        handled = await self.handle_events(
            HandleEventsInput(
                events_namespace=input.events_namespace,
                events_table=input.iceberg_table_name,
            )
        )
        events = handled.events
        results = handled.results
        if not events:
            workflow.logger.info("No events to process — clean exit")
            return IngestionOutput()
        _ = logger  # keep module logger reachable for non-workflow contexts

        ack_result = await self.write_ack(
            WriteAckInput(events=events, results=results, workflow_run_id=run_id)
        )

        success = sum(1 for r in results if r.get("status") == "SUCCESS")
        retry = sum(1 for r in results if r.get("status") == "RETRY")
        failed = sum(1 for r in results if r.get("status") == "FAILED")
        return IngestionOutput(
            processed=len(events),
            success=success,
            retry=retry,
            failed=failed,
            ack_path=ack_result.ack_path,
        )
