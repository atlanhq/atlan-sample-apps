"""
Connector Transformer - Metadata Transformation

The transformer converts raw extracted data into Atlan entity format
using YAML-based transformation templates.

Each YAML file in this directory defines how to map source fields
to Atlan entity attributes.
"""

import os
from typing import Any

from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.transformers.common.utils import get_yaml_query_template_path_mappings
from application_sdk.transformers.query import QueryBasedTransformer

logger = get_logger(__name__)


class ConnectorTransformer(QueryBasedTransformer):
    """
    Transformer for converting source metadata to Atlan format.

    Uses YAML templates to define field mappings. Each template corresponds
    to an entity type (e.g., resource.yaml -> RESOURCE).

    TODO: Add YAML templates for each entity type you want to create.
    """

    def __init__(
        self,
        connector_name: str = "template",  # TODO: Change to your connector name
        tenant_id: str = "default",
        **kwargs: Any,
    ):
        super().__init__(connector_name=connector_name, tenant_id=tenant_id, **kwargs)

        transformer_dir = os.path.dirname(__file__)

        # -----------------------------------------------------------------
        # Register entity types
        # Each entry maps to a YAML file: "RESOURCE" -> resource.yaml
        # TODO: Add your entity types here
        # -----------------------------------------------------------------
        self.entity_class_definitions = get_yaml_query_template_path_mappings(
            transformer_dir,
            [
                "RESOURCE",  # Maps to resource.yaml
                # TODO: Add more entity types as needed
                # "FOLDER",
                # "FILE",
            ],
        )

        logger.info(f"Transformer initialized with types: {list(self.entity_class_definitions.keys())}")
