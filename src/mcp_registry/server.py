import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Request, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import bcrypt

from .config import settings
from .database import init_db, close_prisma, get_prisma
from .health_check import setup_scheduler, router as health_check_router
from .data_agents import router as data_agents_router
from .models import (
    ApplicationEndpointsRegistration,
    ApplicationUpdate,
    RegistrationResult,
    ApplicationResponse,
    EndpointsWithEnvironmentResponse,
    ApplicationWithEnvironmentEndpoints,
    ApplicationWithEnvironmentEndpointsSecure
)
from .auth import (
    validate_application_access,
    get_application_by_app_key,
    verify_admin_key
)
from .endpoint_registration import register_endpoints

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_api_key(provided_key: str, application_id: str, environment_id: str = None) -> bool:
    """
    Verify a provided API key against hashed keys in the database.
    
    Args:
        provided_key: The plain text API key provided by the client
        application_id: The application ID to check keys for
        environment_id: Optional environment ID to check keys for (if None, checks all environments)
        
    Returns:
        bool: True if the key is valid, False otherwise
    """
    try:
        async with get_prisma() as prisma:
            # Build query filter
            where_clause = {"applicationId": application_id}
            if environment_id:
                where_clause["environmentId"] = environment_id
            
            # Find API keys for this application (and optionally environment)
            api_keys = await prisma.apikey.find_many(
                where=where_clause
            )
            
            # Verify the provided API key against the hashed keys in the database
            for stored_key in api_keys:
                try:
                    # Convert the provided API key to bytes and verify against the stored hash
                    if bcrypt.checkpw(provided_key.encode('utf-8'), stored_key.token.encode('utf-8')):
                        return True
                except Exception as e:
                    logger.warning(f"Error verifying API key: {e}")
                    continue
            
            return False
    except Exception as e:
        logger.error(f"Error during API key verification: {e}")
        return False

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["X-API-Key", "X-App-Key", "X-Admin-Key", "X-Environment", 
                   "Content-Type", "Authorization"],
)

# Mount static files directory
import os
import pathlib
current_dir = pathlib.Path(__file__).parent.absolute()
static_dir = os.path.join(current_dir, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include health check router
app.include_router(health_check_router)

# Include data agents router
app.include_router(data_agents_router)

# Events
@app.on_event("startup")
async def startup_db_client():
    await init_db()
    # Setup health check scheduler
    setup_scheduler(app)

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_prisma()

# Root endpoint - redirect to welcome page
@app.get("/", response_class=RedirectResponse, status_code=302)
async def root():
    """Redirect to the static welcome page"""
    return "/static/index.html"

# Health check endpoint
@app.get("/health")
async def health():
    """
    Health check endpoint that returns the status of the service and its dependencies.
    """
    db_status = "ok"
    
    # Check database connection
    try:
        async with get_prisma() as prisma:
            await prisma.application.count()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"
    
    return {
        "status": "ok" if db_status == "ok" else "error",
        "version": settings.APP_VERSION,
        "dependencies": {
            "database": db_status
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Endpoint 1: Update Application
@app.put("/applications/{app_key}", response_model=ApplicationResponse)
async def update_application(
    app_key: str,
    app_data: ApplicationUpdate,
    request: Request,
    api_key: str = Header(None, alias="X-API-Key"),
    app_key_header: str = Header(None, alias="X-App-Key")
):
    """
    Update an application's details.
    
    Only name, description, and healthCheckUrl can be updated.
    Authentication is required via API key in the X-API-Key header and
    application key in the X-App-Key header.
    """
    # Validate API key and app key
    if not api_key or not app_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required authentication headers"
        )
    
    # Verify that app_key in path matches app_key in header
    if app_key != app_key_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="App key in path must match App key in header"
        )
        
    async with get_prisma() as prisma:
        # Find the application by app_key
        app = await prisma.application.find_unique(
            where={"appKey": app_key}
        )
        
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
            
        # Verify API key
        if not await verify_api_key(api_key, app.id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key for this application"
            )
    
        # Update the application - only specific fields allowed
        update_data = {}
        if app_data.description is not None:
            update_data["description"] = app_data.description
        if app_data.healthCheckUrl is not None:
            update_data["healthCheckUrl"] = app_data.healthCheckUrl
            
        updated_app = await prisma.application.update(
            where={"id": app.id},
            data=update_data
        )
        
        # Create audit log
        try:
            await prisma.auditlog.create(data={
                "action": "update_application",
                "details": f"Updated application {app_key}",
                "ipAddress": request.client.host,
                "userAgent": request.headers.get("user-agent"),
                "applicationId": app.id
            })
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
        
        return updated_app

# Endpoint 2: Register Endpoints
@app.post("/register/endpoints", response_model=RegistrationResult)
async def register_application_endpoints(
    registration: ApplicationEndpointsRegistration,
    request: Request,
    api_key: str = Header(None, alias="X-API-Key"),
    app_key_header: str = Header(None, alias="X-App-Key")
):
    """
    Register multiple endpoints for an application.
    
    This endpoint accepts a list of endpoints to register for an application.
    It validates the application and API key, then updates or creates endpoints
    as needed, and removes any endpoints that weren't included in the request.
    
    Authentication is done via API key in the X-API-Key header and
    application key in the X-App-Key header.
    """
    # Validate headers match what's in the registration
    if app_key_header != registration.app_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App key in header must match app_key in request body"
        )
    
    return await register_endpoints(request, registration)

