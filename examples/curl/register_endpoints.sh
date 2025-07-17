#!/bin/bash

# Register Endpoints Curl Example
# This demonstrates how to register multiple endpoints for an application

# Variables
APP_KEY="your-app-key"
API_KEY="your-api-key"
API_URL="http://localhost:8000/register/endpoints"
ENVIRONMENT="production"  # Can be changed to any environment name

# Payload - Register multiple endpoints
PAYLOAD='{
    "app_key": "'$APP_KEY'",
    "environment": "'$ENVIRONMENT'",
    "endpoints": [
        {
            "name": "Get User",
            "path": "/api/users/{id}",
            "method": "GET",
            "description": "Retrieve user details by ID",
            "isPublic": false,
            "pathParams": {
                "id": {
                    "type": "string",
                    "description": "User ID"
                }
            },
            "queryParams": null,
            "requestBody": null,
            "responseBody": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "email": {
                        "type": "string"
                    }
                }
            }
        },
        {
            "name": "Create User",
            "path": "/api/users",
            "method": "POST",
            "description": "Create a new user",
            "isPublic": false,
            "pathParams": null,
            "queryParams": null,
            "requestBody": {
                "type": "object",
                "required": ["name", "email"],
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "email": {
                        "type": "string"
                    }
                }
            },
            "responseBody": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "email": {
                        "type": "string"
                    }
                }
            }
        }
    ]
}'

# Execute the request
curl -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -H "X-App-Key: $APP_KEY" \
     -H "X-API-Key: $API_KEY" \
     -d "$PAYLOAD"

echo -e "\n\nCommand explanation:"
echo "- POST request to register multiple endpoints for an application"
echo "- APP_KEY: The unique key identifying your application"
echo "- API_KEY: Authentication key for API access"
echo "- ENVIRONMENT: The target environment (production, staging, etc.)"
echo "- Payload contains:"
echo "  * app_key: Application key"
echo "  * environment: Target environment"
echo "  * endpoints: Array of endpoint definitions including:"
echo "    - name: Display name for the endpoint"
echo "    - path: URL path pattern"
echo "    - method: HTTP method (GET, POST, PUT, DELETE, etc.)"
echo "    - description: Human-readable description"
echo "    - isPublic: Whether the endpoint is publicly accessible"
echo "    - pathParams: URL path parameters (if any)"
echo "    - queryParams: Query string parameters (if any)"
echo "    - requestBody: Request body schema (if any)"
echo "    - responseBody: Response body schema (if any)"
