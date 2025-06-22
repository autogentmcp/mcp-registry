# mcp-registry: Application & Endpoint Registry Server

A FastAPI-based registry server with Redis backend for application/endpoint management, heartbeat monitoring, and health checks. Designed for dynamic agent/tool discovery and LLM-friendly metadata.

## Features
- Register applications with metadata and healthcheck endpoints
- Register endpoints for each application, including parameter types/descriptions and security metadata
- List all registered endpoints and their details
- Heartbeat and health monitoring for applications
- Redis backend for high performance and scalability

## API Endpoints

### Register Application
`POST /register_application`
```json
{
  "app_key": "myapp",
  "app_description": "Demo application for testing",
  "base_domain": "https://myapp.example.com",
  "app_healthcheck_endpoint": "https://myapp.example.com/health"
}
```

### Register Endpoint
`POST /register_endpoint`
```json
{
  "app_key": "myapp",
  "endpoint_uri": "/api/do-something",
  "endpoint_description": "Does something useful",
  "parameter_details": {
    "param1": {"type": "string", "description": "The user's name"},
    "param2": {"type": "int", "description": "The user's age"}
  },
  "security": {
    "type": "api_key",
    "header": "X-API-KEY",
    "secret_ref": "myapp_api_key"
  }
}
```

### List Endpoints
`GET /list_endpoints`
Returns all registered endpoints with metadata.

### Heartbeat
`POST /heartbeat?app_key=myapp`
Keeps the application enabled and healthy.

## Configuration
- Set your Redis connection in `src/mcp_registry/config.py` or via the `REDIS_URL` environment variable.

## Quickstart

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn src.mcp_registry.server:app --reload
   ```
3. Use the API endpoints above to register and manage your applications and endpoints.

## Example curl
See the API Endpoints section for sample curl commands.

## Development
- Edit and extend the FastAPI app in `src/mcp_registry/server.py`.
- Use RedisInsight or another Redis UI to inspect the backend if needed.

---
This project is designed for high-availability, LLM-friendly agent/endpoint discovery, and secure metadata management.