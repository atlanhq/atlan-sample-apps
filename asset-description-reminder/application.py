from application_sdk.server.fastapi import APIServer, HttpWorkflowTrigger  
from application_sdk.clients.workflow import WorkflowClient
from application_sdk.clients.utils import get_workflow_client
from application_sdk.worker import Worker
from application_sdk.constants import APPLICATION_NAME
from workflows.description_reminder_workflow import AssetDescriptionReminderWorkflow  
from activities.description_reminder_activities import AssetDescriptionReminderActivities  
from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

# --- Request Models ---
class WorkflowRequest(BaseModel):
    user_username: str

class AssetDescriptionReminderApplication:  
    def __init__(self, name: str = "asset-description-reminder"):  
        self.name = name
        self.workflow_client = None
        self.api_server = None
        self.worker = None
        self.activities = None
        self.custom_router = APIRouter()
          
    async def setup_reminder_workflow(self):  
        """Setup the asset description reminder workflow client"""  
        self.workflow_client = get_workflow_client(application_name=self.name)
        await self.workflow_client.load()
        self.activities = AssetDescriptionReminderActivities()
          
    async def setup_api_server(self):  
        """Setup FastAPI server with HTTP triggers"""  
        if not self.workflow_client:
            raise RuntimeError("Workflow client not initialized. Call setup_reminder_workflow() first.")
            
        self.api_server = APIServer(
            workflow_client=self.workflow_client
        )
          
        # Register the workflow with a standard HTTP trigger
        self.api_server.register_workflow(  
            workflow_class=AssetDescriptionReminderWorkflow,  
            triggers=[HttpWorkflowTrigger(endpoint="/start", methods=["POST"])]  
        )
        
        # Register custom routes for frontend and user management
        await self._setup_additional_routes()
        self.api_server.app.include_router(self.custom_router)
        
    async def _setup_additional_routes(self):
        """Setup additional routes for user management and frontend"""
        # Mount static files
        static_path = os.path.join(os.path.dirname(__file__), "frontend", "static")
        if os.path.exists(static_path):
            self.api_server.app.mount("/static", StaticFiles(directory=static_path), name="static")
        
        # Frontend route
        @self.custom_router.get("/", response_class=HTMLResponse)
        async def frontend():
            """Serve the frontend interface"""
            frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "templates", "index.html")
            if os.path.exists(frontend_path):
                with open(frontend_path, "r") as f:
                    return HTMLResponse(content=f.read())
            return HTMLResponse("<h1>Asset Description Reminder</h1><p>Frontend not found</p>")
        
        # API route to get tenant users
        @self.custom_router.get("/api/v1/users")
        async def get_tenant_users():
            """Get list of users in the tenant"""
            try:
                users = await self.activities.get_tenant_users()
                return JSONResponse(content={"users": users})
            except Exception as e:
                return JSONResponse(content={"error": str(e)}, status_code=500)
        
    async def setup_worker(self):
        """Setup the Temporal worker"""
        if not self.workflow_client or not self.activities:
            raise RuntimeError("Workflow client and activities must be initialized first.")
            
        self.worker = Worker(
            workflow_client=self.workflow_client,
            workflow_classes=[AssetDescriptionReminderWorkflow],
            workflow_activities=AssetDescriptionReminderWorkflow.get_activities(self.activities),
        )
    
    async def start_worker(self, daemon: bool = False):
        """Start the Temporal worker"""
        if not self.worker:
            await self.setup_worker()
        await self.worker.start(daemon=daemon)
        
    async def start_server(self, port: int = 8001):
        """Start the FastAPI server"""
        if not self.api_server:
            raise RuntimeError("API server not initialized. Call setup_api_server() first.")
        await self.api_server.start(port=port)
        
    async def start_workflow(self, workflow_args: dict, workflow_class):
        """Start a workflow execution"""
        if not self.workflow_client:
            raise RuntimeError("Workflow client not initialized. Call setup_reminder_workflow() first.")
        return await self.workflow_client.start_workflow(
            workflow_args=workflow_args,
            workflow_class=workflow_class
        ) 