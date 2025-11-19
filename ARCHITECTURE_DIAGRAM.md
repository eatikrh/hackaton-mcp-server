# Architecture Sequence Diagrams

## Complete Flow: Slack Bot → MCP Server → Backend

```mermaid
sequenceDiagram
    participant User as Slack User
    participant Bot as Slack Bot
    participant KC as Keycloak<br/>(Port 8080)
    participant MCP as MCP Server<br/>(Port 3000)
    participant Backend as Backend Service

    Note over User,Backend: Step 1: User Authentication (One Time)
    
    User->>Bot: Types command in Slack
    Bot->>KC: POST /token<br/>username, password, scope=openid
    KC->>KC: Validate credentials
    KC->>Bot: access_token (JWT)
    Bot->>Bot: Store token for user
    
    Note over User,Backend: Step 2: Query Backend Service
    
    User->>Bot: /query command
    Bot->>MCP: POST /slack/query<br/>{access_token, backend_url, endpoint}
    
    Note over MCP: Token Validation
    MCP->>KC: POST /token/introspect<br/>{token, client_id, client_secret}
    KC->>KC: Validate token<br/>Check: active, not expired
    KC->>MCP: {active: true, username, email, roles}
    
    Note over MCP: Extract User Identity
    MCP->>MCP: extract_user_info()<br/>username, email, roles, groups
    
    Note over MCP: Call Backend
    MCP->>Backend: GET/POST {endpoint}<br/>Authorization: Bearer {access_token}
    Backend->>Backend: Validate token<br/>Apply authorization
    Backend->>MCP: Backend data
    
    Note over MCP: Prepare Response
    MCP->>MCP: Combine user info + backend response
    MCP->>Bot: {status: success, user: {...}, backend_response: {...}}
    
    Bot->>User: Display results in Slack
```

## Token Validation Detail

```mermaid
sequenceDiagram
    participant Tool as query_backend_service<br/>(backend_query_tool.py)
    participant Val as token_validator.py
    participant KC as Keycloak
    participant Client as backend_client.py
    participant Backend as Backend Service

    Tool->>Val: validate_token_with_keycloak(access_token)
    
    Val->>KC: POST /token/introspect<br/>token={access_token}<br/>client_id, client_secret
    
    alt Token Valid
        KC->>Val: {active: true, sub, username, email, roles, exp}
        Val->>Val: Check active == true
        Val->>Val: Log: "Token validated for user"
        Val->>Tool: Return token_info
    else Token Invalid
        KC->>Val: {active: false}
        Val->>Val: Raise TokenValidationError
        Val->>Tool: Error: "Token not active"
    end
    
    Tool->>Tool: extract_user_info(token_info)<br/>Extract username, email, roles
    
    Tool->>Client: call_service(access_token, endpoint)
    Client->>Backend: GET {endpoint}<br/>Authorization: Bearer {token}
    
    alt Backend Success
        Backend->>Client: 200 OK + data
        Client->>Tool: backend_response
        Tool->>Tool: Return {status: success, user, backend_response}
    else Backend Auth Failure
        Backend->>Client: 403 Forbidden
        Client->>Tool: BackendServiceError
        Tool->>Tool: Return {status: error, error: backend_service_failed}
    end
```

## Component Architecture

```mermaid
graph TB
    subgraph "Slack Bot"
        A[User Command]
        B[OAuth Flow Handler]
        C[Token Storage]
    end
    
    subgraph "MCP Server (Port 3000)"
        D[Slack API<br/>slack_api.py]
        E[Query Tool<br/>backend_query_tool.py]
        F[Token Validator<br/>token_validator.py]
        G[Backend Client<br/>backend_client.py]
        H[Tool Discovery<br/>list_capabilities.py]
    end
    
    subgraph "Keycloak (Port 8080)"
        I[OAuth Endpoints<br/>/token]
        J[Introspection<br/>/token/introspect]
        K[User Store]
    end
    
    subgraph "Backend Services"
        L[API Endpoint<br/>with Bearer auth]
    end
    
    A-->B
    B-->I
    I-->K
    I-->C
    C-->D
    D-->E
    E-->F
    F-->J
    J-->K
    E-->G
    G-->L
    L-->G
    G-->E
    E-->D
    D-->A
    D-->H
    
    style F fill:#fff,stroke:#333,color:#000
    style J fill:#fff,stroke:#333,color:#000
    style E fill:#fff,stroke:#333,color:#000
    style G fill:#fff,stroke:#333,color:#000
```

## Files Involved

| Step | File | Function |
|------|------|----------|
| 1. Entry | `slack_api.py` | `slack_query_backend()` |
| 2. Tool | `backend_query_tool.py` | `query_backend_service()` |
| 3. Validate | `token_validator.py` | `validate_token_with_keycloak()` |
| 4. Extract | `token_validator.py` | `extract_user_info()` |
| 5. Backend | `backend_client.py` | `call_service()` |
| 6. Return | `backend_query_tool.py` | Return combined response |

## Key Validation Points

1. **Token Introspection** (Line 46-54 in token_validator.py)
   - Calls: `POST http://localhost:8080/realms/master/protocol/openid-connect/token/introspect`
   - Sends: token, client_id, client_secret
   - Gets: active status, user info, roles

2. **Active Check** (Line 60-63 in token_validator.py)
   - Verifies: `token_info.get("active") == True`
   - Fails if: token expired, revoked, or invalid

3. **User Extraction** (Line 79-124 in token_validator.py)
   - Extracts: username, email, user_id, roles, groups
   - Supports: Multiple claim formats (Keycloak, Google, Red Hat SSO)

4. **Backend Call** (Line 64-95 in backend_client.py)
   - Adds: `Authorization: Bearer {access_token}` header
   - Backend validates token independently (two-tier auth)


