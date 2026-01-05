from __future__ import annotations

from typing import Any, Dict

from app.models import DqPocRequest
from app.workflow import DqPocWorkflow
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.server.fastapi import APIServer

logger = get_logger(__name__)


async def start_dq_poc(
    *,
    server: APIServer,
    body: DqPocRequest,
) -> Dict[str, Any]:
    """
    Start the dq_poc workflow via the SDK WorkflowClient and return a custom
    response.
    """
    if not server.workflow_client:
        raise RuntimeError("Temporal client not initialized")

    workflow_args: Dict[str, Any] = body.model_dump(by_alias=True)
    workflow_data = await server.workflow_client.start_workflow(
        workflow_args=workflow_args,
        workflow_class=DqPocWorkflow,
    )
    logger.info(f"Workflow data is as follows: {workflow_data}")
    # Wait for the workflow to finish and return its result (activity's dummy
    # dict).
    handle = workflow_data.get("handle")
    if handle is None:
        raise RuntimeError("Workflow handle missing; cannot fetch result")

    return await handle.result()


# End of file
