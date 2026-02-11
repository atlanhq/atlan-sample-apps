"""
End-to-end tests for Starburst Enterprise metadata extraction workflow.
"""

import unittest

import pytest
from application_sdk.test_utils.e2e.base import BaseTest


class TestSEPWorkflow(unittest.TestCase, BaseTest):
    """E2E tests for SEP hybrid metadata extraction workflow."""

    extracted_output_base_path = (
        "./local/dapr/objectstore/artifacts/apps/starburst-enterprise/workflows"
    )

    @pytest.mark.order(1)
    def test_health_check(self):
        """Server availability check."""
        import requests

        response = requests.get(f"{self.client.host}/server/health")
        self.assertEqual(response.status_code, 200)

    @pytest.mark.order(2)
    def test_auth(self):
        """Test REST + SQL authentication."""
        response = self.client.auth(
            credentials=self.test_workflow_args["credentials"]
        )
        self.assertTrue(response.get("success"), "Auth should succeed")

    @pytest.mark.order(3)
    def test_metadata(self):
        """Test metadata retrieval (catalog/schema listing)."""
        response = self.client.get_metadata(
            credentials=self.test_workflow_args["credentials"]
        )
        self.assertTrue(response.get("success"), "Metadata fetch should succeed")
        self.assertIn("data", response)
        self.assertIsInstance(response["data"], list)

    @pytest.mark.order(4)
    def test_preflight_check(self):
        """Test preflight check for REST + SQL connectivity."""
        response = self.client.preflight_check(
            credentials=self.test_workflow_args["credentials"],
            metadata=self.test_workflow_args.get("metadata", {}),
        )
        self.assertTrue(response.get("success"), "Preflight check should succeed")
        data = response.get("data", {})
        self.assertIn("domainsCheck", data)
        self.assertIn("catalogsCheck", data)

    @pytest.mark.order(5)
    def test_run_workflow(self):
        """Execute the full hybrid extraction workflow."""
        self.run_workflow()
