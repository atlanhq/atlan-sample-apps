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

    # Setup FastAPI server (always - for web UI, docs, health checks)
    await app.setup_server(workflow_class=GiphyWorkflow)

    # Setup MCP server if enabled
    if enable_mcp:
        logger.info("🤖 Starting in MCP mode for AI agents")
        await app.setup_mcp_server(mcp_name="Atlan Giphy App")
        await app.start_mcp_server()  # Takes control of process for MCP
    else:
        # Start FastAPI server for web UI
        logger.info("🌐 Starting web server for human interface")
        await app.start_server()


if __name__ == "__main__":
    import sys
    
    # Check for MCP enable flag
    enable_mcp = "--mcp" in sys.argv or "--enable-mcp" in sys.argv
    
    print("🚀 Starting Atlan Giphy App")
    
    if enable_mcp:
        print("🤖 MCP Mode: AI agents can use giphy tools")
        print("✨ Activities with @mcp_tool decorators will be exposed")
        print("📋 Available MCP tools: fetch_gif, send_email") 
        print("🔌 Install in Claude: mcp install main.py --name 'Atlan Giphy' --args '--mcp'")
    else:
        print("🌐 Web Mode: FastAPI server with web UI")
        print("🔗 Access web UI at http://localhost:8000")
        print("💡 For AI integration, run: python main.py --mcp")
    
    asyncio.run(main(daemon=False, enable_mcp=enable_mcp))
