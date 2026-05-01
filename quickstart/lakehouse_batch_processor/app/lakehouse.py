"""SDK-shaped table schemas for the batch processor sample.

Schemas are declared via the SDK :class:`Schema` / :class:`Field` /
:class:`PartitionBy` dataclasses — no pyiceberg or pyarrow types appear
in this module. The SDK ``LakehouseWriter`` translates them internally
when creating tables and building Arrow batches.
"""

from __future__ import annotations

from application_sdk.lakehouse import Field, PartitionBy, Schema

EVENTS_SCHEMA = Schema(
    fields=[
        Field("event_id", "string", nullable=False),
        Field("payload", "string", nullable=True),
        Field("received_at", "timestamp", nullable=False),
    ]
)

RESULTS_SCHEMA = Schema(
    fields=[
        Field("event_id", "string", nullable=False),
        Field("status", "string", nullable=False),
        Field("api_status_code", "int", nullable=True),
        Field("error_message", "string", nullable=True),
        Field("processed_at", "timestamp", nullable=False),
    ],
    partition_by=PartitionBy("status"),
)
