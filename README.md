# MCP Registry

A high-performance, LLM-friendly Model Context Protocol registry server for managing applications and their endpoints. Built with FastAPI and PostgreSQL with Prisma ORM.

## Features

- **Application Management**: Manage application metadata
- **Endpoint Registry**: Document API endpoints with detailed metadata:
  - Path and query parameters
  - Request and response schemas
  - Method, description, and visibility
- **Environment Support**: Multiple environments per application (production, staging, etc.)
- **API Key Authentication**: Secure access via API keys
- **Audit Logging**: Track changes to your registry
- **Health Check Monitoring**: Automatic monitoring of application and environment health:
  - Periodic health checks of registered applications
  - Environment-specific health monitoring using baseDomain
  - Health status tracking and history

## Tech Stack

- **FastAPI**: High-performance API framework
- **PostgreSQL**: Robust relational database
- **Prisma ORM**: Type-safe database client
- **Authentication**: API key-based authentication
- **Python 3.12+**: Modern Python features

## Installation

1. Clone the repository
   ```bash
   git clone https://github.com/spranab/mcp-registry.git
   cd mcp-registry
   ```

2. Create a virtual environment and install dependencies
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the database
   ```bash
   # Install Prisma CLI
   pip install prisma

   # Generate Prisma client
   prisma generate

   # Apply migrations
   prisma db push
   ```

4. Configure environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your database URL, secrets, etc.
   ```

5. Run the server
   ```bash
   python run_server.py
   # Or directly with uvicorn:
   # uvicorn src.mcp_registry.server:app --reload
   ```

## API Documentation

When the server is running, visit http://localhost:8000/docs for the Swagger UI documentation.

## Authentication

The registry uses API key authentication for all endpoints:
- **X-API-Key header**: The API key for the application
- **X-App-Key header**: The application key that identifies the application
- **X-Admin-Key header**: Admin key for administrative endpoints

## Core API Endpoints

### Application Management
- `PUT /applications/{app_key}` - Update an application's details (name, description, healthCheckUrl)

### Endpoint Management
- `POST /register/endpoints` - Register multiple endpoints for an application
- `GET /endpoints?app_key={app_key}&environment={environment}` - List all endpoints for an application

### Administrative Endpoints
- `GET /applications` - List all applications registered in the system
- `GET /applications/with-endpoints` - List all applications with their endpoints

### System Endpoints
- `GET /health` - Health check endpoint

## Directory Structure

```
mcp-registry/
├── examples/               # Example API usage scripts
│   ├── curl/               # Curl examples (bash and batch)
│   └── curl_examples.md    # Markdown examples
├── prisma/                 # Prisma schema and migrations
├── src/                    # Source code
│   └── mcp_registry/       # Main package
│       ├── auth.py         # Authentication logic
│       ├── config.py       # Configuration settings
│       ├── database.py     # Database connection
│       ├── endpoint_registration.py # Endpoint registration logic
│       ├── models.py       # Pydantic models
│       └── server.py       # FastAPI application
├── .env.example            # Example environment variables
├── README.md               # This file
├── requirements.txt        # Python dependencies
└── run_server.py           # Server runner
```

## Example Usage

For detailed API usage examples, see:
- [curl_examples.md](examples/curl_examples.md) for Markdown examples
- [examples/curl](examples/curl) directory for executable scripts
  ```json
  {
    "app_key": "your-app-key",
    "environment": "production",
    "endpoints": [
      {
        "name": "Get User",
        "path": "/api/users/{userId}",
        "method": "GET",
        "description": "Get user by ID",
        "isPublic": false,
        "authType": "API_KEY",
        "pathParams": {
          "userId": {
            "type": "string",
            "description": "The ID of the user to fetch"
          }
        },
        "queryParams": {
          "include": {
            "type": "string",
            "description": "Fields to include in response"
          }
        },
        "responseBody": {
          "type": "object",
          "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"}
          }
        }
      }
    ]
  }
  ```

- `GET /endpoints` - List all endpoints for an application

### Environment Management
- `POST /applications/{app_id}/environments` - Create a new environment
- `GET /applications/{app_id}/environments` - Get all environments for an application
- `PUT /applications/{app_id}/environments/{env_id}` - Update an environment
- `DELETE /applications/{app_id}/environments/{env_id}` - Delete an environment

### Endpoint Management
- `POST /applications/{app_id}/endpoints` - Create a new endpoint
- `GET /applications/{app_id}/endpoints` - Get all endpoints for an application
- `PUT /applications/{app_id}/endpoints/{endpoint_id}` - Update an endpoint
- `DELETE /applications/{app_id}/endpoints/{endpoint_id}` - Delete an endpoint

### API Key Management
- `POST /applications/{app_id}/api-keys` - Create a new API key
- `GET /applications/{app_id}/api-keys` - Get all API keys for an application
- `PUT /applications/{app_id}/api-keys/{key_id}/revoke` - Revoke an API key

### Security Settings
- `POST /applications/{app_id}/environments/{env_id}/security` - Create security settings
- `GET /applications/{app_id}/environments/{env_id}/security` - Get security settings
- ~~`PUT /applications/{app_id}/environments/{env_id}/security` - Update security settings~~ *(Updates disabled for security)*

### Audit Logging
- `GET /applications/{app_id}/audit-logs` - Get audit logs for an application

## Example Environment Variables

```
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mcp_registry

# Security
SECRET_KEY=your-secret-key-here
REGISTRY_ADMIN_KEY=your-admin-api-key-here

# Default user
DEFAULT_USER_ID=cl123456789
```

## Development

- Edit the FastAPI app in `src/mcp_registry/server.py`
- Update the Prisma schema in `prisma/schema.prisma`
- Add new models in `src/mcp_registry/models.py`
- Modify authentication in `src/mcp_registry/auth.py`

---
This project is designed for high-availability, LLM-friendly agent/endpoint discovery, and secure metadata management.