# Endpoint 3: List Endpoints
@app.get("/endpoints", response_model=EndpointsWithEnvironmentResponse)
async def list_endpoints(
    app_key: str,
    environment: Optional[str] = "production"
):
    """
    List all endpoints for an application in a specific environment.
    
    Returns both the environment data (including baseDomain) and the endpoints.
    """
    async with get_prisma() as prisma:
        # Find application by app_key
        application = await prisma.application.find_unique(
            where={"appKey": app_key}
        )
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Find environment by name
        environment_obj = await prisma.environment.find_first(
            where={
                "applicationId": application.id,
                "name": environment
            }
        )
        
        if not environment_obj:
            raise HTTPException(
                status_code=404, 
                detail=f"Environment '{environment}' not found for this application"
            )
        
        # Get endpoints for this application and environment
        endpoints = await prisma.endpoint.find_many(
            where={
                "applicationId": application.id,
                "environmentId": environment_obj.id
            }
        )
        
        # Return both environment data and endpoints, safely handling the baseDomain field
        return {
            "environment": {
                "id": environment_obj.id,
                "name": environment_obj.name,
                "description": environment_obj.description,
                "baseDomain": getattr(environment_obj, "baseDomain", None),
                "status": environment_obj.status,
                "applicationId": environment_obj.applicationId,
                "createdAt": environment_obj.createdAt,
                "updatedAt": environment_obj.updatedAt
            },
            "endpoints": endpoints
        }

# Endpoint 4: List all applications
@app.get("/applications", response_model=List[ApplicationResponse])
async def list_applications(
    admin_key: str = Depends(verify_admin_key)
):
    """
    List all applications registered in the system.
    Requires admin authentication.
    """
    async with get_prisma() as prisma:
        applications = await prisma.application.find_many()
        
        # Convert to response format with default authenticationMethod
        response_data = []
        for app in applications:
            app_dict = app.dict()
            if app_dict.get("authenticationMethod") is None:
                app_dict["authenticationMethod"] = "API_KEY"
            response_data.append(app_dict)
            
        return response_data

# Endpoint 5: List all applications with their endpoints
@app.get("/applications/with-endpoints", response_model=List[ApplicationWithEnvironmentEndpointsSecure])
async def list_applications_with_endpoints(
    admin_key: str = Depends(verify_admin_key),
    environment: Optional[str] = "production"
):
    """
    List all applications with their endpoints for a specific environment.
    Requires admin authentication.
    
    Returns a list of applications, each with their environment data (including baseDomain and security) 
    and associated endpoints.
    """
    async with get_prisma() as prisma:
        # Get all applications
        applications = await prisma.application.find_many(
            include={
                "environments": True
            }
        )
        
        result = []
        
        # For each application, get its endpoints
        for app in applications:
            # Find the specified environment for this application
            app_env = next((env for env in app.environments if env.name == environment), None)
            
            environment_data = None
            endpoints = []
            
            if app_env:
                # Get environment security details
                security_data = await prisma.environmentsecurity.find_unique(
                    where={"environmentId": app_env.id}
                )
                
                # Create environment data with security details
                environment_data = {
                    "id": app_env.id,
                    "name": app_env.name,
                    "description": app_env.description,
                    "baseDomain": getattr(app_env, "baseDomain", None),
                    "status": app_env.status,
                    "createdAt": app_env.createdAt,
                    "updatedAt": app_env.updatedAt,
                    "applicationId": app_env.applicationId,
                    "security": security_data
                }
                
                # Get endpoints for this application and environment
                endpoints = await prisma.endpoint.find_many(
                    where={
                        "applicationId": app.id,
                        "environmentId": app_env.id
                    }
                )
            
            # Create a response object directly
            app_data = {
                "id": app.id,
                "name": app.name,
                "description": app.description,
                "appKey": app.appKey,
                "status": app.status,
                "authenticationMethod": app.authenticationMethod or "API_KEY",  # Default to API_KEY if null
                "healthCheckUrl": app.healthCheckUrl,
                "createdAt": app.createdAt,
                "updatedAt": app.updatedAt,
                "userId": app.userId,
                "environment": environment_data,
                "endpoints": endpoints
            }
            
            result.append(app_data)
        
        return result
