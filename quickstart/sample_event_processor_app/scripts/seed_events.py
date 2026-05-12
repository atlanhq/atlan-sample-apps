"""Seed sample events into a local Iceberg events table for E2E testing.

Without a real AE running, you can populate
``apps.automation-engine.<table>`` directly to exercise the
event-processing sample end-to-end. Each row gets
``status = 'unprocessed'`` so an ``events_read`` call with
``where="status = 'unprocessed'"`` picks them up.

Rows are written with AE CloudEvent column names (``id``, ``data``,
``received_at``, ``status``) — the same shape the sample reads in
production.

Usage::

    ICEBERG_CATALOG_URI=http://localhost:8181/api/catalog \\
    ICEBERG_CLIENT_ID=<id> \\
    ICEBERG_CLIENT_SECRET=<secret> \\
    uv run python scripts/seed_events.py --count 25
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Make the app/ package importable when run as a script.
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.lakehouse import EVENTS_SCHEMA  # noqa: E402
from application_sdk.lakehouse import LakehouseWriter  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed sample events.")
    parser.add_argument(
        "--namespace",
        default="apps.automation-engine",
        help="Namespace where AE writes events (default: apps.automation-engine)",
    )
    parser.add_argument(
        "--table",
        default="lakehouse_batch_events",
        help="Events table name",
    )
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()

    # In production the events table is owned by AE; for local seeding the
    # SDK writer logs a cross-namespace warning, which is expected here.
    writer = LakehouseWriter.from_env(app_namespace=args.namespace)
    now = datetime.now(UTC).replace(tzinfo=None)
    records = [
        {
            "id": str(uuid.uuid4()),
            "data": f"hello world #{i + 1}",
            "received_at": now,
            "status": "unprocessed",
        }
        for i in range(args.count)
    ]
    rows = writer.append(args.table, records, schema=EVENTS_SCHEMA)
    print(f"Seeded {rows} events into {args.namespace}.{args.table}")


if __name__ == "__main__":
    main()
