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
            "type": "PRIVATE",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPDomain.get_attributes(obj)
        assert result["attributes"]["name"] == "Finance"
        assert result["attributes"]["description"] == "Financial data domain"
        assert result["attributes"]["schemaLocationUri"] == "s3://bucket/finance"
        assert result["custom_attributes"]["type"] == "PRIVATE"
        assert "default/starburst/1234" in result["attributes"]["qualifiedName"]

    def test_empty_optional_fields(self):
        obj = {
            "name": "Minimal",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPDomain.get_attributes(obj)
        assert result["attributes"]["name"] == "Minimal"
        assert result["attributes"]["description"] == ""
        assert result["custom_attributes"]["type"] == ""


class TestSEPDataProduct:
    def test_get_attributes(self):
        obj = {
            "name": "Revenue Metrics",
            "summary": "Revenue data product",
            "description": "Detailed description",
            "catalogName": "hive",
            "schemaName": "revenue_metrics",
            "status": "PUBLISHED",
            "dataDomainId": "domain-1",
            "domainName": "Finance",
            "type": "PRIVATE",
            "publishedAt": "2026-01-01T00:00:00Z",
            "publishedBy": "admin",
            "owners": [{"name": "Alice", "email": "alice@example.com"}],
            "accessMetadata": {
                "lastQueriedAt": "2026-02-01T00:00:00Z",
                "lastQueriedBy": "bob",
            },
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPDataProduct.get_attributes(obj)
        attrs = result["attributes"]
        custom = result["custom_attributes"]

        assert attrs["name"] == "Revenue Metrics"
        assert attrs["status"] == "PUBLISHED"
        assert attrs["catalogName"] == "hive"
        assert attrs["schemaName"] == "revenue_metrics"
        assert attrs["domainId"] == "domain-1"
        assert attrs["domainName"] == "Finance"
        assert attrs["publishedAt"] == "2026-01-01T00:00:00Z"
        assert attrs["publishedBy"] == "admin"
        assert len(attrs["owners"]) == 1
        assert attrs["owners"][0]["name"] == "Alice"
        assert custom["visibility"] == "PRIVATE"
        assert custom["lastQueriedAt"] == "2026-02-01T00:00:00Z"
        assert custom["lastQueriedBy"] == "bob"

    def test_empty_owners(self):
        obj = {
            "name": "Empty",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPDataProduct.get_attributes(obj)
        assert result["attributes"]["owners"] == []


class TestSEPDataset:
    def test_view_attributes(self):
        obj = {
            "dataset_name": "monthly_revenue",
            "dataset_description": "Monthly revenue view",
            "view_definition": "SELECT * FROM revenue",
            "catalog_name": "hive",
            "schema_name": "revenue_metrics",
            "data_product_name": "Revenue Metrics",
            "is_materialized": False,
            "status": "PUBLISHED",
            "view_security_mode": "DEFINER",
            "definition_properties": {},
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPDataset.get_attributes(obj)
        attrs = result["attributes"]
        custom = result["custom_attributes"]

        assert attrs["name"] == "monthly_revenue"
        assert attrs["status"] == "PUBLISHED"
        assert custom["is_materialized"] is False
        assert custom["viewSecurityMode"] == "DEFINER"
        assert custom["refreshSchedule"] == ""

    def test_materialized_view_attributes(self):
        obj = {
            "dataset_name": "mv_summary",
            "dataset_description": "Materialized summary",
            "view_definition": "SELECT sum(x) FROM t",
            "catalog_name": "iceberg",
            "schema_name": "analytics",
            "data_product_name": "Analytics",
            "is_materialized": True,
            "status": "PUBLISHED",
            "view_security_mode": "DEFINER",
            "definition_properties": {
                "refresh_schedule": "0 * * * *",
                "refresh_schedule_timezone": "UTC",
            },
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPDataset.get_attributes(obj)
        custom = result["custom_attributes"]

        assert custom["is_materialized"] is True
        assert custom["refreshSchedule"] == "0 * * * *"
        assert custom["refreshScheduleTimezone"] == "UTC"


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
        assert result["attributes"]["description"] == "Revenue amount"


class TestSEPCatalog:
    def test_get_attributes(self):
        obj = {
            "catalog_name": "hive",
            "connector_id": "hive-1",
            "connector_name": "hive",
            "state": "OPERATIONAL",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPCatalog.get_attributes(obj)
        assert result["attributes"]["name"] == "hive"
        assert result["custom_attributes"]["connector_name"] == "hive"
        assert result["custom_attributes"]["state"] == "OPERATIONAL"


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
            "comment": "User email address",
            "column_default": "",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPColumn.get_attributes(obj)
        assert result["attributes"]["name"] == "email"
        assert result["attributes"]["isNullable"] is True
        assert result["attributes"]["order"] == 3
        assert result["attributes"]["description"] == "User email address"

    def test_null_comment(self):
        obj = {
            "table_catalog": "hive",
            "table_schema": "public",
            "table_name": "users",
            "column_name": "id",
            "ordinal_position": 1,
            "is_nullable": "NO",
            "data_type": "bigint",
            "comment": None,
            "column_default": "",
            "connection_qualified_name": "default/starburst/1234",
        }
        result = SEPColumn.get_attributes(obj)
        assert result["attributes"]["isNullable"] is False
        assert result["attributes"]["description"] == ""
