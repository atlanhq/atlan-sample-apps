"""Data contracts for the Generic Connector.

All contracts extend Input/Output base classes for type safety and Temporal
serialization compatibility.  Each App and @task method uses a single
dataclass for input and output.

Replace or extend these with fields specific to your source system.
"""

from application_sdk.app import Input, Output
from application_sdk.contracts.types import ConnectionRef, FileReference

# =============================================================================
# App-level contracts
# =============================================================================


class GenericConnectorInput(Input):
    """Top-level input for the Generic Connector workflow."""

    connection: ConnectionRef | None = None
    """Atlan connection reference — resolved from the workflow UI."""

    source: str = ""
    """Source identifier (URL, path, or connection string) for the data source."""

    output_dir: str = ""
    """Working directory for intermediate files.  Auto-generated if empty."""

    load_to_atlan: bool = True
    """Upload transformed assets to Atlan via publish-app when True."""


class GenericConnectorOutput(Output):
    """Top-level output from the Generic Connector workflow."""

    connection_qualified_name: str = ""
    transformed_data_prefix: str = ""

    record_count: int = 0
    """Total number of asset records written to the output file."""

    output_file: FileReference | None = None
    """FileReference to the final Atlan assets JSONL file."""

    atlan_loaded_count: int = 0
    atlan_created_count: int = 0
    atlan_updated_count: int = 0
    atlan_error_count: int = 0
    atlan_errors: list = []


# =============================================================================
# Task-level contracts: extract
# =============================================================================


class ExtractInput(Input):
    """Input for the extract task."""

    source: str = ""
    """Source identifier passed from the top-level workflow input."""

    output_dir: str = ""
    """Directory for raw JSONL output files."""


class ExtractOutput(Output):
    """Output from the extract task."""

    output_file: FileReference | None = None
    """FileReference to the raw JSONL file written by the extract task."""

    record_count: int = 0
    """Number of raw records extracted."""


# =============================================================================
# Task-level contracts: transform
# =============================================================================


class TransformInput(Input):
    """Input for the transform task."""

    raw_file: FileReference | None = None
    """FileReference to the raw JSONL file produced by extract."""

    connection_qualified_name: str = ""
    """Atlan connection QN — used to build asset qualified names."""

    output_dir: str = ""
    """Directory for the transformed output file."""

    workflow_id: str = ""
    """Temporal workflow ID — stamped onto every asset for sync tracking."""


class TransformOutput(Output):
    """Output from the transform task."""

    output_file: FileReference | None = None
    """FileReference to the Atlan assets JSONL file."""

    record_count: int = 0
    """Number of Atlan asset records written."""
