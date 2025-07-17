#!/usr/bin/env python
"""
Example script to demonstrate using the MCP Registry API
"""
import asyncio
import httpx
import json
from pprint import pprint
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
EMAIL = "admin@example.com"
PASSWORD = "password123"
APP_NAME = "Example App"

async def get_token(email: str, password: str) -> str:
    """Get an access token for API authentication"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/token", 
            params={"email": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        return data["access_token"]

async def create_application(token: str) -> Dict[str, Any]:
    """Create a new application in the registry"""
    headers = {"Authorization": f"Bearer {token}"}
    app_data = {
        "name": APP_NAME,
        "description": "An example application to demonstrate the MCP Registry API",
        "appKey": "example-app-123",
        "authenticationMethod": "API_KEY",
        "healthCheckUrl": "https://example.com/health"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/applications", 
            json=app_data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def create_endpoint(token: str, app_id: str) -> Dict[str, Any]:
    """Create a new endpoint for the application"""
    headers = {"Authorization": f"Bearer {token}"}
    endpoint_data = {
        "name": "Get User",
        "path": "/api/users/{userId}",
        "method": "GET",
        "description": "Get a user by ID",
        "isPublic": False,
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
                "description": "Fields to include in the response",
                "required": False
            }
        },
        "responseBody": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "email": {"type": "string"}
            }
        },
        "applicationId": app_id
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/applications/{app_id}/endpoints", 
            json=endpoint_data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def create_api_key(token: str, app_id: str, env_id: str) -> Dict[str, Any]:
    """Create a new API key for the application"""
    headers = {"Authorization": f"Bearer {token}"}
    api_key_data = {
        "name": "Development API Key",
        "applicationId": app_id,
        "environmentId": env_id,
        "userId": "user_id_here"  # You would replace this with the actual user ID
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/applications/{app_id}/api-keys", 
            json=api_key_data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def get_application_with_endpoints(token: str, app_id: str) -> Dict[str, Any]:
    """Get an application with all its endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/applications/{app_id}/with-endpoints", 
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def main():
    """Main function to demonstrate the MCP Registry API"""
    try:
        # Get an access token
        print("Getting access token...")
        token = await get_token(EMAIL, PASSWORD)
        print(f"Token: {token[:10]}...")
        
        # Create a new application
        print("\nCreating application...")
        app = await create_application(token)
        app_id = app["id"]
        print(f"Application created with ID: {app_id}")
        
        # Get the default environment
        print("\nGetting environments...")
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/applications/{app_id}/environments", 
                headers=headers
            )
            response.raise_for_status()
            environments = response.json()
            
        if environments:
            env_id = environments[0]["id"]
            print(f"Using environment: {environments[0]['name']} (ID: {env_id})")
            
            # Create an API key
            print("\nCreating API key...")
            api_key = await create_api_key(token, app_id, env_id)
            print(f"API key created: {api_key['token']}")
        
        # Create an endpoint
        print("\nCreating endpoint...")
        endpoint = await create_endpoint(token, app_id)
        print(f"Endpoint created: {endpoint['path']} ({endpoint['method']})")
        
        # Get the application with endpoints
        print("\nGetting application with endpoints...")
        app_with_endpoints = await get_application_with_endpoints(token, app_id)
        print("\nApplication with endpoints:")
        print(f"Name: {app_with_endpoints['name']}")
        print(f"Description: {app_with_endpoints['description']}")
        print(f"Endpoints: {len(app_with_endpoints['endpoints'])}")
        for ep in app_with_endpoints["endpoints"]:
            print(f"  - {ep['method']} {ep['path']}")
            
    except httpx.HTTPStatusError as e:
        print(f"Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
