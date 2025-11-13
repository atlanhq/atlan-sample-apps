import os
import unittest

import pytest

from application_sdk.test_utils.e2e.base import BaseTest


class TestGiphyWorkflow(unittest.TestCase, BaseTest):
    """E2E tests for Giphy workflow.
    
    Giphy is a simple workflow that:
    - Takes a search_term and recipients as input
    - Fetches a GIF from Giphy API
    - Sends an email with the GIF
    - Does NOT have auth, metadata, or preflight check endpoints
    - Only has: health check, start workflow, get configuration, and workflow status
    """

    extracted_output_base_path = (
        "./local/dapr/objectstore/artifacts/apps/default/workflows"
    )

    @classmethod
    def prepare_dir_paths(cls):
        """
        Prepares directory paths for the test to pick up the configuration file.
        Overrides base method to skip schema directory check since giphy
        doesn't extract data for validation.
        """
        import inspect

        # Prepare the base directory path
        tests_dir = os.path.dirname(inspect.getfile(cls))

        # Prepare the config file path
        cls.config_file_path = f"{tests_dir}/config.yaml"
        if not os.path.exists(cls.config_file_path):
            raise FileNotFoundError(f"Config file not found: {cls.config_file_path}")

        # Set schema_base_path to tests_dir to satisfy BaseTest requirements
        # (not used for giphy since there's no data validation)
        cls.schema_base_path = f"{tests_dir}/schema"
        # Create schema directory if it doesn't exist (empty is fine)
        os.makedirs(cls.schema_base_path, exist_ok=True)

    @pytest.mark.order(1)
    def test_health_check(self):
        """
        Check if the server is up and running and is responding to requests
        """
        import requests

        # Check server health endpoint
        response = requests.get(f"{self.client.host}/server/health")
        self.assertEqual(response.status_code, 200)

    @pytest.mark.order(2)
    def test_run_workflow(self):
        """
        Test running the giphy workflow
        """
        self.run_workflow()

    @pytest.mark.order(3)
    def test_configuration_get(self):
        """
        Test configuration retrieval
        """
        from application_sdk.test_utils.e2e.conftest import workflow_details

        response = self.client._get(
            f"/config/{workflow_details[self.test_name]['workflow_id']}"
        )
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data["success"], True)
        self.assertEqual(
            response_data["message"], "Workflow configuration fetched successfully"
        )

        # Verify that response data contains the expected search_term and recipients
        self.assertEqual(
            response_data["data"]["search_term"], self.test_workflow_args["search_term"]
        )
        self.assertEqual(
            response_data["data"]["recipients"], self.test_workflow_args["recipients"]
        )

    # Override BaseTest methods that don't apply to giphy - all skipped
    @pytest.mark.skip(reason="Giphy workflow doesn't have auth endpoint")
    def test_auth(self):
        """Skip - giphy doesn't have authentication."""
        pass

    @pytest.mark.skip(reason="Giphy workflow doesn't have metadata endpoint")
    def test_metadata(self):
        """Skip - giphy doesn't have metadata endpoint."""
        pass

    @pytest.mark.order(4)
    @pytest.mark.skip(reason="Giphy workflow doesn't have preflight check endpoint")
    def test_preflight_check(self):
        """Skip - giphy doesn't have preflight check."""
        pass

    @pytest.mark.order(6)
    @pytest.mark.skip(reason="Giphy workflow doesn't have metadata for configuration update")
    def test_configuration_update(self):
        """Skip - giphy doesn't have metadata for updates."""
        pass

    @pytest.mark.order(7)
    @pytest.mark.skip(reason="Giphy workflow doesn't extract data for validation")
    def test_data_validation(self):
        """Skip - giphy doesn't extract data."""
        pass

    @pytest.mark.order(8)
    @pytest.mark.skip(reason="Giphy workflow doesn't have auth endpoint")
    def test_auth_negative_invalid_credentials(self):
        """Skip - giphy doesn't have auth endpoint."""
        pass

    @pytest.mark.order(9)
    @pytest.mark.skip(reason="Giphy workflow doesn't have metadata endpoint")
    def test_metadata_negative(self):
        """Skip - giphy doesn't have metadata endpoint."""
        pass

    @pytest.mark.order(13)
    @pytest.mark.skip(reason="Giphy workflow doesn't have metadata endpoint")
    def test_metadata_with_invalid_credentials(self):
        """Skip - giphy doesn't have metadata endpoint."""
        pass

    @pytest.mark.order(14)
    @pytest.mark.skip(reason="Giphy workflow doesn't have preflight check endpoint")
    def test_preflight_check_with_invalid_credentials(self):
        """Skip - giphy doesn't have preflight check."""
        pass

    @pytest.mark.order(15)
    @pytest.mark.skip(reason="Giphy workflow doesn't require credentials/metadata")
    def test_run_workflow_with_invalid_credentials(self):
        """Skip - giphy doesn't require credentials."""
        pass

