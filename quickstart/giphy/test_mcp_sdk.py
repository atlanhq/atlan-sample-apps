#!/usr/bin/env python3
"""
Test the SDK MCP integration without needing full infrastructure.

This tests that our @mcp_tool decorators are being discovered correctly
by the Application SDK.
"""

import asyncio
from app.activities import GiphyActivities
from app.workflow import GiphyWorkflow
from application_sdk.application import BaseApplication
from application_sdk.observability.logger_adaptor import get_logger

logger = get_logger(__name__)


async def test_mcp_discovery():
    """Test that MCP discovery works without full infrastructure."""
    print("🧪 Testing SDK MCP Integration")
    print("=" * 50)
    
    try:
        # Create app with MCP enabled
        app = BaseApplication(name="giphy-test", enable_mcp=True)
        
        # Store workflow classes manually (simulating setup_workflow)
        app._workflow_and_activities_classes = [(GiphyWorkflow, GiphyActivities)]
        
        # Test MCP server setup
        await app.setup_mcp_server(mcp_name="Test Giphy MCP")
        
        if app.mcp_server:
            print("✅ MCP server created successfully")
            print(f"📋 Registered tools: {len(app.mcp_server.registered_tools)}")
            
            for tool in app.mcp_server.registered_tools:
                print(f"   • {tool['name']}: {tool['description']}")
                
            print("\n📋 Testing tool discovery:")
            
            # Check if our decorated activities were discovered
            tools = app.mcp_server.registered_tools
            tool_names = [tool['name'] for tool in tools]
            
            if 'fetch_gif' in tool_names:
                print("✅ fetch_gif activity discovered and registered")
            else:
                print("❌ fetch_gif activity not found")
                
            if 'send_email' in tool_names:
                print("✅ send_email activity discovered and registered") 
            else:
                print("❌ send_email activity not found")
                
            if 'get_workflow_args' in tool_names:
                print("⚠️  get_workflow_args was exposed (should be excluded)")
            else:
                print("✅ get_workflow_args correctly excluded (no @mcp_tool decorator)")
                
        else:
            print("❌ MCP server was not created")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure MCP dependencies are installed: pip install 'mcp[cli]'")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    print("\n" + "=" * 50)
    print("🎯 SDK MCP Integration Test Complete")


if __name__ == "__main__":
    asyncio.run(test_mcp_discovery()) 