# Application Endpoint Registration

This document describes how to use the Application Endpoint Registration API in the MCP Registry.

## Overview

The Application Endpoint Registration API allows client applications to register their endpoints with the MCP Registry. This enables:

1. Discovery of available endpoints by other applications
2. Documentation of endpoint parameters, request/response bodies, etc.
3. Automatic updating when endpoints change
4. Removing endpoints that no longer exist

## Authentication

The API uses API key authentication. To make requests to the API, you need:

- **X-App-Key header**: The application key for your application
- **X-API-Key header**: An API key for your application and environment
- **X-Environment header**: The environment to register endpoints for (default: production)

## Register Endpoints

### Request

```http
POST /register/endpoints
Content-Type: application/json
X-App-Key: your-app-key
X-API-Key: your-api-key
X-Environment: production

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
    },
    {
      "name": "Create User",
      "path": "/api/users",
      "method": "POST",
      "description": "Create a new user",
      "requestBody": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "email": {"type": "string"}
        },
        "required": ["name", "email"]
      }
    }
  ]
}
```

### Response

```json
{
  "added": 1,
  "updated": 1,
  "deleted": 0,
  "message": "Successfully registered endpoints for Example App (production)"
}
```

## Endpoint Fields

| Field | Type | Description |
|-------|------|-------------|
| name | string | Name of the endpoint |
| path | string | URL path of the endpoint, with path parameters in curly braces |
| method | string | HTTP method (GET, POST, PUT, DELETE, etc.) |
| description | string | Description of what the endpoint does |
| isPublic | boolean | Whether the endpoint is public or requires authentication |
| authType | string | Authentication type (API_KEY, JWT, etc.) |
| authConfig | string | Additional authentication configuration |
| pathParams | object | Path parameters with type and description |
| queryParams | object | Query parameters with type and description |
| requestBody | object | Schema of the request body |
| responseBody | object | Schema of the response body |

## Behavior

- **Adding**: New endpoints in the request that don't exist in the database will be created
- **Updating**: Existing endpoints (matching path and method) will be updated
- **Deleting**: Endpoints that exist in the database but are not in the request will be deleted

This ensures that the registry always reflects the current state of your API.

## Example Client

Here's an example of how to use the API with Python:

```python
import httpx
import asyncio

async def register_endpoints():
    headers = {
        "X-App-Key": "your-app-key",
        "X-API-Key": "your-api-key",
        "X-Environment": "production"
    }
    
    payload = {
        "app_key": "your-app-key",
        "environment": "production",
        "endpoints": [
            {
                "name": "Get User",
                "path": "/api/users/{userId}",
                "method": "GET",
                "description": "Get user by ID",
                # ... other fields ...
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/register/endpoints",
            json=payload,
            headers=headers
        )
        
        print(response.json())

asyncio.run(register_endpoints())
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- **400 Bad Request**: Invalid request payload
- **401 Unauthorized**: Invalid API key or application key
- **404 Not Found**: Application or environment not found
- **500 Internal Server Error**: Server-side error

Each error response includes a detail message explaining the issue.
