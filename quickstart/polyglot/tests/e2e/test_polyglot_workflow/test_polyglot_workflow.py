import math
import os
import unittest

import pytest
from application_sdk.test_utils.e2e.base import BaseTest


class TestPolyglotWorkflow(unittest.TestCase, BaseTest):
    """E2E tests for Polyglot workflow.

    Polyglot is a simple workflow that:
    - Takes a number as input
    - Calculates factorial using Java code from Python via JPype
    - Saves the result to JSON
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
        Overrides base method to skip schema directory check since polyglot
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
        # (not used for polyglot since there's no data validation)
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
        Test running the polyglot workflow
        """
        self.run_workflow()

    @pytest.mark.order(3)
    @pytest.mark.asyncio
    async def test_configuration_get(self):
        """
        Test configuration retrieval
        """
        from application_sdk.test_utils.e2e.conftest import workflow_details

        # Ensure workflow has been run (in case test is run individually)
        if self.test_name not in workflow_details:
            self.run_workflow()

        response = self.client._get(
            f"/config/{workflow_details[self.test_name]['workflow_id']}"
        )
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data["success"], True)
        self.assertEqual(
            response_data["message"], "Workflow configuration fetched successfully"
        )

        # Verify that response data contains the expected number
        self.assertEqual(
            response_data["data"]["number"], self.test_workflow_args["number"]
        )

        # Get workflow result to verify factorial calculation
        # Since the API result endpoint may not be available, we'll get the result
        # directly from Temporal after run_workflow() completes
        workflow_id = workflow_details[self.test_name]["workflow_id"]

        # Get result from Temporal client (run_workflow already waits for completion)
        from app.workflow import PolyglotWorkflow
        from application_sdk.test_utils.e2e.conftest import temporal_client

        # Get workflow result from Temporal
        workflow_handle = temporal_client.get_workflow_handle(
            workflow_id, workflow_type=PolyglotWorkflow
        )
        workflow_result = await workflow_handle.result()

        # Verify the overall workflow status
        self.assertEqual(
            workflow_result.get("status"),
            "success",
            "Workflow status should be 'success'",
        )

        # Verify calculation_result structure
        calculation_result = workflow_result.get("calculation_result", {})
        self.assertIsInstance(
            calculation_result, dict, "calculation_result should be a dictionary"
        )

        input_number = calculation_result.get("input")
        factorial_result = calculation_result.get("result")
        success = calculation_result.get("success", False)
        output_path = calculation_result.get("output_path")

        # Assert calculation was successful
        self.assertTrue(success, "Factorial calculation should succeed")
        self.assertEqual(
            input_number,
            self.test_workflow_args["number"],
            f"Input number should match test input: {self.test_workflow_args['number']}",
        )
        self.assertIsNotNone(
            factorial_result,
            "Factorial result should not be None",
        )
        self.assertIsNotNone(
            output_path,
            "Output path should be present in calculation_result",
        )
        self.assertIsInstance(output_path, str, "Output path should be a string")

        # Calculate expected factorial using math.factorial
        expected_factorial = math.factorial(input_number)

        # Assert factorial result is correct
        self.assertEqual(
            factorial_result,
            expected_factorial,
            f"Factorial of {input_number} should be {expected_factorial}, but got {factorial_result}",
        )

        # Verify save_stats structure
        save_stats = workflow_result.get("save_stats", {})
        self.assertIsInstance(save_stats, dict, "save_stats should be a dictionary")
        self.assertTrue(
            save_stats.get("success", False),
            "Save operation should be successful",
        )
        self.assertIn(
            "file_path",
            save_stats,
            "save_stats should contain 'file_path'",
        )
        self.assertIn(
            "record_count",
            save_stats,
            "save_stats should contain 'record_count'",
        )
        self.assertIn(
            "chunk_count",
            save_stats,
            "save_stats should contain 'chunk_count'",
        )
        self.assertIsInstance(
            save_stats.get("record_count"),
            int,
            "record_count should be an integer",
        )
        self.assertGreater(
            save_stats.get("record_count", 0),
            0,
            "record_count should be greater than 0",
        )

    # Override BaseTest methods that don't apply to polyglot - all skipped
    @pytest.mark.skip(reason="Polyglot workflow doesn't have auth endpoint")
    def test_auth(self):
        """Skip - polyglot doesn't have authentication."""
        pass

    @pytest.mark.skip(reason="Polyglot workflow doesn't have metadata endpoint")
    def test_metadata(self):
        """Skip - polyglot doesn't have metadata endpoint."""
        pass

    @pytest.mark.order(4)
    @pytest.mark.skip(reason="Polyglot workflow doesn't have preflight check endpoint")
    def test_preflight_check(self):
        """Skip - polyglot doesn't have preflight check."""
        pass

    @pytest.mark.order(6)
    @pytest.mark.skip(
        reason="Polyglot workflow doesn't have metadata for configuration update"
    )
    def test_configuration_update(self):
        """Skip - polyglot doesn't have metadata for updates."""
        pass

    @pytest.mark.order(7)
    @pytest.mark.skip(reason="Polyglot workflow doesn't extract data for validation")
    def test_data_validation(self):
        """Skip - polyglot doesn't extract data."""
        pass

    @pytest.mark.order(8)
    @pytest.mark.skip(reason="Polyglot workflow doesn't have auth endpoint")
    def test_auth_negative_invalid_credentials(self):
        """Skip - polyglot doesn't have auth endpoint."""
        pass

    @pytest.mark.order(9)
    @pytest.mark.skip(reason="Polyglot workflow doesn't have metadata endpoint")
    def test_metadata_negative(self):
        """Skip - polyglot doesn't have metadata endpoint."""
        pass

    @pytest.mark.order(13)
    @pytest.mark.skip(reason="Polyglot workflow doesn't have metadata endpoint")
    def test_metadata_with_invalid_credentials(self):
        """Skip - polyglot doesn't have metadata endpoint."""
        pass

    @pytest.mark.order(14)
    @pytest.mark.skip(reason="Polyglot workflow doesn't have preflight check endpoint")
    def test_preflight_check_with_invalid_credentials(self):
        """Skip - polyglot doesn't have preflight check."""
        pass

    @pytest.mark.order(15)
    @pytest.mark.skip(reason="Polyglot workflow doesn't require credentials/metadata")
    def test_run_workflow_with_invalid_credentials(self):
        """Skip - polyglot doesn't require credentials."""
        pass
