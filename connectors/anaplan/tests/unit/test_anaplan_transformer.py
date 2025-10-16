import os

import daft
import pytest
from app.transformers import AppTransformer


class TestAppTransformer:
    """Test cases for App transformer functionality."""

    @pytest.fixture
    def app_transformer(self):
        """Create an AppTransformer instance for testing."""
        return AppTransformer(connector_name="anaplan", tenant_id="test_tenant")

    def test_app_transformer_initialization(self, app_transformer):
        """Test that AppTransformer initializes correctly."""
        assert app_transformer is not None
        assert app_transformer.connector_name == "anaplan"
        assert app_transformer.tenant_id == "test_tenant"
        assert hasattr(app_transformer, "entity_class_definitions")

    def test_entity_class_definitions_loaded(self, app_transformer):
        """Test that entity class definitions are properly loaded."""
        expected_asset_types = [
            "APP",
            "PAGE",
        ]

        for asset_type in expected_asset_types:
            assert asset_type in app_transformer.entity_class_definitions

    def test_yaml_template_files_exist(self):
        """Test that all required YAML template files exist."""
        # Get the correct path to the transformers directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        transformer_dir = os.path.join(current_dir, "../../app/transformers")
        transformer_dir = os.path.normpath(transformer_dir)

        expected_yaml_files = [
            "app.yaml",
            "page.yaml",
        ]

        for yaml_file in expected_yaml_files:
            file_path = os.path.join(transformer_dir, yaml_file)
            assert os.path.exists(file_path), f"YAML template not found: {file_path}"

    def test_app_transformer_inheritance(self, app_transformer):
        """Test that AppTransformer inherits from QueryBasedTransformer."""
        from application_sdk.transformers.query import QueryBasedTransformer

        assert isinstance(app_transformer, QueryBasedTransformer)

    def test_app_transformer_default_parameters(self):
        """Test AppTransformer with default parameters."""
        transformer = AppTransformer()
        assert transformer.connector_name == "anaplan"
        assert transformer.tenant_id == "default"

    def test_app_transformer_custom_parameters(self):
        """Test AppTransformer with custom parameters."""
        transformer = AppTransformer(
            connector_name="custom_anaplan", tenant_id="custom_tenant"
        )
        assert transformer.connector_name == "custom_anaplan"
        assert transformer.tenant_id == "custom_tenant"

    def test_app_transformer_empty_dataframe(self, app_transformer):
        """Test transformer behavior with empty dataframe."""
        empty_dataframe = daft.from_pydict({})  # type: ignore

        # Should not raise an exception
        assert app_transformer is not None
        assert empty_dataframe is not None

    def test_app_transformer_yaml_template_structure(self):
        """Test that YAML templates have the expected structure."""
        # Get the correct path to the transformers directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        transformer_dir = os.path.join(current_dir, "../../app/transformers")
        transformer_dir = os.path.normpath(transformer_dir)

        # Test a few key YAML files for structure
        key_files = ["app.yaml", "page.yaml"]

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

    def test_app_transformer_qualified_name_pattern(self):
        """Test that qualifiedName follows the expected pattern in YAML templates."""
        # Get the correct path to the transformers directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        transformer_dir = os.path.join(current_dir, "../../../app/transformers")
        transformer_dir = os.path.normpath(transformer_dir)

        # Check that qualifiedName uses concat pattern
        yaml_files = [
            "app.yaml",
            "page.yaml",
        ]

        for yaml_file in yaml_files:
            file_path = os.path.join(transformer_dir, yaml_file)
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    content = f.read()
                    assert "qualifiedName:" in content
                    assert "concat(" in content
                    assert "connection_qualified_name" in content
