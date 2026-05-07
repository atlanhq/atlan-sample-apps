"""Fixtures for Generic Connector integration tests.

Tests connect to an external Temporal dev server.
Secret/state/storage infrastructure is mocked — no Dapr required.

Environment variables:
    TEMPORAL_HOST: Temporal server address (default: ``localhost:7233``).

Run tests with: uv run pytest tests/integration/ -v
Requires: temporal server start-dev
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio

# Trigger GenericConnector app registration before create_worker is called.
from app.connector import GenericConnector
from application_sdk.execution._temporal.backend import TemporalExecutorBackend
from application_sdk.execution._temporal.converter import create_data_converter_for_app
from application_sdk.execution._temporal.worker import create_worker
from application_sdk.infrastructure.context import (
    InfrastructureContext,
    set_infrastructure,
)
from application_sdk.observability.observability import AtlanObservability
from application_sdk.storage import create_local_store, create_memory_store
from application_sdk.testing.mocks import MockSecretStore, MockStateStore
from temporalio.client import Client

# Pre-wire a memory store so periodic observability flush does not spam warnings.
AtlanObservability._deployment_store = create_memory_store()

_TASK_QUEUE = "generic-queue"
_TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
_temporal_reachable: bool | None = None


class AppExecutor:
    """Thin wrapper around TemporalExecutorBackend for integration tests."""

    def __init__(self, backend: TemporalExecutorBackend) -> None:
        self._backend = backend

    async def execute_app(
        self,
        app_cls: Any,
        input_data: Any,
        *,
        execution_id_prefix: str = "",
    ) -> Any:
        from application_sdk.app.context import AppContext
        from application_sdk.execution.retry import RetryPolicy

        app_name = getattr(app_cls, "_app_name", execution_id_prefix or "app")
        context = AppContext(
            app_name=app_name,
            app_version="0.0.0",
            run_id=execution_id_prefix or app_name,
        )
        return await self._backend.execute(
            app_cls,
            input_data,
            context=context,
            retry_policy=RetryPolicy(),
        )


@pytest.fixture(scope="session")
def store_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("sdk-store")


@pytest.fixture(scope="session")
def infrastructure(store_root: Path) -> InfrastructureContext:
    ctx = InfrastructureContext(
        state_store=MockStateStore(),
        secret_store=MockSecretStore({}),
        storage=create_local_store(store_root),
    )
    set_infrastructure(ctx)
    return ctx


def _check_temporal_reachable(host: str) -> bool:
    async def _probe() -> bool:
        try:
            client = await Client.connect(host, lazy=True)
            handle = client.get_workflow_handle("__connectivity_probe__")
            await asyncio.wait_for(handle.describe(), timeout=3.0)
            return True
        except TimeoutError:
            return False
        except Exception:
            return True

    return asyncio.run(_probe())


@pytest.fixture(autouse=True, scope="session")
def require_temporal() -> None:
    """Skip all integration tests if Temporal is not reachable."""
    global _temporal_reachable
    if _temporal_reachable is None:
        _temporal_reachable = _check_temporal_reachable(_TEMPORAL_HOST)
    if not _temporal_reachable:
        pytest.skip(
            f"Temporal server not running at {_TEMPORAL_HOST} — "
            "start it with: temporal server start-dev"
        )


@pytest_asyncio.fixture(scope="session")
async def temporal_client() -> Client:
    data_converter = create_data_converter_for_app(GenericConnector)
    return await Client.connect(_TEMPORAL_HOST, data_converter=data_converter)


@pytest_asyncio.fixture(scope="session")
async def generic_worker(
    temporal_client: Client,
    infrastructure: InfrastructureContext,
) -> Any:
    w = create_worker(temporal_client, task_queue=_TASK_QUEUE)
    async with w:
        yield


@pytest.fixture(scope="session")
def generic_executor(
    temporal_client: Client,
    generic_worker: Any,
) -> AppExecutor:
    backend = TemporalExecutorBackend(
        client=temporal_client,
        task_queue=_TASK_QUEUE,
    )
    return AppExecutor(backend=backend)
