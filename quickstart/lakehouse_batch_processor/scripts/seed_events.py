"""Seed sample events into the Iceberg events table via the SDK lakehouse writer.

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

# Make the app/ package importable when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.lakehouse import EVENTS_SCHEMA  # noqa: E402
from application_sdk.lakehouse import LakehouseWriter  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed sample events.")
    parser.add_argument("--namespace", default="samples")
    parser.add_argument("--table", default="lakehouse_batch_events")
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()

    writer = LakehouseWriter.from_env(app_namespace=args.namespace)

    now = datetime.now(UTC).replace(tzinfo=None)
    records = [
        {
            "event_id": str(uuid.uuid4()),
            "payload": f"hello world #{i + 1}",
            "received_at": now,
        }
        for i in range(args.count)
    ]
    rows = writer.append(
        args.table,
        records,
        schema=EVENTS_SCHEMA,
        namespace=args.namespace,
    )
    print(f"Seeded {rows} events into {args.namespace}.{args.table}")


if __name__ == "__main__":
    main()
