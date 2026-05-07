# AUTO-GENERATED from contract/app.pkl — DO NOT EDIT MANUALLY.
# To regenerate: make generate
from __future__ import annotations

from typing import ClassVar

from application_sdk.contracts.base import Input
from application_sdk.contracts.types import ConnectionRef


class AppInputContract(Input):
    _config_hash_exclude: ClassVar[set[str]] = {
        "output_dir",
        "load_to_atlan",
    }

    connection: ConnectionRef | None = None
    """Atlan connection to create or reuse."""

    source: str = ""
    """URL, path, or connection string for the data source."""

    output_dir: str = ""
    """Working directory for intermediate files. Auto-generated if empty."""

    load_to_atlan: bool = True
    """Upload transformed assets to Atlan via publish-app when True."""
