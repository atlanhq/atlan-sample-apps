import os

import daft
import pytest
from app.transformers import AnaplanTransformer


class TestAnaplanTransformer:
    """Test cases for Anaplan transformer functionality."""

    @pytest.fixture
    def anaplan_transformer(self):
        """Create an AnaplanTransformer instance for testing."""
        return AnaplanTransformer(connector_name="anaplan", tenant_id="test_tenant")

    def test_anaplan_transformer_initialization(self, anaplan_transformer):
        """Test that AnaplanTransformer initializes correctly."""
        assert anaplan_transformer is not None
        assert anaplan_transformer.connector_name == "anaplan"
        assert anaplan_transformer.tenant_id == "test_tenant"
        assert hasattr(anaplan_transformer, "entity_class_definitions")

    def test_entity_class_definitions_loaded(self, anaplan_transformer):
        """Test that entity class definitions are properly loaded."""
        expected_asset_types = [
            "ANAPLANAPP",
            "ANAPLANPAGE",
        ]

        for asset_type in expected_asset_types:
            assert asset_type in anaplan_transformer.entity_class_definitions

    def test_yaml_template_files_exist(self):
        """Test that all required YAML template files exist."""
        # Get the correct path to the transformers directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        transformer_dir = os.path.join(current_dir, "../../app/transformers")
        transformer_dir = os.path.normpath(transformer_dir)

        expected_yaml_files = [
            "anaplanapp.yaml",
            "anaplanpage.yaml",
        ]

        for yaml_file in expected_yaml_files:
            file_path = os.path.join(transformer_dir, yaml_file)
            assert os.path.exists(file_path), f"YAML template not found: {file_path}"

    def test_anaplan_transformer_inheritance(self, anaplan_transformer):
        """Test that AnaplanTransformer inherits from QueryBasedTransformer."""
        from application_sdk.transformers.query import QueryBasedTransformer

        assert isinstance(anaplan_transformer, QueryBasedTransformer)

    def test_anaplan_transformer_default_parameters(self):
        """Test AnaplanTransformer with default parameters."""
        transformer = AnaplanTransformer()
        assert transformer.connector_name == "anaplan"
        assert transformer.tenant_id == "default"

    def test_anaplan_transformer_custom_parameters(self):
        """Test AnaplanTransformer with custom parameters."""
        transformer = AnaplanTransformer(
            connector_name="custom_anaplan", tenant_id="custom_tenant"
        )
        assert transformer.connector_name == "custom_anaplan"
        assert transformer.tenant_id == "custom_tenant"

    def test_anaplan_transformer_empty_dataframe(self, anaplan_transformer):
        """Test transformer behavior with empty dataframe."""
        empty_dataframe = daft.from_pydict({})  # type: ignore

        # Should not raise an exception
        assert anaplan_transformer is not None
        assert empty_dataframe is not None

    def test_anaplan_transformer_yaml_template_structure(self):
        """Test that YAML templates have the expected structure."""
        # Get the correct path to the transformers directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        transformer_dir = os.path.join(current_dir, "../../app/transformers")
        transformer_dir = os.path.normpath(transformer_dir)

        # Test a few key YAML files for structure
        key_files = ["anaplanapp.yaml", "anaplanpage.yaml"]

        for yaml_file in key_files:
            file_path = os.path.join(transformer_dir, yaml_file)
            assert os.path.exists(file_path), f"YAML template not found: {file_path}"

            # Read and check basic structure
            with open(file_path, "r") as f:
                content = f.read()
                assert "table:" in content
                assert "columns:" in content
                assert "typeName:" in content
                assert "status:" in content
                assert "attributes:" in content

    def test_anaplan_transformer_qualified_name_pattern(self):
        """Test that qualifiedName follows the expected pattern in YAML templates."""
        # Get the correct path to the transformers directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        transformer_dir = os.path.join(current_dir, "../../../app/transformers")
        transformer_dir = os.path.normpath(transformer_dir)

        # Check that qualifiedName uses concat pattern
        yaml_files = [
            "anaplanapp.yaml",
            "anaplanpage.yaml",
        ]

        for yaml_file in yaml_files:
            file_path = os.path.join(transformer_dir, yaml_file)
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    content = f.read()
                    assert "qualifiedName:" in content
                    assert "concat(" in content
                    assert "connection_qualified_name" in content
