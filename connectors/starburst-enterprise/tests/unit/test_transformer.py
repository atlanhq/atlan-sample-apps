"""
Unit tests for Starburst Enterprise metadata transformer.
"""

from app.transformer import (
    SEPCatalog,
    SEPColumn,
    SEPDataProduct,
    SEPDataset,
    SEPDatasetColumn,
    SEPDomain,
    SEPSchema,
    SEPTable,
)


class TestSEPDomain:
    def test_get_attributes(self):
        obj = {
            "name": "Finance",
            "description": "Financial data domain",
            "schemaLocation": "s3://bucket/finance",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPDomain.get_attributes(obj)
        assert result["attributes"]["name"] == "Finance"
        assert "default/starburst/1234" in result["attributes"]["qualifiedName"]


class TestSEPDataProduct:
    def test_get_attributes(self):
        obj = {
            "name": "Revenue Metrics",
            "summary": "Revenue data product",
            "catalogName": "hive",
            "schemaName": "revenue_metrics",
            "status": "PUBLISHED",
            "dataDomainId": "domain-1",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPDataProduct.get_attributes(obj)
        assert result["attributes"]["name"] == "Revenue Metrics"
        assert result["attributes"]["status"] == "PUBLISHED"
        assert result["attributes"]["catalogName"] == "hive"


class TestSEPDataset:
    def test_get_attributes(self):
        obj = {
            "dataset_name": "monthly_revenue",
            "dataset_description": "Monthly revenue view",
            "view_definition": "SELECT * FROM revenue",
            "catalog_name": "hive",
            "schema_name": "revenue_metrics",
            "data_product_name": "Revenue Metrics",
            "is_materialized": False,
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPDataset.get_attributes(obj)
        assert result["attributes"]["name"] == "monthly_revenue"
        assert result["custom_attributes"]["is_materialized"] is False


class TestSEPDatasetColumn:
    def test_get_attributes(self):
        obj = {
            "column_name": "amount",
            "data_type": "decimal(10,2)",
            "description": "Revenue amount",
            "catalog_name": "hive",
            "schema_name": "revenue_metrics",
            "dataset_name": "monthly_revenue",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPDatasetColumn.get_attributes(obj)
        assert result["attributes"]["name"] == "amount"
        assert result["attributes"]["dataType"] == "decimal(10,2)"


class TestSEPCatalog:
    def test_get_attributes(self):
        obj = {
            "catalog_name": "hive",
            "catalog_kind": "hive",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPCatalog.get_attributes(obj)
        assert result["attributes"]["name"] == "hive"
        assert result["custom_attributes"]["catalog_kind"] == "hive"


class TestSEPSchema:
    def test_get_attributes(self):
        obj = {
            "catalog_name": "hive",
            "schema_name": "public",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPSchema.get_attributes(obj)
        assert result["attributes"]["name"] == "public"
        assert result["attributes"]["databaseName"] == "hive"


class TestSEPTable:
    def test_get_attributes(self):
        obj = {
            "table_catalog": "hive",
            "table_schema": "public",
            "table_name": "users",
            "table_type": "TABLE",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPTable.get_attributes(obj)
        assert result["attributes"]["name"] == "users"
        assert result["attributes"]["schemaName"] == "public"
        assert result["custom_attributes"]["table_type"] == "TABLE"


class TestSEPColumn:
    def test_get_attributes(self):
        obj = {
            "table_catalog": "hive",
            "table_schema": "public",
            "table_name": "users",
            "column_name": "email",
            "ordinal_position": 3,
            "is_nullable": "YES",
            "data_type": "varchar",
            "column_default": "",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPColumn.get_attributes(obj)
        assert result["attributes"]["name"] == "email"
        assert result["attributes"]["isNullable"] is True
        assert result["attributes"]["order"] == 3
