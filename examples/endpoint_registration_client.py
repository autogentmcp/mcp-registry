#!/usr/bin/env python
"""
Example script to register endpoints with the MCP Registry
"""
import asyncio
import httpx
import json
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:8000"
APP_KEY = "example-app-123"
API_KEY = "mcp_your_api_key_here"
ENVIRONMENT = "production"

async def register_endpoints():
    """Register sample endpoints with the MCP Registry"""
    
    # Define endpoints to register
    endpoints = [
        {
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
            }
        },
        {
            "name": "Create User",
            "path": "/api/users",
            "method": "POST",
            "description": "Create a new user",
            "isPublic": False,
            "authType": "API_KEY",
            "requestBody": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "password": {"type": "string"}
                },
                "required": ["name", "email", "password"]
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
            "name": "Update User",
            "path": "/api/users/{userId}",
            "method": "PUT",
            "description": "Update a user",
            "isPublic": False,
            "authType": "API_KEY",
            "pathParams": {
                "userId": {
                    "type": "string",
                    "description": "The ID of the user to update"
                }
            },
            "requestBody": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"}
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
        }
    ]
    
    # Prepare the payload
    payload = {
        "app_key": APP_KEY,
        "environment": ENVIRONMENT,
        "endpoints": endpoints
    }
    
    # Set up headers
    headers = {
        "X-API-Key": API_KEY,
        "X-App-Key": APP_KEY,
        "X-Environment": ENVIRONMENT,
        "Content-Type": "application/json"
    }
    
    try:
        # Make the request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/register/endpoints",
                json=payload,
                headers=headers
            )
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                print(f"Endpoints registered successfully!")
                print(f"Added: {result['added']}")
                print(f"Updated: {result['updated']}")
                print(f"Deleted: {result['deleted']}")
                print(f"Message: {result['message']}")
                return result
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"Error: {e}")
        return None

async def list_endpoints():
    """List all endpoints for the application"""
    
    # Set up headers
    headers = {
        "X-API-Key": API_KEY,
        "X-App-Key": APP_KEY
    }
    
    try:
        # Make the request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/endpoints",
                params={"app_key": APP_KEY, "environment": ENVIRONMENT},
                headers=headers
            )
            
            # Handle response
            if response.status_code == 200:
                endpoints = response.json()
                print(f"Retrieved {len(endpoints)} endpoints:")
                for ep in endpoints:
                    print(f"  - {ep['method']} {ep['path']}: {ep['description']}")
                return endpoints
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"Error: {e}")
        return None

async def main():
    """Main function"""
    print("Registering endpoints...")
    await register_endpoints()
    
    print("\nListing endpoints...")
    await list_endpoints()

if __name__ == "__main__":
    asyncio.run(main())
