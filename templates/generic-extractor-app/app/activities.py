"""
Connector Activities - Temporal Activity Definitions

Activities are the individual units of work in a workflow.
This template includes three main activities:
1. extract_metadata - Fetches data from your source
2. transform_metadata - Converts to Atlan format
3. write_output - Writes JSON-L files for publishing

Each activity is decorated with @activity.defn for Temporal registration.
"""

import os
from typing import Any, Dict, List, Type

import daft
import pandas as pd
from app.clients import ConnectorClient
from app.handlers import ConnectorHandler
from app.transformers import ConnectorTransformer
from application_sdk.activities.common.models import ActivityStatistics
from application_sdk.activities.common.utils import auto_heartbeater, get_workflow_id
from application_sdk.activities.metadata_extraction.base import (
    BaseMetadataExtractionActivities,
    BaseMetadataExtractionActivitiesState,
)
from application_sdk.io.json import JsonFileWriter
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.transformers import TransformerInterface
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger


class ConnectorActivitiesState(BaseMetadataExtractionActivitiesState):
    """
    State container for activities within a workflow execution.

    Add any workflow-scoped state variables here that need to persist
    across activity executions within the same workflow run.
    """

    # Track extracted data for use in later activities
    extracted_data: List[Dict[str, Any]] = []
    # Track transformed data for write activity
    transformed_data: Any = None


class ConnectorActivities(BaseMetadataExtractionActivities):
    """
    Activity implementations for the connector workflow.

    Activities handle the actual work: API calls, data transformation, file I/O.
    The SDK provides automatic heartbeating and state management.
    """

    def __init__(
        self,
        client_class: Type[ConnectorClient] | None = None,
        handler_class: Type[ConnectorHandler] | None = None,
        transformer_class: Type[TransformerInterface] | None = None,
    ):
        super().__init__(
            client_class=client_class or ConnectorClient,
            handler_class=handler_class or ConnectorHandler,
            transformer_class=transformer_class or ConnectorTransformer,
        )

    async def _set_state(self, workflow_args: Dict[str, Any]):
        """Initialize activity state for this workflow run."""
        workflow_id = get_workflow_id()
        if not self._state.get(workflow_id):
            self._state[workflow_id] = ConnectorActivitiesState()
        await super()._set_state(workflow_args)

    # =========================================================================
    # ACTIVITY: Extract Metadata
    # =========================================================================
    @auto_heartbeater
    @activity.defn
    async def extract_metadata(self, workflow_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from the source system.

        This activity fetches raw metadata from your data source and stores it
        for the transformation step.

        TODO: Implement your extraction logic in the client and call it here.

        Args:
            workflow_args: Workflow configuration including credentials, output_path, etc.

        Returns:
            Dict with extraction statistics.
        """
        logger.info("Starting metadata extraction")

        try:
            state = await self._get_state(workflow_args)

            if not state.client:
                raise ValueError("Client not initialized")

            # -----------------------------------------------------------------
            # EXTRACTION LOGIC
            # TODO: Call your client methods to fetch metadata
            # The stub implementation fetches placeholder data
            # -----------------------------------------------------------------
            raw_data = await state.client.fetch_metadata()

            # Store in state for transformation activity
            state.extracted_data = raw_data

            logger.info(f"Extracted {len(raw_data)} records")

            return {
                "status": "success",
                "records_extracted": len(raw_data),
            }

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise

    # =========================================================================
    # ACTIVITY: Transform Metadata
    # =========================================================================
    @auto_heartbeater
    @activity.defn
    async def transform_metadata(self, workflow_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform extracted metadata to Atlan format.

        This activity converts raw source data into the Atlan entity format
        using YAML-based transformation templates.

        TODO: Define your transformation templates in app/transformers/*.yaml

        Args:
            workflow_args: Workflow configuration.

        Returns:
            Dict with transformation statistics.
        """
        logger.info("Starting metadata transformation")

        try:
            state = await self._get_state(workflow_args)

            if not state.transformer:
                raise ValueError("Transformer not initialized")

            if not state.extracted_data:
                logger.warning("No data to transform")
                return {"status": "success", "records_transformed": 0}

            # -----------------------------------------------------------------
            # TRANSFORMATION LOGIC
            # Convert extracted data using the transformer
            # The transformer uses YAML templates to map fields
            # -----------------------------------------------------------------

            # Create a Daft DataFrame from extracted data
            df = daft.from_pylist(state.extracted_data)

            # Add connection info required by transformer
            connection_name = workflow_args.get("connection", {}).get("connection_name", "")
            connection_qn = workflow_args.get("connection", {}).get("connection_qualified_name", "")

            # Transform using YAML template
            transformed_df = state.transformer.transform_metadata(
                dataframe=df,
                typename="resource",  # Matches YAML filename
                connection_name=connection_name,
                connection_qualified_name=connection_qn,
                **workflow_args,
            )

            # Store transformed data for write activity
            state.transformed_data = transformed_df

            record_count = transformed_df.count_rows() if transformed_df is not None else 0
            logger.info(f"Transformed {record_count} records")

            return {
                "status": "success",
                "records_transformed": record_count,
            }

        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            raise

    # =========================================================================
    # ACTIVITY: Write Output
    # =========================================================================
    @auto_heartbeater
    @activity.defn
    async def write_output(self, workflow_args: Dict[str, Any]) -> ActivityStatistics:
        """
        Write transformed metadata to JSON-L files.

        This activity writes the transformed data to JSON-L format files
        that can be published to Atlan.

        Args:
            workflow_args: Workflow configuration including output_path.

        Returns:
            ActivityStatistics with write metrics.
        """
        logger.info("Starting output write")

        try:
            state = await self._get_state(workflow_args)
            # The output_path var is injected OOTB and establishes a path relevant to the workflow run
            output_path = workflow_args.get("output_path", "/tmp/connector-output")

            # Setup JSON writer
            json_writer = JsonFileWriter(
                path=os.path.join(output_path, "transformed", "resource"),
                typename="resource",
            )

            # -----------------------------------------------------------------
            # WRITE LOGIC
            # Write transformed data to JSON-L files
            # -----------------------------------------------------------------
            if hasattr(state, "transformed_data") and state.transformed_data is not None:
                # Convert Daft DataFrame to pandas for the writer
                # The SDK's writer calls len() and head() which work on pandas DataFrames
                pandas_df = state.transformed_data.to_pandas()
                await json_writer.write(pandas_df)
                logger.info(f"Wrote output to: {json_writer.path}")
            else:
                logger.warning("No transformed data to write")

            return json_writer.statistics

        except Exception as e:
            logger.error(f"Write failed: {e}")
            raise
