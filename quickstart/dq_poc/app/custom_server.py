from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Type

from app.workflow import DqPocWorkflow
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.server.fastapi import APIServer, HttpWorkflowTrigger
from application_sdk.workflows import WorkflowInterface
from fastapi import Body
from fastapi.routing import APIRouter
from pydantic import BaseModel

logger = get_logger(__name__)


class DqPocStartResponse(BaseModel):
    """Custom response model for the dq-poc custom endpoint."""

    workflow_id: str
    run_id: str
    message: str
    started_at: str


class DqPocServer(APIServer):
    """
    Extends the default SDK APIServer with a custom endpoint.

    - Keeps default SDK routes (including POST /workflows/v1/start)
    - Adds POST /api/v1/dq-poc that returns a custom response shape
    """

    custom_router: APIRouter = APIRouter()

    def register_routers(self):
        # Let the base class register all default routes first
        # (it calls register_routes()).
        super().register_routers()
        # Then include our custom router.
        self.app.include_router(self.custom_router, prefix="/api/v1")
        # Convenience alias (so it also works under the SDK workflow prefix).
        self.app.include_router(self.custom_router, prefix="/workflows/v1")

    def register_routes(self):
        self.custom_router.add_api_route(
            "/dq-poc",
            self.start_dq_poc,
            methods=["POST"],
            response_model=DqPocStartResponse,
            summary="Start dq-poc workflow (custom response)",
        )
        super().register_routes()

    async def start_dq_poc(
        self,
        body: Dict[str, Any] = Body(default_factory=dict),
        workflow_class: Type[WorkflowInterface] = DqPocWorkflow,
    ) -> DqPocStartResponse:
        if not self.workflow_client:
            raise RuntimeError("Temporal client not initialized")

        workflow_data = await self.workflow_client.start_workflow(
            workflow_args=body,
            workflow_class=workflow_class,
        )

        return DqPocStartResponse(
            workflow_id=workflow_data.get("workflow_id", ""),
            run_id=workflow_data.get("run_id", ""),
            message="Workflow started",
            started_at=datetime.now(timezone.utc).isoformat(),
        )

    def register_default_workflow_start(self, workflow_class: Type[WorkflowInterface]):
        """Register the standard SDK workflow trigger.

        This is the default SDK endpoint: POST /workflows/v1/start
        """
        self.register_workflow(
            workflow_class=workflow_class,
            triggers=[HttpWorkflowTrigger()],
        )
