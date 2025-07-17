from datetime import datetime
from typing import Optional, Tuple
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import APIKeyHeader
from prisma.models import ApiKey, Application
import bcrypt

from .database import get_prisma
from .config import settings

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Application Key header
app_key_header = Header(None, alias="X-App-Key")

# Environment header
environment_header = Header("production", alias="X-Environment")

async def validate_application_access(
    app_key: str = Depends(app_key_header),
    api_key: str = Depends(api_key_header),
    environment: str = Depends(environment_header)
) -> Tuple[Application, ApiKey]:
    """
    Validate application access using API key and App key
    Returns the application and API key objects if valid
    """
    if not app_key or not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required authentication headers",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    async with get_prisma() as prisma:
        # Find the application by app_key
        application = await prisma.application.find_unique(
            where={"appKey": app_key},
            include={"environments": True}
        )
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid application key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        if application.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Application is not active",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        # Find environment by name
        env = next((e for e in application.environments if e.name == environment), None)
        if not env:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Environment '{environment}' not found for this application",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        # Find all API keys for this application and environment to verify the provided key
        api_keys = await prisma.apikey.find_many(
            where={
                "applicationId": application.id,
                "environmentId": env.id
            },
            include={"application": True, "environment": True}
        )
        
        # Verify the provided API key against the hashed keys in the database
        valid_api_key = None
        for stored_key in api_keys:
            try:
                # Convert the provided API key to bytes and verify against the stored hash
                if bcrypt.checkpw(api_key.encode('utf-8'), stored_key.token.encode('utf-8')):
                    valid_api_key = stored_key
                    break
            except Exception:
                continue
        
        if not valid_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        # Use the valid API key for further checks
        api_key_obj = valid_api_key
            
        if api_key_obj.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is not active",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        # Check if expired
        if api_key_obj.expiresAt and api_key_obj.expiresAt < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
                headers={"WWW-Authenticate": "ApiKey"},
            )
            
        # Update last used time
        await prisma.apikey.update(
            where={"id": api_key_obj.id},
            data={"lastUsed": datetime.utcnow()}
        )
        
        return application, api_key_obj

async def verify_admin_key(admin_key: str = Header(None, alias="X-Admin-Key")):
    """
    Verify the admin API key for admin-only endpoints
    """
    if not admin_key or admin_key != settings.REGISTRY_ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return admin_key

async def get_application_by_app_key(app_key: str) -> Optional[Application]:
    """
    Get an application by its app key
    """
    if not app_key:
        return None
        
    async with get_prisma() as prisma:
        application = await prisma.application.find_unique(
            where={"appKey": app_key}
        )
        return application
        
async def get_environment_by_name(app_id: str, env_name: str) -> Optional[dict]:
    """
    Get an environment by its name for a given application
    """
    if not app_id or not env_name:
        return None
        
    async with get_prisma() as prisma:
        environment = await prisma.environment.find_first(
            where={
                "applicationId": app_id,
                "name": env_name
            }
        )
        return environment
        
async def validate_api_key(
    api_key: str = Depends(api_key_header),
    app_key: str = Depends(app_key_header),
    environment: str = Depends(environment_header)
) -> Optional[ApiKey]:
    """
    Validate an API key for a specific application and environment
    This simpler version is for endpoints that just need basic validation
    """
    if not api_key or not app_key:
        return None
    
    async with get_prisma() as prisma:
        # Get application
        application = await prisma.application.find_unique(
            where={"appKey": app_key},
            include={"environments": True}
        )
        
        if not application:
            return None
            
        # Find environment by name
        env = next((e for e in application.environments if e.name == environment), None)
        if not env:
            return None
            
        # Get all API keys for this application and environment
        api_keys = await prisma.apikey.find_many(
            where={
                "applicationId": application.id,
                "environmentId": env.id
            },
            include={"application": True, "environment": True}
        )
        
        # Verify the provided API key against the hashed keys in the database
        valid_api_key = None
        for stored_key in api_keys:
            try:
                # Convert the provided API key to bytes and verify against the stored hash
                if bcrypt.checkpw(api_key.encode('utf-8'), stored_key.token.encode('utf-8')):
                    valid_api_key = stored_key
                    break
            except Exception:
                continue
        
        if not valid_api_key:
            return None
            
        if valid_api_key.status != "ACTIVE":
            return None
            
        # Check if expired
        if valid_api_key.expiresAt and valid_api_key.expiresAt < datetime.utcnow():
            return None
            
        # Update last used time
        await prisma.apikey.update(
            where={"id": valid_api_key.id},
            data={"lastUsed": datetime.utcnow()}
        )
        
        return valid_api_key
