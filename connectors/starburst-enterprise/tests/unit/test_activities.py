"""
Unit tests for Starburst Enterprise metadata extraction activities.
"""

import pytest

from app.activities import SEPMetadataExtractionActivities


class TestSEPActivities:
    @pytest.fixture
    def activities(self) -> SEPMetadataExtractionActivities:
        return SEPMetadataExtractionActivities()

    def test_load_sql_extract_catalog(self, activities: SEPMetadataExtractionActivities):
        """Test that SQL template files can be loaded."""
        sql = activities._load_sql("extract_catalog.sql")
        assert "catalog_name" in sql
        assert "system.metadata.catalogs" in sql

    def test_load_sql_test_auth(self, activities: SEPMetadataExtractionActivities):
        sql = activities._load_sql("test_authentication.sql")
        assert "SELECT 1" in sql

    def test_build_rest_client(self, activities: SEPMetadataExtractionActivities):
        """Test REST client construction from workflow args."""
        workflow_args = {
            "credentials": {
                "host": "sep.example.com",
                "port": 8080,
                "username": "admin",
                "password": "secret",
                "http_scheme": "https",
                "role": "sysadmin",
            }
        }
        client = activities._build_rest_client(workflow_args)
        assert client.base_url == "https://sep.example.com:8080"
        assert "Authorization" in client.headers
