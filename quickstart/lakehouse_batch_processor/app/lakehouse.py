"""Iceberg read/write helpers for the batch processor sample."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pyarrow as pa
from pyiceberg.partitioning import PartitionField, PartitionSpec
from pyiceberg.schema import Schema
from pyiceberg.transforms import IdentityTransform
from pyiceberg.types import (
    IntegerType,
    NestedField,
    StringType,
    TimestampType,
)

from app.models import EventRecord, OutcomeRecord

if TYPE_CHECKING:
    from pyiceberg.catalog import Catalog


EVENTS_SCHEMA = Schema(
    NestedField(1, "event_id", StringType(), required=True),
    NestedField(2, "payload", StringType(), required=False),
    NestedField(3, "received_at", TimestampType(), required=True),
)

EVENTS_ARROW_SCHEMA = pa.schema(
    [
        pa.field("event_id", pa.string(), nullable=False),
        pa.field("payload", pa.string(), nullable=True),
        pa.field("received_at", pa.timestamp("us"), nullable=False),
    ]
)


OUTCOMES_SCHEMA = Schema(
    NestedField(1, "event_id", StringType(), required=True),
    NestedField(2, "status", StringType(), required=True),
    NestedField(3, "api_status_code", IntegerType(), required=False),
    NestedField(4, "error_message", StringType(), required=False),
    NestedField(5, "processed_at", TimestampType(), required=True),
)

OUTCOMES_ARROW_SCHEMA = pa.schema(
    [
        pa.field("event_id", pa.string(), nullable=False),
        pa.field("status", pa.string(), nullable=False),
        pa.field("api_status_code", pa.int32(), nullable=True),
        pa.field("error_message", pa.string(), nullable=True),
        pa.field("processed_at", pa.timestamp("us"), nullable=False),
    ]
)


def load_catalog_from_env() -> "Catalog":
    """Build a PyIceberg catalog from environment variables.

    Required env vars:
      - ICEBERG_CATALOG_URI
      - ICEBERG_CLIENT_ID
      - ICEBERG_CLIENT_SECRET

    Optional:
      - ICEBERG_WAREHOUSE (default: "context_store")
    """
    from pyiceberg.catalog import load_catalog

    uri = os.environ["ICEBERG_CATALOG_URI"]
    client_id = os.environ["ICEBERG_CLIENT_ID"]
    client_secret = os.environ["ICEBERG_CLIENT_SECRET"]
    warehouse = os.environ.get("ICEBERG_WAREHOUSE", "context_store")
    return load_catalog(
        warehouse,
        **{
            "type": "rest",
            "uri": uri,
            "warehouse": warehouse,
            "credential": f"{client_id}:{client_secret}",
            "scope": "PRINCIPAL_ROLE:ALL",
            "rest.sigv4-enabled": "false",
        },
    )


class IcebergReader:
    """Read events from the input Iceberg table."""

    def __init__(self, catalog: "Catalog") -> None:
        self._catalog = catalog

    def read_events(
        self, namespace: str, table: str, limit: int = 100
    ) -> list[EventRecord]:
        table_id = f"{namespace}.{table}"
        try:
            t = self._catalog.load_table(table_id)
        except Exception:
            return []

        arrow = t.scan(limit=limit).to_arrow()
        if arrow.num_rows == 0:
            return []
        return [
            EventRecord(
                event_id=arrow["event_id"][i].as_py(),
                payload=arrow["payload"][i].as_py() or "",
            )
            for i in range(arrow.num_rows)
        ]


class IcebergWriter:
    """Append outcome rows to the outcomes Iceberg table.

    Auto-creates the namespace + table if either is missing. Partitions on
    ``status`` so downstream consumers can scan SUCCESS/RETRY/FAILED cheaply.
    """

    def __init__(self, catalog: "Catalog") -> None:
        self._catalog = catalog

    def write_outcomes(
        self, namespace: str, table: str, outcomes: list[OutcomeRecord]
    ) -> int:
        if not outcomes:
            return 0

        table_id = f"{namespace}.{table}"
        try:
            t = self._catalog.load_table(table_id)
        except Exception:
            try:
                self._catalog.create_namespace(namespace)
            except Exception:
                pass
            t = self._catalog.create_table(
                identifier=table_id,
                schema=OUTCOMES_SCHEMA,
                partition_spec=_outcomes_partition_spec(),
            )

        now = datetime.now(UTC).replace(tzinfo=None)
        arrow = pa.table(
            {
                "event_id": [o.event_id for o in outcomes],
                "status": [o.status for o in outcomes],
                "api_status_code": [o.api_status_code for o in outcomes],
                "error_message": [o.error_message for o in outcomes],
                "processed_at": [now] * len(outcomes),
            },
            schema=OUTCOMES_ARROW_SCHEMA,
        )
        t.append(arrow)
        return arrow.num_rows


def _outcomes_partition_spec() -> PartitionSpec:
    field_id = OUTCOMES_SCHEMA.find_field("status").field_id
    return PartitionSpec(
        PartitionField(
            source_id=field_id,
            field_id=1000,
            transform=IdentityTransform(),
            name="status",
        )
    )
