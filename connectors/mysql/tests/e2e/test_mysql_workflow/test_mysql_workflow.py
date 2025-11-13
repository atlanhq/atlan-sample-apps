import unittest

from application_sdk.test_utils.e2e.base import BaseTest


class TestMySQLWorkflow(unittest.TestCase, BaseTest):
    """E2E tests for MySQL metadata extraction workflow."""

    extracted_output_base_path = (
        "./local/dapr/objectstore/artifacts/apps/mysql/workflows"
    )
