"""Schema declarations for the AE events table the sample reads from.

The sample only **reads** events (AE writes them via its event consumer);
it doesn't own a results table. The schema below is reference-only — used
by ``scripts/seed_events.py`` to populate a local ``automation_engine``
table for end-to-end local testing without a real AE running.
"""

from __future__ import annotations

from application_sdk.lakehouse import Field, Schema

EVENTS_SCHEMA = Schema(
    fields=[
        Field("event_id", "string", nullable=False),
        Field("payload", "string", nullable=True),
        Field("received_at", "timestamp", nullable=False),
        Field("status", "string", nullable=False),
    ]
)
