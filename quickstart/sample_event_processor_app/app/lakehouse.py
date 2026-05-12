"""Schema declarations for the AE events table the sample reads from.

The sample only **reads** events (AE writes them via its event consumer);
it doesn't own a results table. The schema below is reference-only — used
by ``scripts/seed_events.py`` to populate a local ``apps.automation-engine``
table for end-to-end local testing without a real AE running.

AE's full per-trigger table is the CloudEvents envelope (``id``,
``specversion``, ``type``, ``source``, ``datacontenttype``, ``subject``,
``time``, ``data``, ``topic``, ``pubsubname``, traceparent fields,
``received_at``) plus lifecycle columns (``status``, ``retry_count``,
``processed_at``, ``error_message``). The sample declares only the
columns it actually reads.
"""

from __future__ import annotations

from application_sdk.lakehouse import Field, Schema

EVENTS_SCHEMA = Schema(
    fields=[
        Field("id", "string", nullable=False),
        Field("data", "string", nullable=True),
        Field("received_at", "timestamp", nullable=False),
        Field("status", "string", nullable=False),
    ]
)
