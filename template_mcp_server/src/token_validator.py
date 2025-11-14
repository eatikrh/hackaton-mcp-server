"""Token validation against Keycloak.

This module validates OAuth access tokens received from Slack bot
against a Keycloak instance using token introspection.
"""

from typing import Dict, Any, Optional
import httpx

from template_mcp_server.src.settings import settings
from template_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


class TokenValidationError(Exception):
    """Raised when token validation fails."""
    pass


async def validate_token_with_keycloak(access_token: str) -> Dict[str, Any]:
    """Validate access token with Keycloak introspection endpoint.
    
    Args:
        access_token: The OAuth access token to validate
        
    Returns:
        Dictionary containing token information including:
        - active: bool - Whether token is valid
        - username: str - Username of the token owner
        - email: str - Email of the user
        - roles: list - List of user roles
        - exp: int - Token expiration timestamp
        
    Raises:
        TokenValidationError: If validation fails or token is invalid
    """
    if not access_token:
        raise TokenValidationError("Access token is required")
    
    introspection_url = settings.SSO_INTROSPECTION_URL
    if not introspection_url:
        raise TokenValidationError("SSO_INTROSPECTION_URL not configured")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                introspection_url,
                data={
                    "token": access_token,
                    "client_id": settings.SSO_CLIENT_ID,
                    "client_secret": settings.SSO_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            
            token_info = response.json()
            
            # Check if token is active
            if not token_info.get("active", False):
                logger.warning("Token validation failed: token is not active")
                raise TokenValidationError("Token is not active or has expired")
            
            logger.info(
                f"Token validated successfully for user: {token_info.get('username', 'unknown')}"
            )
            
            return token_info
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error during token validation: {e}")
        raise TokenValidationError(f"Failed to validate token: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        raise TokenValidationError(f"Token validation error: {e}")


def extract_user_info(token_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user information from token introspection response.
    
    Args:
        token_info: Token introspection response from Keycloak
        
    Returns:
        Dictionary with user information:
        - username: str
        - email: str
        - user_id: str
        - roles: list
        - groups: list
    """
    # Extract username
    username = (
        token_info.get("preferred_username") or
        token_info.get("username") or
        token_info.get("email") or
        token_info.get("sub")
    )
    
    # Extract roles from various possible locations
    roles = []
    
    # Keycloak realm roles
    if "realm_access" in token_info and "roles" in token_info["realm_access"]:
        roles.extend(token_info["realm_access"]["roles"])
    
    # Direct roles claim
    if "roles" in token_info:
        if isinstance(token_info["roles"], list):
            roles.extend(token_info["roles"])
    
    # Extract groups
    groups = []
    if "groups" in token_info:
        if isinstance(token_info["groups"], list):
            groups = token_info["groups"]
    
    return {
        "username": username,
        "email": token_info.get("email"),
        "user_id": token_info.get("sub"),
        "roles": roles,
        "groups": groups,
    }

