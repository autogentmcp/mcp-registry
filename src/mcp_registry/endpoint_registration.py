from datetime import datetime
import logging
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status
import bcrypt
from prisma import Json

from .database import get_prisma
from .models import ApplicationEndpointsRegistration, RegistrationResult

# Configure logging
logger = logging.getLogger(__name__)

async def register_endpoints(
    request: Request,
    registration: ApplicationEndpointsRegistration
) -> RegistrationResult:
    """
    Register multiple endpoints for an application.
    
    This will:
    1. Validate the application and API key
    2. Update existing endpoints
    3. Create new endpoints
    4. Delete endpoints that are not in the registration payload
    
    Returns a RegistrationResult with counts of added, updated, and deleted endpoints.
    Raises HTTPException if there are any validation or authentication errors.
    """
    try:
        # Get API key from headers
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-API-Key header"
            )
        
        # Find the application using app_key from the registration
        async with get_prisma() as prisma:
            app = await prisma.application.find_unique(
                where={"appKey": registration.app_key},
                include={"environments": True}
            )
            
            if not app:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Application not found"
                )
            
            # Find environment by name
            environment = None
            for env in app.environments:
                if env.name == registration.environment:
                    environment = env
                    break
            
            if not environment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Environment '{registration.environment}' not found for this application"
                )
                
            # Find all API keys for this application and environment to verify the provided key
            api_keys = await prisma.apikey.find_many(
                where={
                    "applicationId": app.id,
                    "environmentId": environment.id
                }
            )
            
            # Verify the provided API key against the hashed keys in the database
            valid_api_key = None
            for stored_key in api_keys:
                try:
                    # Convert the provided API key to bytes and verify against the stored hash
                    if bcrypt.checkpw(api_key.encode('utf-8'), stored_key.token.encode('utf-8')):
                        valid_api_key = stored_key
                        break
                except Exception as e:
                    logger.warning(f"Error verifying API key: {e}")
                    continue
            
            if not valid_api_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key for this application and environment"
                )
            
            # Validate that we have endpoints to register
            if not registration.endpoints or len(registration.endpoints) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No endpoints provided for registration"
                )
                
            # Check for duplicate endpoints in the request
            endpoint_paths = set()
            for endpoint in registration.endpoints:
                endpoint_key = f"{endpoint.path}:{endpoint.method}"
                if endpoint_key in endpoint_paths:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Duplicate endpoint found: {endpoint.path} ({endpoint.method})"
                    )
                endpoint_paths.add(endpoint_key)
                
            logger.info(f"Registering {len(registration.endpoints)} endpoints for application {app.name} ({registration.environment})")
            
            # Get existing endpoints for this application and environment
            existing_endpoints = await prisma.endpoint.find_many(
                where={
                    "applicationId": app.id,
                    "environmentId": environment.id
                }
            )
            
            # Track existing endpoint paths and methods for lookup
            existing_endpoint_keys = {
                f"{ep.path}:{ep.method}": ep for ep in existing_endpoints
            }
            
            # Track what we've processed to determine which to delete
            processed_endpoint_keys = set()
            
            added = 0
            updated = 0
            
            # Process each endpoint in the registration
            for endpoint in registration.endpoints:
                # Create the endpoint key for lookup
                endpoint_key = f"{endpoint.path}:{endpoint.method}"
                processed_endpoint_keys.add(endpoint_key)
                
                # Map the endpoint registration to Prisma data
                # Use the connect syntax for relations and only include non-None JSON fields
                endpoint_data = {
                    "name": endpoint.name,
                    "path": endpoint.path,
                    "method": endpoint.method,
                    "description": endpoint.description,
                    "isPublic": endpoint.isPublic,
                    "application": {"connect": {"id": app.id}},
                    "environment": {"connect": {"id": environment.id}}
                }
                
                # Only add JSON fields if they have values
                if endpoint.pathParams is not None:
                    endpoint_data["pathParams"] = Json(endpoint.pathParams)
                if endpoint.queryParams is not None:
                    endpoint_data["queryParams"] = Json(endpoint.queryParams)
                if endpoint.requestBody is not None:
                    endpoint_data["requestBody"] = Json(endpoint.requestBody)
                if endpoint.responseBody is not None:
                    endpoint_data["responseBody"] = Json(endpoint.responseBody)
                
                logger.debug(f"Processing endpoint {endpoint_key} with data: {endpoint_data}")
                logger.debug(f"JSON fields: pathParams={endpoint.pathParams}, queryParams={endpoint.queryParams}")
                
                # Check if this endpoint already exists
                if endpoint_key in existing_endpoint_keys:
                    # Update existing endpoint
                    existing = existing_endpoint_keys[endpoint_key]
                    logger.debug(f"Updating existing endpoint {endpoint_key} with ID {existing.id}")
                    await prisma.endpoint.update(
                        where={"id": existing.id},
                        data=endpoint_data
                    )
                    updated += 1
                else:
                    # Create new endpoint
                    logger.debug(f"Creating new endpoint {endpoint_key}")
                    await prisma.endpoint.create(data=endpoint_data)
                    added += 1
            
            # Delete endpoints that weren't in the registration payload
            to_delete = set(existing_endpoint_keys.keys()) - processed_endpoint_keys
            deleted = len(to_delete)
            
            for endpoint_key in to_delete:
                existing = existing_endpoint_keys[endpoint_key]
                await prisma.endpoint.delete(where={"id": existing.id})
            
            # Create audit log entry
            # TODO: Add audit logging for endpoint registration in future version
            pass
            
            return RegistrationResult(
                added=added,
                updated=updated,
                deleted=deleted,
                message=f"Successfully registered endpoints for {app.name} ({registration.environment})"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and convert other exceptions to HTTP exceptions
        logger.error(f"Error registering endpoints: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering endpoints: {str(e)}"
        )
