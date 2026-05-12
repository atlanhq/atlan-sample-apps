"""Local end-to-end run for SampleEventProcessorApp without Polaris.

Drives the workflow against a real local Temporal dev server. The lakehouse
+ object store are stubbed with in-memory / local-disk fakes so the run
exercises the full Temporal workflow path without needing a Polaris
catalog or Dapr-backed object store.

Prereqs:
    temporal server start-dev --db-filename ./temporal.db   # already running

What it does:
    1. Monkey-patches LakehouseReader.from_env to serve seeded events
    2. Monkey-patches upload_file_from_bytes to write to ./local/tmp/
    3. Starts a Temporal worker for SampleEventProcessorApp
    4. Triggers the workflow with an AE-shaped payload
    5. Prints workflow output + inspects the parquet ack
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Pin the application name BEFORE importing the SDK; constants are read at
# import time.
os.environ.setdefault("ATLAN_APPLICATION_NAME", "sample-event-processor-app")
os.environ.setdefault("ATLAN_LOCAL_DEVELOPMENT", "true")
os.environ.setdefault("ATLAN_TEMPORAL_HOST", "localhost:7233")
# events_read / events_ack don't need real Polaris — but the SDK reads
# ICEBERG_* during from_env(); we patch that out, but set placeholders
# so anything that reads them at import doesn't bail.
os.environ.setdefault("ICEBERG_CATALOG_URI", "http://stub.invalid")
os.environ.setdefault("ICEBERG_CLIENT_ID", "stub")
os.environ.setdefault("ICEBERG_CLIENT_SECRET", "stub")
os.environ.setdefault("ICEBERG_WAREHOUSE", "context_store")

LOCAL_DIR = Path(__file__).parent / "local" / "tmp"
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s: %(message)s",
)
logger = logging.getLogger("local_run")

# ---------------------------------------------------------------------------
# Seed events that "live" in the fake lakehouse table
# ---------------------------------------------------------------------------

NOW = datetime.now(timezone.utc).replace(tzinfo=None)
# Seed with AE CloudEvent column names (id, data, ...) so the local
# flow exercises the same column shape the app will see against real AE.
SEEDED_EVENTS: list[dict[str, Any]] = [
    {
        "id": f"evt-{i:03d}",
        "data": f"hello world #{i}",
        "received_at": NOW,
        "status": "unprocessed",
    }
    for i in range(12)
]


class _FakeReader:
    """Drop-in stand-in for LakehouseReader. Pops events off as they're read."""

    def __init__(self, events: list[dict[str, Any]]) -> None:
        self._remaining = list(events)
        self.fetch_call_count = 0

    def fetch_records(
        self,
        namespace: str,
        table: str,
        *,
        where: str | None = None,
        sort_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        self.fetch_call_count += 1
        n = limit if limit is not None else len(self._remaining)
        batch = self._remaining[:n]
        self._remaining = self._remaining[n:]
        logger.info(
            "FakeReader.fetch_records(%s.%s, where=%r, sort=%r, limit=%s) "
            "→ %d events (call #%d, %d still queued)",
            namespace,
            table,
            where,
            sort_by,
            limit,
            len(batch),
            self.fetch_call_count,
            len(self._remaining),
        )
        return batch


_FAKE_READER = _FakeReader(SEEDED_EVENTS)


# ---------------------------------------------------------------------------
# Apply patches BEFORE importing the App / SDK lakehouse modules
# ---------------------------------------------------------------------------

from unittest.mock import patch  # noqa: E402

# Force-import the lakehouse package so events_read / events_ack modules
# are loaded and their bindings exist before we patch them.
import application_sdk.lakehouse  # noqa: E402, F401


async def _fake_upload(*, key: str, content: bytes) -> str:
    """Write the parquet ack to the local filesystem instead of an object store."""
    target = LOCAL_DIR / key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    logger.info("FakeUpload wrote %d bytes → %s", len(content), target)
    return str(target)


# Patch the LakehouseReader.from_env classmethod everywhere — events_read.py
# does `LakehouseReader.from_env()` and the class object is shared, so this
# affects every caller.
patch(
    "application_sdk.lakehouse.reader.LakehouseReader.from_env",
    new=staticmethod(lambda: _FAKE_READER),
).start()

# Patch the upload symbol bound inside events_ack (which did
# `from application_sdk.storage.batch import upload_file_from_bytes`).
patch(
    "application_sdk.lakehouse.events_ack.upload_file_from_bytes",
    new=_fake_upload,
).start()

# ---------------------------------------------------------------------------
# Now import the App + Temporal plumbing
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).parent))

