# MCP Registry API Examples

This document provides curl examples for interacting with the MCP Registry API.

## Authentication

The API uses header-based authentication:

| Header | Description | Required For |
|--------|-------------|--------------|
| `X-API-Key` | API key for the application | All application endpoints |
| `X-App-Key` | Application key identifier | All application endpoints |
| `X-Admin-Key` | Admin API key | Admin-only endpoints |
| `X-Environment` | Environment name (defaults to "production") | Endpoints with environment context |

## API Endpoints

### 1. Update Application

Update an application's details.

```bash
curl -X PUT "http://localhost:8000/applications/my-app-key" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -H "X-App-Key: my-app-key" \
  -d '{
    "name": "Updated App Name",
    "description": "This is an updated description",
    "healthCheckUrl": "https://example.com/health"
  }'
```

### 2. Register Endpoints

Register multiple endpoints for an application. This will create new endpoints, update existing ones, and delete endpoints not included in the request.

```bash
curl -X POST "http://localhost:8000/register/endpoints" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -H "X-App-Key: my-app-key" \
  -d '{
    "app_key": "my-app-key",
    "environment": "production",
    "endpoints": [
      {
        "name": "Get User Profile",
        "path": "/users/{user_id}",
        "method": "GET",
        "description": "Retrieve a user profile by ID",
        "isPublic": false,
        "pathParams": {
          "user_id": {
            "type": "string",
            "description": "The user ID"
          }
        },
        "queryParams": {
          "include_details": {
            "type": "boolean",
            "description": "Whether to include additional details"
          }
        },
        "responseBody": {
          "type": "object",
          "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "email": {"type": "string"}
          }
        }
      },
      {
        "name": "Create User",
        "path": "/users",
        "method": "POST",
        "description": "Create a new user",
        "isPublic": false,
        "requestBody": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"}
          },
          "required": ["name", "email"]
        },
        "responseBody": {
          "type": "object",
          "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "email": {"type": "string"},
            "created_at": {"type": "string", "format": "date-time"}
          }
        }
      }
    ]
  }'
```

### 3. List Endpoints

List all endpoints for an application in a specific environment.

```bash
curl -X GET "http://localhost:8000/endpoints?app_key=my-app-key&environment=production"
```

### 4. List Applications

List all applications registered in the system (admin only).

```bash
curl -X GET "http://localhost:8000/applications" \
  -H "X-Admin-Key: your-admin-key-here"
```

### 5. List Applications with Endpoints

List all applications with their endpoints for a specific environment (admin only).

```bash
curl -X GET "http://localhost:8000/applications/with-endpoints?environment=production" \
  -H "X-Admin-Key: your-admin-key-here"
```

## Error Handling

The API returns appropriate HTTP status codes for various error conditions:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication credentials
- `403 Forbidden`: Authenticated but not authorized to perform the action
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Example error response:

```json
{
  "detail": "Invalid API key for this application"
}
```
