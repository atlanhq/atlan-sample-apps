import os
from typing import Any

from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.transformers.common.utils import (
    get_yaml_query_template_path_mappings,
)
from application_sdk.transformers.query import QueryBasedTransformer

logger = get_logger(__name__)


class AnaplanTransformer(QueryBasedTransformer):
    """Anaplan transformer for converting raw metadata to Atlas format.

    ------------------------------------------------------------
    CALL CHAIN: Activities (transform_data) --> Transformer.transform_metadata() --> Atlas JSON Output

    TRANSFORMATION FLOW:
    1. Raw parquet files read from "raw" directory
    2. YAML templates define mapping rules for each asset type
    3. Transformer converts raw data to Atlas entity format
    4. Transformed data written as JSON to "transformed" directory
    """

    def __init__(
        self, connector_name: str = "anaplan", tenant_id: str = "default", **kwargs: Any
    ):
        """Initialize Anaplan transformer with entity class definitions.

        ------------------------------------------------------------
        ENTITY CLASS SETUP:
        - Maps asset types to their YAML template files
        - Base class automatically loads and applies YAML rules
        """
        super().__init__(connector_name=connector_name, tenant_id=tenant_id, **kwargs)

        # Define entity class definitions for easy asset type expansion
        transformer_dir = os.path.dirname(__file__)

        # Map asset types to their YAML template files
        # NOTE: The get_yaml_query_template_path_mappings function automatically converts YAML filenames to uppercase when creating the mapping
        self.entity_class_definitions = get_yaml_query_template_path_mappings(
            transformer_dir,
            [
                "ANAPLANAPP",
                "ANAPLANPAGE",
            ],
        )

        logger.info("Anaplan transformer initialized with entity class definitions")
        logger.info(
            f"Supported asset types: {list(self.entity_class_definitions.keys())}"
        )
