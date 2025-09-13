import os
from typing import Any

from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.transformers.common.utils import (
    get_yaml_query_template_path_mappings,
)
from application_sdk.transformers.query import QueryBasedTransformer

logger = get_logger(__name__)


class AppTransformer(QueryBasedTransformer):
    """Transformer for converting raw metadata to Atlas format.

    Transforms raw App metadata from parquet files into Atlas-compatible
    JSON format using YAML template definitions.
    """

    def __init__(
        self, connector_name: str = "anaplan", tenant_id: str = "default", **kwargs: Any
    ):
        """Initialize transformer with entity class definitions.

        Sets up the transformer with YAML template mappings for App asset types.
        The base class automatically loads and applies YAML transformation rules.

        Args:
            connector_name: Name of the connector (default: "anaplan").
            tenant_id: Tenant identifier (default: "default").
            **kwargs: Additional keyword arguments passed to parent class.
        """
        super().__init__(connector_name=connector_name, tenant_id=tenant_id, **kwargs)

        # Define entity class definitions for easy asset type expansion
        transformer_dir = os.path.dirname(__file__)

        # Map asset types to their YAML template files
        # NOTE: The get_yaml_query_template_path_mappings function automatically converts YAML filenames to uppercase when creating the mapping
        self.entity_class_definitions = get_yaml_query_template_path_mappings(
            transformer_dir,
            [
                "APP",
                "PAGE",
            ],
        )

        logger.info("App transformer initialized with entity class definitions")
        logger.info(
            f"Supported asset types: {list(self.entity_class_definitions.keys())}"
        )
