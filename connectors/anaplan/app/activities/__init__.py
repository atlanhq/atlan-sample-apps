import json
import os
from typing import Any, Dict, Type

import pandas as pd
from app.activities.extracts.apps import extract_apps_data
from app.activities.extracts.pages import extract_pages_with_details
from app.activities.utils import get_app_guids, setup_parquet_output, should_include_asset
from app.clients import AppClient
from app.handlers import AppHandler
from app.transformers import AppTransformer
from application_sdk.activities.common.models import ActivityStatistics
from application_sdk.activities.common.utils import auto_heartbeater, get_workflow_id
from application_sdk.activities.metadata_extraction.base import (
    BaseMetadataExtractionActivities,
    BaseMetadataExtractionActivitiesState,
)
from application_sdk.inputs.parquet import ParquetInput
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from application_sdk.outputs.json import JsonOutput
from application_sdk.transformers import TransformerInterface
from temporalio import activity

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()
activity.logger = logger


class AppMetadataExtractionActivitiesState(BaseMetadataExtractionActivitiesState):
    """State class for App metadata extraction activities.

    Extends the base state with App-specific state attributes.
    Manages the current filter state and configuration for include/exclude operations.

    Attributes:
        metadata_filter_state: Current filter state ("include", "exclude", or "none").
        metadata_filter: Current metadata filter configuration.
    """

    # App-specific workflow parameters
    metadata_filter_state: str = "none"
    metadata_filter: Dict[str, Any] = {}


