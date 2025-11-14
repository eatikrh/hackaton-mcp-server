"""Client for calling backend REST services with OAuth token.

This module provides a client to call backend REST services,
passing through the OAuth access token from Slack bot.
"""

from typing import Dict, Any, Optional
import httpx

from template_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


class BackendServiceError(Exception):
    """Raised when backend service call fails."""
    pass


class BackendServiceClient:
    """Client for calling backend REST services with token passthrough."""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize backend service client.
        
        Args:
            base_url: Base URL of the backend service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    async def call_service(
        self,
        access_token: str,
        endpoint: str,
        method: str = "GET",
        **kwargs
    ) -> Dict[str, Any]:
        """Call backend service with OAuth access token.
        
        Args:
            access_token: OAuth access token to pass as Bearer token
            endpoint: API endpoint path (e.g., "/api/users")
            method: HTTP method (GET, POST, PUT, DELETE)
            **kwargs: Additional arguments to pass to httpx request
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            BackendServiceError: If the request fails
        """
        if not access_token:
            raise BackendServiceError("Access token is required")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {access_token}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                )
                
                # Log the request
                logger.info(
                    f"Backend service request: {method} {url} -> {response.status_code}"
                )
                
                # Handle different status codes
                if response.status_code == 401:
                    raise BackendServiceError(
                        "Backend service authentication failed - token may be invalid"
                    )
                elif response.status_code == 403:
                    raise BackendServiceError(
                        "Backend service authorization failed - insufficient permissions"
                    )
                elif response.status_code >= 400:
                    error_msg = f"Backend service error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = f"{error_msg} - {error_data}"
                    except:
                        error_msg = f"{error_msg} - {response.text}"
                    raise BackendServiceError(error_msg)
                
                # Try to parse JSON response
                try:
                    return response.json()
                except:
                    # If not JSON, return text wrapped in dict
                    return {"content": response.text, "status_code": response.status_code}
                    
        except httpx.TimeoutException:
            logger.error(f"Backend service timeout: {url}")
            raise BackendServiceError(f"Backend service timeout: {url}")
        except httpx.RequestError as e:
            logger.error(f"Backend service request error: {e}")
            raise BackendServiceError(f"Backend service request failed: {e}")


async def call_backend_with_token(
    access_token: str,
    backend_url: str,
    endpoint: str,
    method: str = "GET",
    **kwargs
) -> Dict[str, Any]:
    """Convenience function to call backend service.
    
    Args:
        access_token: OAuth access token
        backend_url: Base URL of backend service
        endpoint: API endpoint
        method: HTTP method
        **kwargs: Additional request arguments
        
    Returns:
        Response data
    """
    client = BackendServiceClient(backend_url)
    return await client.call_service(access_token, endpoint, method, **kwargs)

