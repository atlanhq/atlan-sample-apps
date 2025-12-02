import unittest

import pytest
from application_sdk.test_utils.e2e.base import BaseTest


class TestMySQLWorkflow(unittest.TestCase, BaseTest):
    """E2E tests for MySQL metadata extraction workflow."""

    extracted_output_base_path = (
        "./local/dapr/objectstore/artifacts/apps/mysql/workflows"
    )

    @pytest.mark.order(3)
    def test_metadata(self):
        """
        Test Metadata with pattern matching instead of exact matching.
        MySQL returns dynamic data, so we check the structure rather than exact content.
        """
        response = self.client.get_metadata(
            credentials=self.test_workflow_args["credentials"]
        )

        # Check that response has the expected structure
        self.assertTrue(response.get("success"), "Response should have success=True")
        self.assertIn("data", response, "Response should have 'data' field")
        self.assertIsInstance(response["data"], list, "Data field should be a list")

    @pytest.mark.order(4)
    def test_preflight_check(self):
        """
        Test Preflight Check with pattern matching instead of exact matching.
        MySQL returns dynamic messages with table counts, so we check the structure rather than exact content.
        """
        response = self.client.preflight_check(
            credentials=self.test_workflow_args["credentials"],
            metadata=self.test_workflow_args["metadata"],
        )

        # Check that response has the expected structure
        self.assertTrue(response.get("success"), "Response should have success=True")
        self.assertIn("data", response, "Response should have 'data' field")

        # Check that data contains the expected check fields
        data = response["data"]
        expected_checks = [
            "databaseSchemaCheck",
            "tablesCheck",
        ]
        for check in expected_checks:
            self.assertIn(check, data, f"Response should have '{check}' field")
            check_data = data[check]
            self.assertIsInstance(check_data, dict, f"'{check}' should be a dictionary")
            self.assertIn(
                "success", check_data, f"'{check}' should have 'success' field"
            )
            self.assertIn(
                "successMessage",
                check_data,
                f"'{check}' should have 'successMessage' field",
            )
            self.assertIn(
                "failureMessage",
                check_data,
                f"'{check}' should have 'failureMessage' field",
            )
            # Verify success message contains expected text (may include table count)
            if check == "databaseSchemaCheck":
                self.assertIn(
                    "Schemas and Databases check successful",
                    check_data["successMessage"],
                    "Success message should contain expected text",
                )
            elif check == "tablesCheck":
                self.assertIn(
                    "Tables check successful",
                    check_data["successMessage"],
                    "Success message should contain expected text",
                )

    @pytest.mark.order(4)
    def test_run_workflow(self):
        """
        Test running the metadata extraction workflow
        """
        self.run_workflow()
