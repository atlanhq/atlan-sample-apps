"""Integration tests for the Generic Connector.

Tests the full workflow through Temporal with mock infrastructure.
No Dapr required — storage and secrets are mocked.

Requires:
    - temporal server start-dev

Run with:
    uv run pytest tests/integration/ -v
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from app.connector import GenericConnector
from app.contracts import GenericConnectorInput, GenericConnectorOutput

from application_sdk.contracts.types import ConnectionRef

if TYPE_CHECKING:
    from tests.integration.conftest import AppExecutor

CONNECTION_NAME = "test-generic-integration"
CONNECTION_QN = f"default/generic/{CONNECTION_NAME}"


class TestGenericConnectorWorkflow:
    """Full workflow execution tests.

    A class-scoped fixture runs the workflow once and shares the result
    across all tests to avoid redundant Temporal round-trips.
    """

    @pytest.fixture(scope="class")
    async def workflow_result(
        self, generic_executor: AppExecutor
    ) -> GenericConnectorOutput:
        return await generic_executor.execute_app(
            GenericConnector,
            GenericConnectorInput(
                connection=ConnectionRef.model_validate(
                    {
                        "typeName": "Connection",
                        "attributes": {
                            "qualifiedName": CONNECTION_QN,
                            "name": CONNECTION_NAME,
                        },
                    }
                ),
                source="https://example.com/data",
                load_to_atlan=False,
            ),
            execution_id_prefix="test-generic",
        )

    async def test_workflow_completes(
        self, workflow_result: GenericConnectorOutput
    ) -> None:
        assert workflow_result is not None

    async def test_connection_qualified_name(
        self, workflow_result: GenericConnectorOutput
    ) -> None:
        assert workflow_result.connection_qualified_name == CONNECTION_QN

    async def test_no_atlan_loading(
        self, workflow_result: GenericConnectorOutput
    ) -> None:
        """No Atlan loading should occur when load_to_atlan=False."""
        assert workflow_result.atlan_loaded_count == 0
