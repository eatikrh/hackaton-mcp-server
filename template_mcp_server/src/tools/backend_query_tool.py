"""MCP tool that queries backend REST service with token from Slack bot.

This tool demonstrates:
1. Receiving OAuth token from Slack bot (via request context)
2. Validating token with Keycloak
3. Calling backend REST service with the token

For local testing, you can use Keycloak's own endpoints as the backend service:
- http://localhost:8080/realms/master/protocol/openid-connect/userinfo
- http://localhost:8080/admin/realms/master/users
"""

from typing import Any, Dict, Optional
from fastapi import Request

from template_mcp_server.src.token_validator import (
    validate_token_with_keycloak,
    extract_user_info,
    TokenValidationError,
)
from template_mcp_server.src.backend_client import (
    BackendServiceClient,
    BackendServiceError,
)
from template_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


async def query_backend_service(
    access_token: str,
    backend_url: str = "http://localhost:8080",
    endpoint: str = "/realms/master/protocol/openid-connect/userinfo",
) -> Dict[str, Any]:
    """Query backend REST service with OAuth token from Slack bot.
    
    This tool:
    1. Validates the access token with Keycloak
    2. Extracts user information
    3. Calls the backend service with the token
    4. Returns the result
    
    For local testing, defaults to Keycloak's userinfo endpoint.
    
    Args:
        access_token: OAuth access token from Slack bot
        backend_url: URL of the backend REST service 
                     (default: http://localhost:8080 - local Keycloak)
        endpoint: API endpoint to call
                  (default: /realms/master/protocol/openid-connect/userinfo)
        
    Returns:
        Dictionary with backend service response and user info
        
    Examples:
        # Default - query Keycloak userinfo (local testing)
        result = await query_backend_service(
            access_token="eyJhbGc..."
        )
        
        # Query Keycloak admin API
        result = await query_backend_service(
            access_token="eyJhbGc...",
            backend_url="http://localhost:8080",
            endpoint="/admin/realms/master/users"
        )
        
        # Query external backend service
        result = await query_backend_service(
            access_token="eyJhbGc...",
            backend_url="https://api.example.com",
            endpoint="/users/me"
        )
    """
    try:
        # Step 1: Validate token with Keycloak
        logger.info("Validating access token with Keycloak")
        token_info = await validate_token_with_keycloak(access_token)
        
        # Step 2: Extract user information
        user_info = extract_user_info(token_info)
        logger.info(f"Token validated for user: {user_info['username']}")
        
        # Step 3: Call backend service with the token
        logger.info(f"Calling backend service: {backend_url}{endpoint}")
        client = BackendServiceClient(backend_url)
        backend_response = await client.call_service(
            access_token=access_token,
            endpoint=endpoint,
            method="GET"
        )
        
        # Step 4: Return combined result
        return {
            "status": "success",
            "user": user_info,
            "backend_response": backend_response,
            "message": f"Successfully called backend service as {user_info['username']}"
        }
        
    except TokenValidationError as e:
        logger.error(f"Token validation failed: {e}")
        return {
            "status": "error",
            "error": "token_validation_failed",
            "message": str(e)
        }
    
    except BackendServiceError as e:
        logger.error(f"Backend service call failed: {e}")
        return {
            "status": "error",
            "error": "backend_service_failed",
            "message": str(e),
            "user": user_info if 'user_info' in locals() else None
        }
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": "unexpected_error",
            "message": str(e)
        }

