"""Seed sample events into the Iceberg events table.

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

import pyarrow as pa  # noqa: E402

from app.lakehouse import (  # noqa: E402
    EVENTS_ARROW_SCHEMA,
    EVENTS_SCHEMA,
    load_catalog_from_env,
)


def _ensure_table(catalog, namespace: str, table: str):
    table_id = f"{namespace}.{table}"
    try:
        return catalog.load_table(table_id)
    except Exception:
        try:
            catalog.create_namespace(namespace)
        except Exception:
            pass
        return catalog.create_table(identifier=table_id, schema=EVENTS_SCHEMA)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed sample events.")
    parser.add_argument("--namespace", default="samples")
    parser.add_argument("--table", default="lakehouse_batch_events")
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()

    catalog = load_catalog_from_env()
    table = _ensure_table(catalog, args.namespace, args.table)

    now = datetime.now(UTC).replace(tzinfo=None)
    rows = [
        {
            "event_id": str(uuid.uuid4()),
            "payload": f"hello world #{i + 1}",
            "received_at": now,
        }
        for i in range(args.count)
    ]
    arrow = pa.Table.from_pylist(rows, schema=EVENTS_ARROW_SCHEMA)
    table.append(arrow)
    print(f"Seeded {args.count} events into {args.namespace}.{args.table}")


if __name__ == "__main__":
    main()
