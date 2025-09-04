import unittest

import pytest
import requests
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.test_utils.e2e.base import BaseTest
from application_sdk.test_utils.e2e.conftest import workflow_details
from temporalio.client import WorkflowExecutionStatus

logger = get_logger(__name__)


class TestAnaplanWorkflow(unittest.TestCase, BaseTest):
    """Simple E2E test for Anaplan metadata extraction workflow."""

    extracted_output_base_path = (
        "./local/dapr/objectstore/artifacts/apps/anaplan/workflows"
    )

    # Override the workflow timeout to allow for longer running workflows (up to 1 hour)
    workflow_timeout = 3600  # 3600 seconds = 1 hour

    # ============================================================================
    # PHASE 1: BASIC FUNCTIONALITY TESTS (Orders 1-4)
    # ============================================================================

    @pytest.mark.order(1)
    def test_health_check(self):
        """
        Check if the server is up and running and is responding to requests
        """
        response = requests.get(self.client.host)
        self.assertEqual(response.status_code, 200)

    @pytest.mark.order(2)
    def test_auth(self):
        """
        Test the auth and test connection flow with pattern matching
        """
        response = self.client.test_connection(
            credentials=self.test_workflow_args["credentials"]
        )

        # Check structure instead of exact content for Anaplan's dynamic responses
        self.assertTrue(response.get("success"), "Response should have success=True")
        self.assertIn("message", response, "Response should have 'message' field")

    @pytest.mark.order(3)
    def test_metadata(self):
        """
        Test Metadata with pattern matching instead of exact matching.
        Anaplan returns dynamic data, so we check the structure rather than exact content.
        """
        response = self.client.get_metadata(
            credentials=self.test_workflow_args["credentials"]
        )

        # Check that response has the expected structure
        self.assertTrue(response.get("success"), "Response should have success=True")
        self.assertIn("data", response, "Response should have 'data' field")
        self.assertIsInstance(response["data"], list, "Data field should be a list")

        # Check that data contains Anaplan assets (each item should have 'value' and 'title' fields)
        if response["data"]:
            for item in response["data"]:
                self.assertIsInstance(
                    item, dict, "Each data item should be a dictionary"
                )
                self.assertIn(
                    "value", item, "Each data item should have a 'value' field"
                )
                self.assertIn(
                    "title", item, "Each data item should have a 'title' field"
                )
                # Optional: check for children field if it exists
                if "children" in item:
                    self.assertIsInstance(
                        item["children"], list, "Children field should be a list"
                    )

    @pytest.mark.order(4)
    def test_preflight_check(self):
        """
        Test Preflight Check with pattern matching instead of exact matching.
        Anaplan returns dynamic messages, so we check the structure rather than exact content.
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
            "inputValidation",
            "authenticationCheck",
            "appPermissions",
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

    # ============================================================================
    # PHASE 2: NEGATIVE TESTS (Orders 5-9)
    # ============================================================================

    @pytest.mark.order(5)
    def test_auth_negative_invalid_credentials(self):
        """
        Test authentication with invalid credentials
        """
        invalid_credentials = {"username": "invalid", "password": "invalid"}
        try:
            # Use the proper endpoint that goes through the handler
            response = self.client._post("/workflows/v1/auth", data=invalid_credentials)
            # Either expect a non-200 status code or an error message in the response
            if response.status_code == 200:
                response_data = response.json()
                self.assertEqual(response_data["success"], False)
            else:
                self.assertNotEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            # If the request fails with an exception, the test passes
            pass

    @pytest.mark.order(6)
    def test_metadata_negative(self):
        """
        Test metadata API with invalid credentials
        """
        invalid_credentials = {"username": "invalid", "password": "invalid"}
        try:
            # Use the proper endpoint that goes through the handler
            response = self.client._post(
                "/workflows/v1/metadata", data=invalid_credentials
            )
            # Either expect a non-200 status code or an error message in the response
            if response.status_code == 200:
                response_data = response.json()
                # Check for error indicators in the response
                if response_data.get("success", True):
                    # If success is true, check for empty or error data
                    data = response_data.get("data", {})
                    self.assertTrue(
                        not data  # Empty data
                        or "error" in str(data).lower()  # Error in data
                        or "fail" in str(data).lower()  # Failure message
                        or data == {}  # Empty object
                        or isinstance(data, dict)
                        and all(
                            not v for v in data.values()
                        )  # All values are empty/falsy
                    )
            else:
                self.assertNotEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            # If the request fails with an exception, the test passes
            pass

    @pytest.mark.order(7)
    def test_metadata_with_invalid_credentials(self):
        """
        Test metadata API with invalid credentials structure
        """
        # Test with completely different credential structure
        invalid_credentials = {"api_key": "invalid_key", "region": "invalid_region"}
        try:
            # Use the proper endpoint that goes through the handler
            response = self.client._post(
                "/workflows/v1/metadata", data=invalid_credentials
            )
            if response.status_code == 200:
                response_data = response.json()
                # Check for error indicators in the response
                if response_data.get("success", True):
                    data = response_data.get("data", {})
                    self.assertTrue(
                        not data  # Empty data
                        or len(data) == 0  # Empty list/dict
                        or "error" in str(data).lower()  # Error in data
                        or "fail" in str(data).lower()  # Failure message
                    )
            else:
                self.assertNotEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            # If the request fails with an exception, the test passes
            pass

    @pytest.mark.order(8)
    def test_preflight_check_with_invalid_credentials(self):
        """
        Test preflight check with invalid credentials
        """
        invalid_credentials = {"username": "invalid", "password": "invalid"}
        try:
            response = self.client._post(
                "/workflows/v1/check",
                data={
                    "credentials": invalid_credentials,
                    "metadata": self.test_workflow_args["metadata"],
                },
            )
            if response.status_code == 200:
                response_data = response.json()
                # Check for error indicators in the response
                if response_data.get("success", True):
                    data = response_data.get("data", {})
                    self.assertTrue(
                        not data  # Empty data
                        or "error" in str(data).lower()  # Error in data
                        or "fail" in str(data).lower()  # Failure message
                        or data == {}  # Empty object
                        or isinstance(data, dict)
                        and all(
                            not v for v in data.values()
                        )  # All values are empty/falsy
                    )
            else:
                self.assertNotEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            # If the request fails with an exception, the test passes
            pass

    @pytest.mark.order(9)
    def test_run_workflow_with_invalid_credentials(self):
        """
        Test running workflow with invalid credentials
        """
        invalid_credentials = {"username": "invalid", "password": "invalid"}
        try:
            response = self.client._post(
                "/start",
                data={
                    "credentials": invalid_credentials,
                    "metadata": self.test_workflow_args["metadata"],
                    "connection": self.test_workflow_args["connection"],
                },
            )
            if response.status_code == 200:
                response_data = response.json()
                # If the API returns success=True, check for error indicators or workflow failure
                if response_data.get("success", False):
                    # If workflow started, check if it fails
                    if "data" in response_data and "workflow_id" in response_data.get(
                        "data", {}
                    ):
                        workflow_id = response_data["data"]["workflow_id"]
                        run_id = response_data["data"]["run_id"]

                        # Wait a short time for the workflow to potentially fail
                        import time

                        time.sleep(5)

                        # Check workflow status
                        try:
                            status_response = self.client.get_workflow_status(
                                workflow_id, run_id
                            )
                            # The workflow should either fail or be in a non-completed state
                            if status_response.get("success", False):
                                status = status_response.get("data", {}).get("status")
                                self.assertTrue(
                                    status != WorkflowExecutionStatus.COMPLETED.name,
                                    f"Workflow with invalid credentials unexpectedly completed successfully: {status}",
                                )
                        except Exception:
                            # If checking status fails, that's also acceptable
                            pass
                    else:
                        # If no workflow was started, check for error indicators in the response
                        self.assertTrue(
                            "error" in str(response_data).lower()
                            or "fail" in str(response_data).lower()
                            or "invalid" in str(response_data).lower()
                        )
            else:
                self.assertNotEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            # If the request fails with an exception, the test passes
            pass

    # ============================================================================
    # PHASE 3: WORKFLOW EXECUTION (Order 10)
    # ============================================================================

    @pytest.mark.order(10)
    def test_run_workflow(self):
        """
        Test running the metadata extraction workflow.
        Run the workflow completely and wait for completion.
        """
        # Run the workflow using the parent class method
        super().run_workflow()

        print("✅ Workflow test completed successfully")

    # ============================================================================
    # PHASE 4: WORKFLOW-DEPENDENT TESTS (Orders 11-13)
    # ============================================================================

    @pytest.mark.order(11)
    def test_configuration_get(self):
        """
        Test configuration retrieval - requires workflow completion.
        """
        super().test_configuration_get()

    @pytest.mark.order(12)
    def test_configuration_update(self):
        """
        Test Anaplan-specific configuration update - requires workflow completion.
        Updates metadata filters for include/exclude functionality.
        """
        update_payload = {
            "connection": self.test_workflow_args["connection"],
            "metadata": {
                **self.test_workflow_args["metadata"],
                "include-metadata": '{"app_guid_1": {"page_guid_1": {}}}',
                "exclude-metadata": '{"app_guid_2": {"page_guid_2": {}}}',
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
        # Verify that the Anaplan-specific metadata filters were updated
        self.assertEqual(
            response_data["data"]["metadata"]["include-metadata"],
            '{"app_guid_1": {"page_guid_1": {}}}',
        )
        self.assertEqual(
            response_data["data"]["metadata"]["exclude-metadata"],
            '{"app_guid_2": {"page_guid_2": {}}}',
        )

    @pytest.mark.order(13)
    def test_data_validation(self):
        """
        Test for validating the extracted source data - requires workflow completion.
        """
        self.validate_data()
