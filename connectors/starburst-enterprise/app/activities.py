"""
Activities for Starburst Enterprise (SEP) metadata extraction.

This module implements a hybrid extraction pattern:
- REST activities: Fetch Domains, Data Products, Datasets, Dataset Columns from SEP REST API
- SQL activities: Fetch Catalogs, Schemas, Tables, Views, Columns from INFORMATION_SCHEMA
- Join activity: Merge REST Data Products with SQL Schemas/Views

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
    (INFORMATION_SCHEMA layer) and supports merging the two result sets.
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
        """Fetch all Data Products from the SEP REST API.

        Data Products map 1:1 to schemas and contain embedded datasets (views).
        """
        rest_client = self._build_rest_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")

        try:
            products = await rest_client.fetch_data_products()
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
        """Extract Datasets and Dataset Columns from Data Product responses.

        Data Products embed their datasets and columns in the REST response.
        This activity flattens them into separate output files.
        """
        rest_client = self._build_rest_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")

        try:
            products = await rest_client.fetch_data_products()

            datasets: List[Dict[str, Any]] = []
            dataset_columns: List[Dict[str, Any]] = []

            for product in products:
                product_name = product.get("name", "")
                catalog_name = product.get("catalogName", "")
                schema_name = product.get("schemaName", "")
                domain_id = product.get("dataDomainId", "")

                for ds in product.get("datasets", []):
                    ds_record = {
                        "data_product_name": product_name,
                        "data_product_id": product.get("id", ""),
                        "catalog_name": catalog_name,
                        "schema_name": schema_name,
                        "domain_id": domain_id,
                        "dataset_name": ds.get("name", ""),
                        "dataset_description": ds.get("description", ""),
                        "view_definition": ds.get("query", ""),
                        "is_materialized": ds.get("isMaterialized", False),
                    }
                    datasets.append(ds_record)

                    # Extract columns from dataset
                    for col in ds.get("columns", []):
                        col_record = {
                            "data_product_name": product_name,
                            "catalog_name": catalog_name,
                            "schema_name": schema_name,
                            "dataset_name": ds.get("name", ""),
                            "column_name": col.get("name", ""),
                            "data_type": col.get("type", ""),
                            "description": col.get("description", ""),
                        }
                        dataset_columns.append(col_record)

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

    # ─── SQL Activities ────────────────────────────────────────────────

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_catalogs(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch catalog metadata from INFORMATION_SCHEMA via SQL."""
        sql_client = await self._build_sql_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")

        try:
            sql_query = self._load_sql("extract_catalog.sql")
            from sqlalchemy import text

            async with sql_client.engine.connect() as conn:
                result = await conn.execute(text(sql_query))
                rows = result.fetchall()
                columns = list(result.keys())

            if rows:
                data = [dict(zip(columns, row)) for row in rows]
                writer = JsonFileWriter(path=output_path, typename="catalog")
                df = pd.DataFrame(data)
                await writer.write(df)
                logger.info(f"Fetched {len(data)} catalogs via SQL")
                return writer.statistics

            return ActivityStatistics()
        finally:
            if sql_client.engine:
                await sql_client.engine.dispose()

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
        sql_client = await self._build_sql_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")
        catalogs = workflow_args.get("catalogs", [])

        try:
            all_schemas: List[Dict[str, Any]] = []
            from sqlalchemy import text

            async with sql_client.engine.connect() as conn:
                for catalog in catalogs:
                    try:
                        result = await conn.execute(
                            text(
                                f'SELECT catalog_name, schema_name '
                                f'FROM "{catalog}".information_schema.schemata '
                                f"WHERE schema_name != 'information_schema'"
                            )
                        )
                        rows = result.fetchall()
                        columns = list(result.keys())
                        for row in rows:
                            all_schemas.append(dict(zip(columns, row)))
                    except Exception as e:
                        logger.warning(f"Failed to fetch schemas from catalog {catalog}: {e}")

            if all_schemas:
                writer = JsonFileWriter(path=output_path, typename="schema")
                df = pd.DataFrame(all_schemas)
                await writer.write(df)
                logger.info(f"Fetched {len(all_schemas)} schemas via SQL")
                return writer.statistics

            return ActivityStatistics()
        finally:
            if sql_client.engine:
                await sql_client.engine.dispose()

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_tables(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch table and view metadata from INFORMATION_SCHEMA via SQL."""
        sql_client = await self._build_sql_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")
        catalogs = workflow_args.get("catalogs", [])

        try:
            all_tables: List[Dict[str, Any]] = []
            from sqlalchemy import text

            async with sql_client.engine.connect() as conn:
                for catalog in catalogs:
                    try:
                        result = await conn.execute(
                            text(
                                f"SELECT table_catalog, table_schema, table_name, "
                                f"CASE WHEN table_type = 'BASE TABLE' THEN 'TABLE' ELSE table_type END AS table_type "
                                f'FROM "{catalog}".information_schema.tables '
                                f"WHERE table_schema != 'information_schema'"
                            )
                        )
                        rows = result.fetchall()
                        columns = list(result.keys())
                        for row in rows:
                            all_tables.append(dict(zip(columns, row)))
                    except Exception as e:
                        logger.warning(f"Failed to fetch tables from catalog {catalog}: {e}")

            if all_tables:
                writer = JsonFileWriter(path=output_path, typename="table")
                df = pd.DataFrame(all_tables)
                await writer.write(df)
                logger.info(f"Fetched {len(all_tables)} tables/views via SQL")
                return writer.statistics

            return ActivityStatistics()
        finally:
            if sql_client.engine:
                await sql_client.engine.dispose()

    @observability(logger=logger, metrics=metrics, traces=traces)
    @activity.defn
    @auto_heartbeater
    async def fetch_columns(
        self, workflow_args: Dict[str, Any]
    ) -> Optional[ActivityStatistics]:
        """Fetch column metadata from INFORMATION_SCHEMA via SQL."""
        sql_client = await self._build_sql_client(workflow_args)
        base_output_path = workflow_args.get("output_path", "")
        output_path = os.path.join(base_output_path, "raw")
        catalogs = workflow_args.get("catalogs", [])

        try:
            all_columns: List[Dict[str, Any]] = []
            from sqlalchemy import text

            async with sql_client.engine.connect() as conn:
                for catalog in catalogs:
                    try:
                        result = await conn.execute(
                            text(
                                f"SELECT table_catalog, table_schema, table_name, "
                                f"column_name, ordinal_position, column_default, "
                                f"is_nullable, data_type "
                                f'FROM "{catalog}".information_schema.columns '
                                f"WHERE table_schema != 'information_schema'"
                            )
                        )
                        rows = result.fetchall()
                        columns = list(result.keys())
                        for row in rows:
                            all_columns.append(dict(zip(columns, row)))
                    except Exception as e:
                        logger.warning(f"Failed to fetch columns from catalog {catalog}: {e}")

            if all_columns:
                writer = JsonFileWriter(path=output_path, typename="column")
                df = pd.DataFrame(all_columns)
                await writer.write(df)
                logger.info(f"Fetched {len(all_columns)} columns via SQL")
                return writer.statistics

            return ActivityStatistics()
        finally:
            if sql_client.engine:
                await sql_client.engine.dispose()

    # ─── Helper Methods ────────────────────────────────────────────────

    def _build_rest_client(self, workflow_args: Dict[str, Any]) -> SEPRestClient:
        """Build a REST client from workflow args credentials."""
        creds = workflow_args.get("credentials", {})
        return SEPRestClient(
            host=creds["host"],
            port=int(creds.get("port", 8080)),
            username=creds["username"],
            password=creds.get("password", ""),
            http_scheme=creds.get("http_scheme", "https"),
            role=creds.get("role", "sysadmin"),
        )

    async def _build_sql_client(self, workflow_args: Dict[str, Any]) -> SEPSQLClient:
        """Build a SQL client from workflow args credentials."""
        creds = workflow_args.get("credentials", {})
        client = SEPSQLClient()
        await client.setup(
            {
                "user": creds["username"],
                "password": creds.get("password", ""),
                "host": creds["host"],
                "port": str(creds.get("port", 8080)),
                "catalog": creds.get("catalog", "system"),
            }
        )
        return client

    @staticmethod
    def _load_sql(filename: str) -> str:
        """Load a SQL template from the app/sql/ directory."""
        sql_dir = os.path.join(os.path.dirname(__file__), "sql")
        filepath = os.path.join(sql_dir, filename)
        with open(filepath, "r") as f:
            return f.read()
