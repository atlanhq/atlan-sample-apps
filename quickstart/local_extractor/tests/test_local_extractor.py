import json
import os
import tempfile

import pytest
from app.activities import ActivitiesClass


class TestLocalExtractor:
    @pytest.fixture()
    def activities(self) -> ActivitiesClass:
        return ActivitiesClass()

    @pytest.fixture()
    def sample_input_data(self) -> list[dict]:
        """Sample input data matching the expected format."""
        return [
            {
                "Type": "Table",
                "Name": "test_table",
                "Display_Name": "Test Table",
                "Description": "A test table",
                "User_Description": "User provided description",
                "Owner_Users": "user1\nuser2",  # newline separated list of users
                "Owner_Groups": "group1\ngroup2",  # newline separated list of groups
                "Certificate_Status": "VERIFIED",
                "Schema_Name": "public",
                "Database_Name": "test_db",
            },
            {
                "Type": "View",  # Should be filtered out
                "Name": "test_view",
                "Display_Name": "Test View",
            },
            {
                "Type": "Table",
                "Name": "another_table",
                "Display_Name": "Another Table",
                "Description": "Another test table",
                "User_Description": "",
                "Owner_Users": "",  # Empty owner users
                "Owner_Groups": "",  # Empty owner groups
                "Certificate_Status": "DRAFT",
                "Schema_Name": "schema1",
                "Database_Name": "db1",
            },
        ]

    @pytest.fixture()
    def temp_input_file(self, sample_input_data) -> str:
        """Create a temporary input file with sample data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_input_data, f, indent=2)
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture()
    def temp_output_file(self) -> str:
        """Create a temporary output file path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name
        # Remove the file so it can be created by the activity
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @staticmethod
    @pytest.mark.asyncio
    async def test_extract_and_transform_metadata_success(
        activities: ActivitiesClass,
        temp_input_file: str,
        temp_output_file: str,
    ) -> None:
        """Test successful extraction and transformation of metadata."""
        config = {
            "input_file": temp_input_file,
            "output_file": temp_output_file,
        }

        result = await activities.extract_and_transform_metadata(config)

        assert result["status"] == "success"
        assert result["records_processed"] == 2  # Only Table types

        # Verify output file was created and contains correct data
        assert os.path.exists(temp_output_file)

        # Read and verify output
        with open(temp_output_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            assert len(lines) == 2

            # Parse first record
            first_record = json.loads(lines[0])
            assert first_record["typeName"] == "Table"
            assert first_record["name"] == "test_table"
            assert first_record["displayName"] == "Test Table"
            assert first_record["description"] == "A test table"
            assert first_record["userDescription"] == "User provided description"
            assert first_record["ownerUsers"] == ["user1", "user2"]
            assert first_record["ownerGroups"] == ["group1", "group2"]
            assert first_record["certificateStatus"] == "VERIFIED"
            assert first_record["schemaName"] == "public"
            assert first_record["databaseName"] == "test_db"

            # Parse second record
            second_record = json.loads(lines[1])
            assert second_record["typeName"] == "Table"
            assert second_record["name"] == "another_table"
            assert second_record["ownerUsers"] == []
            assert second_record["ownerGroups"] == []
            assert second_record["certificateStatus"] == "DRAFT"
            assert second_record["schemaName"] == "schema1"
            assert second_record["databaseName"] == "db1"
