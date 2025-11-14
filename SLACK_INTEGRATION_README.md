# Slack Bot MCP Server Integration

## Overview

MCP Server that validates OAuth tokens with Keycloak and calls backend REST services. Designed for Slack bot integration.

**Flow:** Slack bot sends access token → MCP validates with Keycloak → MCP calls backend service

## Features

- Token validation via Keycloak introspection
- Backend REST service calls with token passthrough
- Stateless Slack API endpoints (no sessions required)
- Tool capability discovery
- Uses Keycloak as both IdP and backend for local testing

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/slack/tools` | GET | List available MCP tools |
| `/slack/query` | POST | Query backend service with token |
| `/slack/health` | GET | Health check |

## Prerequisites

- Python 3.12+
- Keycloak running on port 8080
- Virtual environment

## Setup

### 1. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Configure Keycloak

In Keycloak admin console (http://localhost:8080):

1. Create client:
   - Client ID: `mcp-server-client`
   - Access Type: `confidential`
   - Direct Access Grants: `ON`
   - Copy client secret from Credentials tab

2. Create user:
   - Username: `developer`
   - Set password: `developer` (Temporary: OFF)

### 3. Configure Environment

Create `.env` file with these required variables:

```bash
cat > .env << 'EOF'
# Required - Server Configuration
MCP_PORT=3000
MCP_TRANSPORT_PROTOCOL=streamable-http
ENABLE_AUTH=false

# Required - Keycloak Configuration
SSO_CLIENT_ID=mcp-server-client
SSO_CLIENT_SECRET=<your-keycloak-client-secret>
SSO_INTROSPECTION_URL=http://localhost:8080/realms/master/protocol/openid-connect/token/introspect
EOF
```

**Note:** 
- `MCP_TRANSPORT_PROTOCOL=streamable-http` is required for stateless operation
- `ENABLE_AUTH=false` is required (token validation happens in tools, not middleware)

### 4. Start MCP Server

```bash
python -m template_mcp_server.src.main
```

## Testing

### Run Integration Test

```bash
export KEYCLOAK_CLIENT_SECRET='<your-keycloak-client-secret>'
./test_slack_api.sh
```

Expected output:
```
✅ MCP Server running
✅ Keycloak running
✅ Token obtained
✅ Found 2 tools
✅ Query succeeded
```

### Manual Test

```bash
# Get token from Keycloak
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -d "client_id=mcp-server-client" \
  -d "client_secret=<your-secret>" \
  -d "username=developer" \
  -d "password=developer" \
  -d "grant_type=password" | jq -r '.access_token')

# List tools
curl -s http://localhost:3000/slack/tools | jq

# Query backend
curl -s -X POST http://localhost:3000/slack/query \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "'"$TOKEN"'",
    "backend_url": "http://localhost:8080",
    "endpoint": "/realms/master"
  }' | jq
```

## Environment Variables

### Required in .env

```bash
MCP_PORT=3000
MCP_TRANSPORT_PROTOCOL=streamable-http
ENABLE_AUTH=false
SSO_CLIENT_ID=mcp-server-client
SSO_CLIENT_SECRET=<secret-from-keycloak>
SSO_INTROSPECTION_URL=http://localhost:8080/realms/master/protocol/openid-connect/token/introspect
```

### Required for test script

```bash
export KEYCLOAK_CLIENT_SECRET=<secret-from-keycloak>
```

### Optional (for custom configuration)

```bash
KEYCLOAK_BASE_URL=http://localhost:8080    # Default
KEYCLOAK_REALM=master                      # Default  
MCP_URL=http://localhost:3000              # Default
```

## Request Format

### Query Backend Service

```json
POST /slack/query
{
  "access_token": "token-from-keycloak",
  "backend_url": "http://localhost:8080",
  "endpoint": "/realms/master"
}
```

### Response Format

```json
{
  "status": "success",
  "user": {
    "username": "developer",
    "email": "developer@example.com",
    "roles": ["..."]
  },
  "backend_response": {
    "realm": "master",
    ...
  },
  "message": "Successfully called backend service as developer"
}
```

## Files

### Source Code
```
template_mcp_server/src/
├── token_validator.py       # Validates tokens with Keycloak
├── backend_client.py         # Backend service HTTP client
├── slack_api.py             # REST API for Slack bots
└── tools/
    ├── backend_query_tool.py    # Main query tool
    └── list_capabilities.py     # Tool discovery
```

### Testing
```
test_slack_api.sh            # Integration test script
```

## Architecture

```
Slack Bot
    ↓ (access token)
MCP Server (/slack/query)
    ├─> Keycloak (validate token)
    └─> Backend Service (with token)
```

## Status

- MCP Server: Complete and tested
- Token validation: Working
- Backend integration: Working
- Slack bot: Requires admin approval for workspace installation

