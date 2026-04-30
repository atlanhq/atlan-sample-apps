"""Lakehouse helpers for the batch processor sample.

Uses ``application_sdk.lakehouse.LakehouseInterface`` for all reads/writes —
this module only owns the sample's table schemas and a small env-driven
catalog loader.
"""

from __future__ import annotations

import os

import pyarrow as pa
from application_sdk.lakehouse import LakehouseInterface
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


def load_catalog_from_env():
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


def load_lakehouse(app_namespace: str = "samples") -> LakehouseInterface:
    """Build a ``LakehouseInterface`` for this sample app.

    Reader can scan any namespace; writer is bound to ``app_namespace`` so
    cross-namespace writes log a warning (per SDK convention).
    """
    return LakehouseInterface(load_catalog_from_env(), app_namespace=app_namespace)