from app.application import ProcessEventsInput, SampleEventProcessorApp  # noqa: E402
from application_sdk.execution._temporal.backend import (  # noqa: E402
    create_temporal_client,
)
from application_sdk.execution._temporal.worker import create_worker  # noqa: E402

_TASK_QUEUE = "sample-event-processor-app-queue"
_WORKFLOW_TYPE = "sample-event-processor-app"  # implicit entry point: run()


async def main() -> None:
    # Touch the App class so SDK auto-registration happens.
    _ = SampleEventProcessorApp

    client = await create_temporal_client(
        host="localhost:7233",
        namespace="default",
        enable_prometheus=False,
    )
    logger.info("Connected to Temporal")

    worker = create_worker(
        client,
        task_queue=_TASK_QUEUE,
        handler=None,
        enable_sdr=False,
        enable_pushgateway=False,
    )

    workflow_id = f"local-run-{int(datetime.now().timestamp())}"
    payload = ProcessEventsInput(
        iceberg_table_name="lakehouse_batch_events",
        events_namespace="apps.automation-engine",
        workflow_id=workflow_id,
        triggered_by="local_run.py",
        trigger_id="local-trigger",
        trigger_name="local-test",
    )

    async with worker:
        logger.info("Worker started; submitting workflow %s", workflow_id)
        handle = await client.start_workflow(
            _WORKFLOW_TYPE,
            payload,
            id=workflow_id,
            task_queue=_TASK_QUEUE,
        )
        logger.info(
            "Workflow submitted (run_id=%s); awaiting result …",
            handle.first_execution_run_id,
        )
        result = await handle.result()
        logger.info("Workflow completed")

    # ---- Inspect ----
    print("\n" + "=" * 70)
    print(f"WORKFLOW OUTPUT: {workflow_id}")
    print("=" * 70)

    # Temporal data-converter returns a plain dict; use mapping access.
    def _get(field: str, default: Any = 0) -> Any:
        if isinstance(result, dict):
            return result.get(field, default)
        return getattr(result, field, default)

    print(f"  processed = {_get('processed')}")
    print(f"  success   = {_get('success')}")
    print(f"  retry     = {_get('retry')}")
    print(f"  failed    = {_get('failed')}")
    ack_path = _get("ack_path", "")
    print(f"  ack_path  = {ack_path}")
    print(f"  reader fetch calls = {_FAKE_READER.fetch_call_count}")
    print(f"  events still queued in fake reader = {len(_FAKE_READER._remaining)}")

    # Inspect the parquet ack we wrote (events_ack returns the relative
    # object-store key — our fake upload writes it under LOCAL_DIR).
    ack_local = LOCAL_DIR / ack_path if ack_path else LOCAL_DIR
    if ack_local.exists() and ack_local.is_file():
        import pyarrow.parquet as pq  # noqa: PLC0415

        table = pq.read_table(io.BytesIO(ack_local.read_bytes()))
        print("\nACK PARQUET CONTENTS:")
        print(f"  schema: {table.schema}")
        print(f"  rows:   {table.num_rows}")
        print("  preview (first 5):")
        for row in table.to_pylist()[:5]:
            print(f"    {row}")
    else:
        print(f"\n!! ack file not found at {ack_local}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
