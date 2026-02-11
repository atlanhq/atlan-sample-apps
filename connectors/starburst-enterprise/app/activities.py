"""
Activities for Starburst Enterprise (SEP) metadata extraction.

This module implements a hybrid extraction pattern:
- REST activities: Fetch Domains, Data Products, Datasets, Dataset Columns from SEP REST API
- SQL activities: Fetch Catalogs, Schemas, Tables, Views, Columns from INFORMATION_SCHEMA

Each activity is independently retriable via Temporal.
"""

import os
from typing import Any, Dict, List, Optional

import pandas as pd
from app.rest_client import SEPRestClient
from app.sql_client import SEPSQLClient
from application_sdk.activities import ActivitiesInterface
from application_sdk.activities.common.models import ActivityStatistics
from application_sdk.activities.common.utils import auto_heartbeater
from application_sdk.io.json import JsonFileWriter
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger
metrics = get_metrics()
traces = get_traces()


class SEPMetadataExtractionActivities(ActivitiesInterface):
    """Activities for extracting metadata from Starburst Enterprise.

    Combines REST API extraction (Data Products layer) with SQL extraction
    (INFORMATION_SCHEMA layer).
    """

    # ─── REST API Activities ───────────────────────────────────────────

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_domains(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch all Domains from the SEP REST API.

        Domains are organizational containers for Data Products.
        """
        rest_client = self._build_rest_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")

        try:
            domains = await rest_client.fetch_domains()
            logger.info(f"Fetched {len(domains)} domains from SEP REST API")

            if domains:
                writer = JsonFileWriter(path=output_path, typename="domain")
                df = pd.DataFrame(domains)
                await writer.write(df)
                return writer.statistics

            return ActivityStatistics()
        finally:
            await rest_client.close()

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_data_products(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch all Data Products with full details from the SEP REST API.

        Fetches the summary list first, then fetches each product's detail
        endpoint to get the embedded views/materializedViews.
        """
        rest_client = self._build_rest_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")

        try:
            products = await rest_client.fetch_all_data_products_with_details()
            logger.info(f"Fetched {len(products)} data products from SEP REST API")

            if products:
                writer = JsonFileWriter(path=output_path, typename="data_product")
                df = pd.DataFrame(products)
                await writer.write(df)
                return writer.statistics

            return ActivityStatistics()
        finally:
            await rest_client.close()

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def extract_datasets_from_products(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Extract Datasets and Dataset Columns from Data Product detail responses.

        Data Products embed their datasets as views[] and materializedViews[].
        Each view/materializedView contains columns[].
        This activity flattens them into separate output files.
        """
        rest_client = self._build_rest_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")

        try:
            products = await rest_client.fetch_all_data_products_with_details()

            datasets: List[Dict[str, Any]] = []
            dataset_columns: List[Dict[str, Any]] = []

            for product in products:
                product_name = product.get("name", "")
                product_id = product.get("id", "")
                catalog_name = product.get("catalogName", "")
                schema_name = product.get("schemaName", "")
                domain_id = product.get("dataDomainId", "")

                # Process views (is_materialized=False)
                for view in product.get("views", []):
                    self._extract_dataset_record(
                        view,
                        is_materialized=False,
                        product_name=product_name,
                        product_id=product_id,
                        catalog_name=catalog_name,
                        schema_name=schema_name,
                        domain_id=domain_id,
                        datasets=datasets,
                        dataset_columns=dataset_columns,
                    )

                # Process materializedViews (is_materialized=True)
                for mv in product.get("materializedViews", []):
                    self._extract_dataset_record(
                        mv,
                        is_materialized=True,
                        product_name=product_name,
                        product_id=product_id,
                        catalog_name=catalog_name,
                        schema_name=schema_name,
                        domain_id=domain_id,
                        datasets=datasets,
                        dataset_columns=dataset_columns,
                    )

            statistics = ActivityStatistics()

            if datasets:
                writer = JsonFileWriter(path=output_path, typename="dataset")
                df = pd.DataFrame(datasets)
                await writer.write(df)
                statistics = writer.statistics
                logger.info(f"Extracted {len(datasets)} datasets from data products")

            if dataset_columns:
                col_writer = JsonFileWriter(path=output_path, typename="dataset_column")
                df = pd.DataFrame(dataset_columns)
                await col_writer.write(df)
                logger.info(f"Extracted {len(dataset_columns)} dataset columns")

            return statistics
        finally:
            await rest_client.close()

    @staticmethod
    def _extract_dataset_record(
        view_obj: Dict[str, Any],
        is_materialized: bool,
        product_name: str,
        product_id: str,
        catalog_name: str,
        schema_name: str,
        domain_id: str,
        datasets: List[Dict[str, Any]],
        dataset_columns: List[Dict[str, Any]],
    ) -> None:
        """Extract a single view/materializedView into dataset + column records."""
        ds_record = {
            "data_product_name": product_name,
            "data_product_id": product_id,
            "catalog_name": catalog_name,
            "schema_name": schema_name,
            "domain_id": domain_id,
            "dataset_name": view_obj.get("name", ""),
            "dataset_description": view_obj.get("description", ""),
            "view_definition": view_obj.get("definitionQuery", ""),
            "is_materialized": is_materialized,
            "status": view_obj.get("status", ""),
        }
        datasets.append(ds_record)

        for col in view_obj.get("columns", []):
            col_record = {
                "data_product_name": product_name,
                "catalog_name": catalog_name,
                "schema_name": schema_name,
                "dataset_name": view_obj.get("name", ""),
                "column_name": col.get("name", ""),
                "data_type": col.get("type", ""),
                "description": col.get("description", ""),
            }
            dataset_columns.append(col_record)

    # ─── SQL Activities ────────────────────────────────────────────────

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_catalogs(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch catalog metadata from system.metadata.catalogs via SQL."""
        sql_client = self._build_sql_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")

        try:
            data = await sql_client.fetch_catalogs()

            if data:
                writer = JsonFileWriter(path=output_path, typename="catalog")
                df = pd.DataFrame(data)
                await writer.write(df)
                logger.info(f"Fetched {len(data)} catalogs via SQL")
                return writer.statistics

            return ActivityStatistics()
        except Exception as e:
            logger.error(f"Failed to fetch catalogs: {e}")
            raise

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_schemas(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch schema metadata from INFORMATION_SCHEMA via SQL.

        Iterates over selected catalogs and queries each catalog's
        information_schema.schemata.
        """
        sql_client = self._build_sql_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")
        catalogs = workflow_args.get("catalogs", [])

        all_schemas: List[Dict[str, Any]] = []
        for catalog in catalogs:
            try:
                schemas = await sql_client.fetch_schemas(catalog)
                all_schemas.extend(schemas)
            except Exception as e:
                logger.warning(f"Failed to fetch schemas from catalog {catalog}: {e}")

        if all_schemas:
            writer = JsonFileWriter(path=output_path, typename="schema")
            df = pd.DataFrame(all_schemas)
            await writer.write(df)
            logger.info(f"Fetched {len(all_schemas)} schemas via SQL")
            return writer.statistics

        return ActivityStatistics()

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_tables(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch table and view metadata from INFORMATION_SCHEMA via SQL."""
        sql_client = self._build_sql_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")
        catalogs = workflow_args.get("catalogs", [])

        all_tables: List[Dict[str, Any]] = []
        for catalog in catalogs:
            try:
                tables = await sql_client.fetch_tables(catalog)
                all_tables.extend(tables)
            except Exception as e:
                logger.warning(f"Failed to fetch tables from catalog {catalog}: {e}")

        if all_tables:
            writer = JsonFileWriter(path=output_path, typename="table")
            df = pd.DataFrame(all_tables)
            await writer.write(df)
            logger.info(f"Fetched {len(all_tables)} tables/views via SQL")
            return writer.statistics

        return ActivityStatistics()

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_columns(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch column metadata from INFORMATION_SCHEMA via SQL."""
        sql_client = self._build_sql_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")
        catalogs = workflow_args.get("catalogs", [])

        all_columns: List[Dict[str, Any]] = []
        for catalog in catalogs:
            try:
                columns = await sql_client.fetch_columns(catalog)
                all_columns.extend(columns)
            except Exception as e:
                logger.warning(f"Failed to fetch columns from catalog {catalog}: {e}")

        if all_columns:
            writer = JsonFileWriter(path=output_path, typename="column")
            df = pd.DataFrame(all_columns)
            await writer.write(df)
            logger.info(f"Fetched {len(all_columns)} columns via SQL")
            return writer.statistics

        return ActivityStatistics()

    # ─── Helper Methods ────────────────────────────────────────────────

    def _build_rest_client(self, workflow_args: Dict[str, Any]) -> SEPRestClient:
        """Build a REST client from workflow args credentials."""
        creds = workflow_args.get("credentials", {})
        return SEPRestClient(
            host=creds["host"],
            port=int(creds.get("port", 443)),
            username=creds["username"],
            password=creds.get("password", ""),
            http_scheme=creds.get("http_scheme", "https"),
            role=creds.get("role", "sysadmin"),
        )

    def _build_sql_client(self, workflow_args: Dict[str, Any]) -> SEPSQLClient:
        """Build a SQL client from workflow args credentials."""
        creds = workflow_args.get("credentials", {})
        return SEPSQLClient(
            host=creds["host"],
            port=int(creds.get("port", 443)),
            username=creds["username"],
            password=creds.get("password", ""),
            http_scheme=creds.get("http_scheme", "https"),
            catalog=creds.get("catalog", "system"),
            role=creds.get("role", "sysadmin"),
        )
