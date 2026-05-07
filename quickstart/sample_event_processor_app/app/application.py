"""SampleEventProcessorApp — AE-triggered ingestion sample.

The flow this app demonstrates::

    event-ingestion-app  ─►  AE event-consumer-node  ─►  this workflow

When AE detects a batch of unprocessed rows in its events table, it
triggers this workflow with the events table name. A single
``handle_events`` activity:

  1. Reads pending events from ``automation_engine.<events_table>`` via
     :func:`application_sdk.lakehouse.events_read`, which loops
     internally in batches of 1000 (capped at 5000 total).
  2. Dispatches each batch to a ``handler`` that POSTs each event to a
     hello-world HTTP API and randomly classifies the result as
     ``SUCCESS`` / ``RETRY`` / ``FAILED``.
  3. Publishes a Parquet ack at
     ``artifacts/sample-event-processor-app/ingestion/<yyyy>/<mm>/<dd>/<run_id>/events_ack.parquet``
     via :func:`application_sdk.lakehouse.events_ack` so AE can mark
     events as acknowledged.

Inputs match the AE event-consumer trigger payload — the workflow does
not expose a UI form. ``events_read`` is the only lakehouse touchpoint;
it talks to PyIceberg internally and the lakehouse stays a blackbox to
this sample.
"""

from __future__ import annotations

import logging
from typing import Any

from application_sdk.app import App
from application_sdk.app.task import task
from application_sdk.contracts.base import Input, Output
from temporalio import activity, workflow

logger = logging.getLogger(__name__)

# Default AE namespace where the event-ingestion-app writes events.
_DEFAULT_EVENTS_NAMESPACE = "automation_engine"

_APP_NAME = "sample-event-processor-app"
_WORKFLOW_NAME = "ingestion"

# events_read batching: pull up to _BATCH_SIZE per fetch, stop after
# _MAX_EVENTS total. Bounds activity run time and keeps each handler
# call within heartbeat / memory limits.
_BATCH_SIZE = 1000
_MAX_EVENTS = 5000


# ---------------------------------------------------------------------------
# Workflow Input / Output (matches AE event-consumer trigger payload)
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
# App
# ---------------------------------------------------------------------------


class SampleEventProcessorApp(App):
    """AE-triggered ingestion sample app on top of the SDK lakehouse module."""

    name = _APP_NAME
    version = "0.1.0"
    description = (
        "Sample app demonstrating AE event-driven ingestion via the SDK "
        "events_read function. Reads events from an AE-vended Iceberg "
        "table in batches, POSTs each to a hello-world API, randomly "
        "classifies, and writes the Parquet ack AE expects."
    )

    @task(timeout_seconds=1800, heartbeat_timeout_seconds=60)
    async def handle_events(self, input: IngestionInput) -> IngestionOutput:
        """Read pending events in batches and publish the AE ack.

        ``events_read`` loops internally — each iteration fetches up to
        ``_BATCH_SIZE`` events and dispatches them to ``_handler``. The
        loop exits when the source is exhausted or ``_MAX_EVENTS`` total
        events have been processed. Then ``events_ack`` writes a single
        Parquet ack covering every event processed.
        """
        from app.api_client import HelloApiCaller
        from app.models import RandomClassifier
        from application_sdk.lakehouse import EventResult, events_ack, events_read

        caller = HelloApiCaller()
        classifier = RandomClassifier()

        async def _handler(events: list[dict[str, Any]]) -> list[EventResult]:
            """Per-event: POST to hello API; random classify the result."""
            out: list[EventResult] = []
            for raw in events:
                event_id = raw["event_id"]
                payload = raw.get("payload", "") or ""
                try:
                    status_code = await caller.call(event_id, payload)
                except Exception as exc:
                    out.append(
                        EventResult(status="FAILED", error_message=f"api error: {exc}")
                    )
                    continue
                result = classifier.classify(event_id, status_code)
                out.append(
                    EventResult(
                        status=result.status,  # type: ignore[arg-type]
                        error_message=result.error_message,
                    )
                )
            return out

        events, results = await events_read(
            namespace=input.events_namespace,
            table=input.iceberg_table_name,
            handler=_handler,
            where="status = 'unprocessed'",
            sort_by="received_at",
            batch_size=_BATCH_SIZE,
            max_events=_MAX_EVENTS,
        )
        if not events:
            logger.info("No events to process — clean exit")
            return IngestionOutput()

        ack_path = await events_ack(
            events,
            results,
            app_name=_APP_NAME,
            workflow_name=_WORKFLOW_NAME,
            workflow_run_id=activity.info().workflow_run_id,
        )

        success = sum(1 for r in results if r.status == "SUCCESS")
        retry = sum(1 for r in results if r.status == "RETRY")
        failed = sum(1 for r in results if r.status == "FAILED")
        return IngestionOutput(
            processed=len(events),
            success=success,
            retry=retry,
            failed=failed,
            ack_path=ack_path,
        )

    async def run(self, input: IngestionInput) -> IngestionOutput:
        if not input.iceberg_table_name:
            workflow.logger.error("No iceberg_table_name provided in trigger payload")
            return IngestionOutput()
        return await self.handle_events(input)