class AppMetadataExtractionActivities(BaseMetadataExtractionActivities):
    """App metadata extraction activities for Temporal workflow execution.

    Provides activities for extracting and transforming App metadata including
    assets like apps and pages with support for metadata filtering.
    """

    def __init__(
        self,
        client_class: Type[AppClient] | None = None,
        handler_class: Type[AppHandler] | None = None,
        transformer_class: Type[TransformerInterface] | None = None,
    ):
        """Initialize App metadata extraction activities.

        Args:
            client_class: Optional AppClient class for API operations.
            handler_class: Optional AppHandler class for business logic.
            transformer_class: Optional TransformerInterface class for data transformation.
        """

        super().__init__(
            client_class=client_class or AppClient,
            handler_class=handler_class or AppHandler,
            transformer_class=transformer_class or AppTransformer,
        )

    # ============================================================================
    # SECTION 1: STATE RELATED METHODS
    # ============================================================================

    async def _set_state(self, workflow_args: Dict[str, Any]):
        """Initialize workflow state with App client, credentials, and transformer.

        Called by the SDK before first activity execution. Extracts credentials from
        SecretStoreInput using credential_guid and initializes all required components.

        Args:
            workflow_args: Dictionary containing workflow configuration and credentials.

        Note:
            Explicitly defined to set the client with credentials one time only,
            allowing single credentialStore lookup.
        """
        workflow_id = get_workflow_id()
        if not self._state.get(workflow_id):
            self._state[workflow_id] = AppMetadataExtractionActivitiesState()

        # Call parent class _set_state to set up client, handler, and transformer
        await super()._set_state(workflow_args)

        # Set metadata filter state to none
        state = self._state[workflow_id]
        if isinstance(state, AppMetadataExtractionActivitiesState):
            state.metadata_filter_state = "none"
            state.metadata_filter = {}

        logger.info(
            f"State set with client, handler, transformer, and metadata filter: {self._state[workflow_id]}"
        )

    # ============================================================================
    # SECTION 2: DEFINED ACTIVITIES
    # ============================================================================

    @auto_heartbeater
    @activity.defn
    async def set_metadata_filter_state(
        self, workflow_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set metadata filter state for workflow execution.

        Evaluates the precedence of metadata filters and maintains state variables
        for use in subsequent activities without re-evaluating filter precedence.

        Args:
            workflow_args: Dictionary containing metadata filter configuration.

        Returns:
            Dictionary containing the metadata filter and filter state.

        Raises:
            ValueError: If invalid JSON is found in include-metadata or exclude-metadata.
        """
        try:
            # Get state to verify it's working
            state = await self._get_state(workflow_args)

            metadata = workflow_args.get("metadata", {})

            try:
                temp_include_metadata = json.loads(metadata.get("include-metadata"))
                temp_exclude_metadata = json.loads(metadata.get("exclude-metadata"))

                if temp_include_metadata:
                    state.metadata_filter_state = "include"
                    state.metadata_filter = temp_include_metadata
                    logger.info(
                        f"Metadata filter state set to include with filter: {state.metadata_filter}"
                    )
                elif temp_exclude_metadata:
                    state.metadata_filter_state = "exclude"
                    state.metadata_filter = temp_exclude_metadata
                    logger.info(
                        f"Metadata filter state set to exclude with filter: {state.metadata_filter}"
                    )
                elif not temp_include_metadata and not temp_exclude_metadata:
                    state.metadata_filter_state = "none"
                    state.metadata_filter = {}
                    logger.info(
                        f"Metadata filter state set to none with filter: {state.metadata_filter}"
                    )
                else:
                    raise ValueError(
                        "Invalid JSON in include-metadata or exclude-metadata"
                    )
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in include-metadata or exclude-metadata")

            return {
                "metadata_filter": state.metadata_filter,
                "metadata_filter_state": state.metadata_filter_state,
            }

        except Exception as e:
            logger.error(f"Failed to set metadata filter state: {str(e)}")
            raise

    @auto_heartbeater
    @activity.defn
    async def extract_apps(
        self, workflow_args: Dict[str, Any]
    ) -> ActivityStatistics:
        """Extract app assets from Anaplan.

        Fetches all available apps from Anaplan API, applies metadata filtering,
        and writes the results to parquet files.

        Args:
            workflow_args: Dictionary containing workflow configuration.

        Returns:
            ActivityStatistics: Statistics about the extraction operation.

        Raises:
            ValueError: If Anaplan client is not found in state.
        """
        try:
            # Get state to access shared client instance
            state = await self._get_state(workflow_args)

            if not state.client:
                raise ValueError("Anaplan client not found in state")

            # Setup parquet output
            parquet_output = setup_parquet_output(workflow_args, "raw/app")

            # Extract all apps data (unfiltered)
            app_data = await extract_apps_data(state.client)
            
            # Check for filters and apply them
            filtered_app_data = [
                app
                for app in app_data
                if should_include_asset(
                    app, "app", state.metadata_filter_state, state.metadata_filter
                )
            ]

            # Create DataFrame and write to parquet
            if filtered_app_data:
                # Use pandas instead of daft : avoid nested directory structure
                pandas_df = pd.DataFrame(app_data)
                await parquet_output.write_dataframe(pandas_df)

                logger.info(
                    f"Successfully wrote {len(app_data)} apps to: {parquet_output.get_full_path()}"
                )

            else:
                logger.warning(
                    f"No apps found, skipping write: {parquet_output.get_full_path()}"
                )

            statistics = await parquet_output.get_statistics(typename="app")
            return statistics

        except Exception as e:
            logger.error(f"Failed to extract apps: {str(e)}")
            raise

    @auto_heartbeater
    @activity.defn
    async def extract_pages(
        self, workflow_args: Dict[str, Any]
    ) -> ActivityStatistics:
        """Extract page assets from Anaplan.

        Fetches all available pages from Anaplan API with detailed information,
        applies metadata filtering, and writes the results to parquet files.

        Args:
            workflow_args: Dictionary containing workflow configuration.

        Returns:
            ActivityStatistics: Statistics about the extraction operation.

        Raises:
            ValueError: If Anaplan client is not found in state.
        """
        try:
            # Get state to access shared client instance
            state = await self._get_state(workflow_args)

            if not state.client:
                raise ValueError("Anaplan client not found in state")

            # Get valid app GUIDs for filtering
            all_apps = await get_app_guids(workflow_args)

            # Setup parquet output
            parquet_output = setup_parquet_output(workflow_args, "raw/page")

            # Extract pages data with details (unfiltered)
            all_detailed_page_data = await extract_pages_with_details(
                state.client,
                all_apps,
            )
            
            # Apply metadata filtering logic
            detailed_page_data = [
                page
                for page in all_detailed_page_data
                if should_include_asset(
                    page, "page", state.metadata_filter_state, state.metadata_filter
                )
            ]

            # Create DataFrame and write to parquet
            if detailed_page_data:
                # Use pandas instead of daft : avoid nested directory structure
                pandas_df = pd.DataFrame(detailed_page_data)
                await parquet_output.write_dataframe(pandas_df)

                logger.info(
                    f"Successfully wrote {len(detailed_page_data)} pages to: {parquet_output.get_full_path()}"
                )

            else:
                logger.warning(
                    f"No pages found, skipping write: {parquet_output.get_full_path()}"
                )

            statistics = await parquet_output.get_statistics(typename="page")
            return statistics

        except Exception as e:
            logger.error(f"Failed to extract pages: {str(e)}")
            raise

    @auto_heartbeater
    @activity.defn
    async def transform_data(self, workflow_args: Dict[str, Any]) -> ActivityStatistics:
        """Transform raw Anaplan metadata into Atlas format.

        Reads raw parquet files and transforms them into Atlas-compatible JSON format
        using the configured transformer.

        Args:
            workflow_args: Dictionary containing workflow configuration including typename.

        Returns:
            ActivityStatistics: Statistics about the transformation operation.

        Raises:
            ValueError: If transformer is not found in state or required parameters are missing.
        """
        try:
            # Get state to access transformer
            state = await self._get_state(workflow_args)

            if not state.transformer:
                raise ValueError("Transformer not found in state")

            # Extract required parameters from workflow_args
            output_prefix = workflow_args.get("output_prefix")
            output_path = workflow_args.get("output_path")
            typename = workflow_args.get("typename")

            if not output_prefix or not output_path:
                raise ValueError(
                    "Output prefix and path must be specified in workflow_args"
                )
            if not typename:
                raise ValueError("Typename not found in workflow_args")

            # Setup input for reading raw parquet files
            # Use the typename to construct the correct path
            raw_input = ParquetInput(
                path=os.path.join(output_path, "raw", typename),
                input_prefix=output_prefix,
                file_names=None,
                chunk_size=None,
            )
            raw_input = raw_input.get_batched_daft_dataframe()

            # Setup output for writing transformed JSON files
            transformed_output = JsonOutput(
                output_prefix=output_prefix,
                output_path=output_path,
                output_suffix="transformed",
                typename=typename,
                chunk_start=workflow_args.get("chunk_start"),
            )

            # Add connection information to workflow_args for transformer
            workflow_args["connection_name"] = workflow_args.get("connection", {}).get(
                "connection_name", None
            )
            workflow_args["connection_qualified_name"] = workflow_args.get(
                "connection", {}
            ).get("connection_qualified_name", None)

            # Process each batch of raw data
            async for dataframe in raw_input:
                if dataframe is not None and dataframe.count_rows() > 0:
                    # Transform raw data to Atlas format using transformer
                    transform_metadata = state.transformer.transform_metadata(
                        dataframe=dataframe, **workflow_args
                    )

                    # Write transformed data to JSON output
                    await transformed_output.write_daft_dataframe(transform_metadata)

            # Return transformation statistics
            return await transformed_output.get_statistics(typename=typename)

        except Exception as e:
            logger.error(f"Failed to transform data: {str(e)}")
            raise
