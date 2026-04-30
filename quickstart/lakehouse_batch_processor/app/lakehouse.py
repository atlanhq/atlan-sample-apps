"""Lakehouse helpers for the batch processor sample.

Uses ``application_sdk.lakehouse`` for all reads/writes — this module only
owns the sample's table schemas. Reader / writer are constructed lazily via
``LakehouseReader.from_env`` / ``LakehouseWriter.from_env`` from the standard
``ICEBERG_*`` environment variables, so the sample app holds no catalog code.
"""

from __future__ import annotations

import pyarrow as pa
from pyiceberg.partitioning import PartitionField, PartitionSpec
from pyiceberg.schema import Schema
from pyiceberg.transforms import IdentityTransform
from pyiceberg.types import IntegerType, NestedField, StringType, TimestampType

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


RESULTS_SCHEMA = Schema(
    NestedField(1, "event_id", StringType(), required=True),
    NestedField(2, "status", StringType(), required=True),
    NestedField(3, "api_status_code", IntegerType(), required=False),
    NestedField(4, "error_message", StringType(), required=False),
    NestedField(5, "processed_at", TimestampType(), required=True),
)

RESULTS_ARROW_SCHEMA = pa.schema(
    [
        pa.field("event_id", pa.string(), nullable=False),
        pa.field("status", pa.string(), nullable=False),
        pa.field("api_status_code", pa.int32(), nullable=True),
        pa.field("error_message", pa.string(), nullable=True),
        pa.field("processed_at", pa.timestamp("us"), nullable=False),
    ]
)


def results_partition_spec() -> PartitionSpec:
    field_id = RESULTS_SCHEMA.find_field("status").field_id
    return PartitionSpec(
        PartitionField(
            source_id=field_id,
            field_id=1000,
            transform=IdentityTransform(),
            name="status",
        )
    )
