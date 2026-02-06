import os
import unittest

import pytest
from application_sdk.test_utils.e2e.base import BaseTest


class TestIncidentDigestWorkflow(unittest.TestCase, BaseTest):
    """E2E tests for the Incident Priority Digest workflow.

    This workflow:
    - Takes records_json as input
    - Writes raw/incidents and transformed/digest outputs
    - Does NOT have auth, metadata, or preflight check endpoints
    """

    extracted_output_base_path = (
        "./local/dapr/objectstore/artifacts/apps/default/workflows"
    )

    @classmethod
    def prepare_dir_paths(cls):
        import inspect

        tests_dir = os.path.dirname(inspect.getfile(cls))
        cls.config_file_path = f"{tests_dir}/config.yaml"
        if not os.path.exists(cls.config_file_path):
            raise FileNotFoundError(f"Config file not found: {cls.config_file_path}")

        cls.schema_base_path = f"{tests_dir}/schema"
        os.makedirs(cls.schema_base_path, exist_ok=True)

    @pytest.mark.order(1)
    def test_health_check(self):
        """Check if the server is up and responding."""
        import requests

        response = requests.get(f"{self.client.host}/server/health")
        self.assertEqual(response.status_code, 200)

    @pytest.mark.order(2)
    def test_run_workflow(self):
        """Test running the incident digest workflow."""
        self.run_workflow()

    @pytest.mark.order(3)
    def test_configuration_get(self):
        """Test configuration retrieval."""
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

        self.assertEqual(
            response_data["data"]["connection"],
            self.test_workflow_args["connection"],
        )

    # Skip endpoints that don't apply to this workflow
    @pytest.mark.skip(reason="Incident digest doesn't have auth endpoint")
    def test_auth(self):
        pass

    @pytest.mark.skip(reason="Incident digest doesn't have metadata endpoint")
    def test_metadata(self):
        pass

    @pytest.mark.order(4)
    @pytest.mark.skip(reason="Incident digest doesn't have preflight check endpoint")
    def test_preflight_check(self):
        pass

    @pytest.mark.order(6)
    @pytest.mark.skip(reason="Incident digest doesn't have configuration update")
    def test_configuration_update(self):
        pass

    @pytest.mark.order(7)
    @pytest.mark.skip(reason="Incident digest doesn't extract typed data for validation")
    def test_data_validation(self):
        pass

    @pytest.mark.order(8)
    @pytest.mark.skip(reason="Incident digest doesn't have auth endpoint")
    def test_auth_negative_invalid_credentials(self):
        pass

    @pytest.mark.order(9)
    @pytest.mark.skip(reason="Incident digest doesn't have metadata endpoint")
    def test_metadata_negative(self):
        pass

    @pytest.mark.order(13)
    @pytest.mark.skip(reason="Incident digest doesn't have metadata endpoint")
    def test_metadata_with_invalid_credentials(self):
        pass

    @pytest.mark.order(14)
    @pytest.mark.skip(reason="Incident digest doesn't have preflight check endpoint")
    def test_preflight_check_with_invalid_credentials(self):
        pass

    @pytest.mark.order(15)
    @pytest.mark.skip(reason="Incident digest doesn't require credentials")
    def test_run_workflow_with_invalid_credentials(self):
        pass
