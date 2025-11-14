"""Template MCP Server implementation.

This module contains the main Template MCP Server class that provides
tools for MCP clients. It uses FastMCP to register and manage MCP capabilities.
"""

from fastmcp import FastMCP

from template_mcp_server.src.settings import settings

# Import tools from the tools package
from template_mcp_server.src.tools.backend_query_tool import (
    query_backend_service,
)
from template_mcp_server.src.tools.code_review_tool import (
    generate_code_review_prompt,
)
from template_mcp_server.src.tools.list_capabilities import (
    get_available_tools,
    get_tool_info,
)
from template_mcp_server.src.tools.multiply_tool import (
    multiply_numbers,
)
from template_mcp_server.src.tools.redhat_logo_tool import (
    get_redhat_logo,
)
from template_mcp_server.utils.pylogger import (
    force_reconfigure_all_loggers,
    get_python_logger,
)

logger = get_python_logger()


class TemplateMCPServer:
    """Main Template MCP Server implementation following tools-first architecture.

    This server provides only tools, not resources or prompts, adhering to
    the tools-first architectural pattern for MCP servers.
    """

    def __init__(self):
        """Initialize the MCP server with template tools following tools-first architecture."""
        try:
            # Initialize FastMCP server
            self.mcp = FastMCP("template")

            # Force reconfigure all loggers after FastMCP initialization to ensure structured logging
            force_reconfigure_all_loggers(settings.PYTHON_LOG_LEVEL)

            self._register_mcp_tools()

            logger.info("Template MCP Server initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Template MCP Server: {e}")
            raise

    def _register_mcp_tools(self) -> None:
        """Register MCP tools for template operations (tools-first architecture).

        Registers all available tools with the FastMCP server instance.
        In tools-first architecture, the server only provides tools.
        Currently includes:
        - multiply_numbers: Basic arithmetic operations
        - generate_code_review_prompt: Code review prompt generation
        - get_redhat_logo: Red Hat logo retrieval as base64
        - query_backend_service: Query backend REST services with OAuth token
        - get_available_tools: List available tools for capability discovery
        - get_tool_info: Get detailed information about a specific tool
        """
        # Register all the imported tools
        self.mcp.tool()(multiply_numbers)
        self.mcp.tool()(generate_code_review_prompt)
        self.mcp.tool()(get_redhat_logo)
        
        # Register Slack bot integration tools
        self.mcp.tool()(query_backend_service)
        self.mcp.tool()(get_available_tools)
        self.mcp.tool()(get_tool_info)
