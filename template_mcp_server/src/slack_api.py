"""Simple REST API for Slack bot integration.

This provides stateless endpoints that don't require MCP session management.
Slack bots can call these endpoints directly with access tokens.
"""

from typing import Dict, Any
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from template_mcp_server.src.tools.backend_query_tool import query_backend_service
from template_mcp_server.src.tools.list_capabilities import (
    get_available_tools,
    get_tool_info,
)
from template_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()

slack_router = APIRouter(prefix="/slack", tags=["Slack Integration"])


class BackendQueryRequest(BaseModel):
    """Request model for backend service query."""
    access_token: str
    backend_url: str = "http://localhost:8080"
    endpoint: str = "/realms/master/protocol/openid-connect/userinfo"


class ToolInfoRequest(BaseModel):
    """Request model for tool info."""
    tool_name: str


@slack_router.post("/query")
async def slack_query_backend(request: BackendQueryRequest) -> Dict[str, Any]:
    """Query backend service with OAuth token from Slack bot.
    
    This is a simple REST endpoint that doesn't require MCP session management.
    Perfect for stateless Slack bot integration.
    
    Args:
        request: Backend query request with access token
        
    Returns:
        User info and backend response
    """
    logger.info(f"Slack bot query: {request.endpoint}")
    
    result = await query_backend_service(
        access_token=request.access_token,
        backend_url=request.backend_url,
        endpoint=request.endpoint
    )
    
    return result


@slack_router.get("/tools")
async def slack_list_tools() -> Dict[str, Any]:
    """List available MCP tools for Slack bot discovery.
    
    Returns:
        List of available tools with metadata
    """
    logger.info("Slack bot requesting tool list")
    return get_available_tools()


@slack_router.post("/tool-info")
async def slack_get_tool_info(request: ToolInfoRequest) -> Dict[str, Any]:
    """Get detailed information about a specific tool.
    
    Args:
        request: Tool info request
        
    Returns:
        Tool metadata
    """
    logger.info(f"Slack bot requesting info for tool: {request.tool_name}")
    return get_tool_info(request.tool_name)


@slack_router.get("/health")
async def slack_health_check() -> Dict[str, str]:
    """Health check for Slack bot integration."""
    return {
        "status": "healthy",
        "service": "slack-integration-api",
        "message": "Ready for Slack bot requests"
    }

