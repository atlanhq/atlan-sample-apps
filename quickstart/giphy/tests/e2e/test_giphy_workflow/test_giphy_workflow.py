import unittest

import pytest
import requests
from application_sdk.test_utils.e2e.base import BaseTest
from application_sdk.test_utils.e2e.conftest import workflow_details


class TestGiphyWorkflow(unittest.TestCase, BaseTest):
    """E2E test for Giphy workflow."""

    extracted_output_base_path = (
        "./local/dapr/objectstore/artifacts/apps/giphy/workflows"
    )

    @pytest.mark.order(1)
    def test_health_check(self):
        """Check if the server is up and running."""
        response = requests.get(self.client.host)
        self.assertEqual(response.status_code, 200)

    @pytest.mark.order(2)
    def test_auth(self):
        """Skip auth test for giphy app."""
        # Giphy app doesn't have auth endpoint
        pass

    @pytest.mark.order(3)
    def test_metadata(self):
        """Skip metadata test for giphy app."""
        # Giphy app doesn't have metadata endpoint
        pass

    @pytest.mark.order(4)
    def test_preflight_check(self):
        """Skip preflight check test for giphy app."""
        # Giphy app doesn't have preflight check endpoint
        pass

    @pytest.mark.order(5)
    def test_run_workflow(self):
        """Test running the giphy workflow."""
        super().run_workflow()

    @pytest.mark.order(6)
    def test_configuration_get(self):
        """Test configuration retrieval."""
        super().test_configuration_get()

    @pytest.mark.order(7)
    def test_configuration_update(self):
        """Test configuration update."""
        update_payload = {
            "connection": self.test_workflow_args["connection"],
            "metadata": {
                **self.test_workflow_args["metadata"],
                "search_term": "funny dog",
            },
        }
        response = requests.post(
            f"{self.client.host}/workflows/v1/config/{workflow_details[self.test_name]['workflow_id']}",
            json=update_payload,
        )
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data["success"], True)
        self.assertEqual(
            response_data["message"], "Workflow configuration updated successfully"
        )

    @pytest.mark.order(8)
    def test_data_validation(self):
        """Skip data validation test for giphy app."""
        # Giphy app doesn't perform data extraction/validation
        pass

