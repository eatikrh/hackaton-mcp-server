"""MCP capability discovery tool.

This module provides functionality for Slack bots and other clients
to discover available MCP tools/capabilities.
"""

from typing import Dict, Any, List

# Constants for local testing
DEFAULT_BACKEND_URL = "http://localhost:8080"
EXAMPLE_TOKEN = "eyJhbGc..."


def get_available_tools() -> Dict[str, Any]:
    """Get list of available MCP tools and their descriptions.
    
    This tool allows clients (like Slack bots) to discover what
    capabilities the MCP server provides.
    
    Returns:
        Dictionary with available tools and their metadata
        
    Example Response:
        {
            "status": "success",
            "tools": [
                {
                    "name": "query_backend_service",
                    "description": "Query backend REST service with OAuth token",
                    "parameters": {
                        "access_token": "OAuth access token from Slack bot",
                        "backend_url": "URL of backend service",
                        "endpoint": "API endpoint to call"
                    },
                    "requires_auth": true
                },
                {
                    "name": "multiply_numbers",
                    "description": "Multiply two numbers",
                    "parameters": {
                        "a": "First number",
                        "b": "Second number"
                    },
                    "requires_auth": false
                }
            ]
        }
    """
    tools = [
        {
            "name": "query_backend_service",
            "description": "Query backend REST service with OAuth token from Slack bot. Validates token with Keycloak and calls backend service. Defaults to Keycloak userinfo endpoint for local testing.",
            "parameters": {
                "access_token": {
                    "type": "string",
                    "description": "OAuth access token from Slack bot",
                    "required": True
                },
                "backend_url": {
                    "type": "string",
                    "description": f"Base URL of the backend REST service (default: {DEFAULT_BACKEND_URL} - local Keycloak)",
                    "required": False,
                    "default": DEFAULT_BACKEND_URL
                },
                "endpoint": {
                    "type": "string",
                    "description": "API endpoint path (default: /realms/master/protocol/openid-connect/userinfo)",
                    "required": False,
                    "default": "/realms/master/protocol/openid-connect/userinfo"
                }
            },
            "returns": {
                "type": "object",
                "description": "User info and backend response data"
            },
            "requires_auth": True,
            "example": {
                "access_token": EXAMPLE_TOKEN,
                "backend_url": DEFAULT_BACKEND_URL,
                "endpoint": "/realms/master/protocol/openid-connect/userinfo"
            },
            "local_testing_examples": [
                {
                    "description": "Get user info (default)",
                    "access_token": EXAMPLE_TOKEN
                },
                {
                    "description": "List users (requires admin role)",
                    "access_token": EXAMPLE_TOKEN,
                    "backend_url": DEFAULT_BACKEND_URL,
                    "endpoint": "/admin/realms/master/users"
                },
                {
                    "description": "Get realm info (public)",
                    "access_token": EXAMPLE_TOKEN,
                    "backend_url": DEFAULT_BACKEND_URL,
                    "endpoint": "/realms/master"
                }
            ]
        },
        {
            "name": "multiply_numbers",
            "description": "Multiply two numbers together",
            "parameters": {
                "a": {
                    "type": "number",
                    "description": "First number",
                    "required": True
                },
                "b": {
                    "type": "number",
                    "description": "Second number",
                    "required": True
                }
            },
            "returns": {
                "type": "object",
                "description": "Result of multiplication"
            },
            "requires_auth": False,
            "example": {
                "a": 5,
                "b": 3
            }
        }
    ]
    
    return {
        "status": "success",
        "tool_count": len(tools),
        "tools": tools,
        "message": f"Found {len(tools)} available tools"
    }


def get_tool_info(tool_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific tool.
    
    Args:
        tool_name: Name of the tool to get info for
        
    Returns:
        Tool metadata or error if tool not found
    """
    all_tools = get_available_tools()
    
    for tool in all_tools["tools"]:
        if tool["name"] == tool_name:
            return {
                "status": "success",
                "tool": tool
            }
    
    return {
        "status": "error",
        "error": "tool_not_found",
        "message": f"Tool '{tool_name}' not found",
        "available_tools": [t["name"] for t in all_tools["tools"]]
    }

