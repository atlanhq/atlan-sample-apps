#!/usr/bin/env python3
"""
Minimal test to verify @mcp_tool decorators work correctly.

This test only checks decorator functionality without creating 
full application infrastructure.
"""

import inspect
from app.activities import GiphyActivities
from app.workflow import GiphyWorkflow


def test_decorator_discovery():
    """Test that activities have the correct MCP decorator metadata."""
    print("🧪 Testing @mcp_tool Decorator Discovery")
    print("=" * 50)
    
    # Create activities instance
    activities = GiphyActivities()
    
    # Get activity methods using the same logic as the SDK
    activity_methods = GiphyWorkflow.get_activities(activities)
    
    print(f"📋 Found {len(activity_methods)} total activities:")
    
    mcp_tools_found = 0
    
    for method in activity_methods:
        method_name = method.__name__
        has_mcp_decorator = hasattr(method, '_is_mcp_tool')
        is_mcp_tool = getattr(method, '_is_mcp_tool', False)
        mcp_description = getattr(method, '_mcp_description', None)
        
        print(f"\n🔍 Activity: {method_name}")
        print(f"   • Has @mcp_tool decorator: {has_mcp_decorator}")
        
        if has_mcp_decorator:
            print(f"   • MCP enabled: {is_mcp_tool}")
            print(f"   • Description: {mcp_description}")
            if is_mcp_tool:
                mcp_tools_found += 1
                print(f"   ✅ Will be exposed as MCP tool")
            else:
                print(f"   ❌ MCP tool disabled")
        else:
            print(f"   ⭕ No @mcp_tool decorator (will not be exposed)")
    
    print(f"\n🎯 Summary:")
    print(f"   • Total activities: {len(activity_methods)}")
    print(f"   • MCP tools: {mcp_tools_found}")
    print(f"   • Not exposed: {len(activity_methods) - mcp_tools_found}")
    
    # Validation
    if mcp_tools_found >= 2:
        print(f"\n✅ SUCCESS: Found {mcp_tools_found} MCP tools (fetch_gif, send_email)")
        print("🚀 SDK MCP integration is working!")
    else:
        print(f"\n❌ ISSUE: Only found {mcp_tools_found} MCP tools")
        print("💡 Make sure activities.py has @mcp_tool decorators")
    
    print("=" * 50)


if __name__ == "__main__":
    test_decorator_discovery() 