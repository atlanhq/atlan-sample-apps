import asyncio
from typing import Any, Dict

from app.activities import GiphyActivities
from app.workflow import GiphyWorkflow
from application_sdk.application import BaseApplication
from application_sdk.observability.decorators.observability_decorator import (
    observability,
)
from application_sdk.observability.logger_adaptor import get_logger
from application_sdk.observability.metrics_adaptor import get_metrics
from application_sdk.observability.traces_adaptor import get_traces

APPLICATION_NAME = "giphy"

logger = get_logger(__name__)
metrics = get_metrics()
traces = get_traces()


@observability(logger=logger, metrics=metrics, traces=traces)
async def main(daemon: bool = True, enable_mcp: bool = False) -> Dict[str, Any]:
    logger.info("Starting giphy application")

    # initialize application with MCP support
    app = BaseApplication(name=APPLICATION_NAME, enable_mcp=enable_mcp)

    # setup workflow
    await app.setup_workflow(
        workflow_and_activities_classes=[(GiphyWorkflow, GiphyActivities)],
        passthrough_modules=["requests", "urllib3"],
    )

    # start worker
    await app.start_worker()

    # Setup FastAPI server (automatically mounts MCP if enable_mcp=True)
    await app.setup_server(workflow_class=GiphyWorkflow)

    # Start the server (FastAPI + MCP mounted at /mcp if enabled)
    await app.start_server()


if __name__ == "__main__":
    import os
    
    # Load .env file if it exists (for local development)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not installed, that's okay
    
    # Check for MCP enable flag (environment variable only)
    enable_mcp = os.getenv("ENABLE_MCP", "false").lower() in ["true", "1", "yes"]
    
    print("Starting Atlan Giphy App")
    print("FastAPI Server: http://localhost:8000")
    
    if enable_mcp:
        print("MCP Integration: ENABLED")
        print("   • Activities with @mcp_tool will be auto-exposed")
        print("   • MCP endpoint: http://localhost:8000/mcp")
        print("   • Available tools: fetch_gif, send_email")
        print("   • Debug with MCP Inspector using streamable HTTP")
        print("   • For Claude Desktop: Use npx mcp-remote http://localhost:8000/mcp")
    else:
        print("MCP Integration: DISABLED")
        print("To enable AI tools:")
        print("   • ENABLE_MCP=true python main.py")
        print("   • Or create .env file with: ENABLE_MCP=true")
    
    asyncio.run(main(daemon=False, enable_mcp=enable_mcp))
