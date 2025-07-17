"""
Health check integration for MCP Registry.
"""

import os
import asyncio
import logging
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Depends, HTTPException, status, Header, APIRouter
from typing import List, Optional

from .models import (
    HealthCheckLogResponse, 
    ApplicationHealthStatusResponse,
    EnvironmentHealthStatusResponse
)
from .config import settings
from .database import get_prisma

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("health_check")

# Constants
MAX_CONSECUTIVE_FAILURES = 3  # Number of consecutive failures before marking as INACTIVE
MAX_CONSECUTIVE_SUCCESSES = 2  # Number of consecutive successes before marking as ACTIVE
HEALTH_CHECK_TIMEOUT = 10  # Seconds to wait for health check response
HEALTH_CHECK_INTERVAL = 300  # Seconds between health checks (5 minutes)

# Create API router
router = APIRouter(
    prefix="/health-check",
    tags=["health-check"],
)

# Global scheduler instance
scheduler = AsyncIOScheduler()

async def check_application_health(app_id: str = None):
    """
    Perform health checks on all active applications or a specific application.
    
    Args:
        app_id: Optional ID of the application to check. If None, checks all active applications.
    """
    try:
        async with get_prisma() as prisma:
            query_filter = {"status": "ACTIVE"}
            if app_id:
                query_filter["id"] = app_id
            
            applications = await prisma.application.find_many(
                where=query_filter,
                include={
                    "environments": True
                }
            )
            
            for app in applications:
                await process_application_health(prisma, app)
                
    except Exception as e:
        logger.error(f"Error during health check execution: {str(e)}")


async def process_application_health(prisma, app):
    """Process health check for a single application and its environments"""
    import httpx
    
    if app.healthCheckUrl:
        # Check the main application health
        health_status, status_code, response_time, message = await perform_health_request(app.healthCheckUrl)
        
        # Update application health status
        consecutive_failures = app.consecutiveFailures
        consecutive_successes = app.consecutiveSuccesses
        current_health_status = app.healthStatus
        
        if health_status == "success":
            consecutive_failures = 0
            consecutive_successes = app.consecutiveSuccesses + 1
            if consecutive_successes >= MAX_CONSECUTIVE_SUCCESSES and current_health_status != "ACTIVE":
                current_health_status = "ACTIVE"
        else:
            consecutive_successes = 0
            consecutive_failures = app.consecutiveFailures + 1
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                current_health_status = "INACTIVE"
        
        # Create health check log
        await prisma.healthchecklog.create(
            data={
                "applicationId": app.id,
                "status": health_status,
                "statusCode": status_code,
                "responseTime": response_time,
                "message": message,
                "consecutiveFailures": consecutive_failures,
                "consecutiveSuccesses": consecutive_successes
            }
        )
        
        # Update application status
        await prisma.application.update(
            where={"id": app.id},
            data={
                "healthStatus": current_health_status,
                "lastHealthCheckAt": datetime.now(),
                "consecutiveFailures": consecutive_failures,
                "consecutiveSuccesses": consecutive_successes
            }
        )
        
        # Process environments if they exist
        if app.environments:
            for env in app.environments:
                await process_environment_health(prisma, app, env)


async def process_environment_health(prisma, app, env):
    """Process health check for a specific environment"""
    import httpx
    from datetime import datetime
    
    # If the environment has a baseDomain, we can construct a health check URL
    health_check_url = None
    
    if env.baseDomain and app.healthCheckUrl:
        # Extract path from app's health check URL and combine with env's baseDomain
        try:
            app_health_url = httpx.URL(app.healthCheckUrl)
            path = app_health_url.path
            health_check_url = f"https://{env.baseDomain.rstrip('/')}{path}"
        except Exception as e:
            logger.error(f"Error constructing environment health check URL: {str(e)}")
    
    if health_check_url:
        health_status, status_code, response_time, message = await perform_health_request(health_check_url)
        
        # Determine health status changes
        current_health_status = env.healthStatus
        
        if health_status == "success":
            if current_health_status != "ACTIVE":
                current_health_status = "ACTIVE"
        else:
            # For environments, immediately mark as inactive on failure
            current_health_status = "INACTIVE"
        
        # Create health check log for environment
        await prisma.healthchecklog.create(
            data={
                "applicationId": app.id,
                "environmentId": env.id,
                "status": health_status,
                "statusCode": status_code,
                "responseTime": response_time,
                "message": message
            }
        )
        
        # Update environment status
        await prisma.environment.update(
            where={"id": env.id},
            data={
                "healthStatus": current_health_status,
                "lastHealthCheckAt": datetime.now()
            }
        )


async def perform_health_request(url: str):
    """
    Perform the actual health check request and return results.
    
    Returns:
        Tuple of (status, status_code, response_time, message)
    """
    import httpx
    from datetime import datetime
    
    status = "failure"
    status_code = None
    response_time = None
    message = None
    
    start_time = datetime.now()
    
    try:
        async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT) as client:
            response = await client.get(url)
            response_time = (datetime.now() - start_time).total_seconds()
            status_code = response.status_code
            
            # Check if response indicates success
            if 200 <= response.status_code < 300:
                status = "success"
                message = "Health check successful"
            else:
                message = f"Health check failed with status code {response.status_code}"
                
    except httpx.RequestError as e:
        status = "error"
        message = f"Request error: {str(e)}"
        response_time = (datetime.now() - start_time).total_seconds()
    except Exception as e:
        status = "error"
        message = f"Unexpected error: {str(e)}"
        response_time = (datetime.now() - start_time).total_seconds()
    
    return status, status_code, response_time, message


async def run_health_check_now(app_id: str = None):
    """Manually trigger a health check run"""
    await check_application_health(app_id)
    logger.info(f"Manual health check completed for app_id={app_id if app_id else 'all'}")


# API Routes

@router.get("/applications/{application_id}", response_model=ApplicationHealthStatusResponse)
async def get_application_health_status(
    application_id: str,
    admin_key: str = Header(None, alias="X-Admin-Key")
):
    """
    Get the current health status of an application.
    """
    if not admin_key or admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")
    
    try:
        async with get_prisma() as prisma:
            app = await prisma.application.find_unique(
                where={"id": application_id},
                include={"environments": True}
            )
            
            if not app:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
            
            return ApplicationHealthStatusResponse(
                id=app.id,
                name=app.name,
                healthStatus=app.healthStatus,
                lastHealthCheckAt=app.lastHealthCheckAt,
                consecutiveFailures=app.consecutiveFailures,
                consecutiveSuccesses=app.consecutiveSuccesses,
                healthCheckUrl=app.healthCheckUrl,
                environments=[
                    EnvironmentHealthStatusResponse(
                        id=env.id,
                        name=env.name,
                        healthStatus=env.healthStatus,
                        lastHealthCheckAt=env.lastHealthCheckAt,
                    )
                    for env in app.environments
                ]
            )
    except Exception as e:
        logger.error(f"Error getting health status: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/applications/{application_id}/logs", response_model=List[HealthCheckLogResponse])
async def get_application_health_logs(
    application_id: str,
    environment_id: Optional[str] = None,
    admin_key: str = Header(None, alias="X-Admin-Key")
):
    """
    Get health check logs for an application.
    """
    if not admin_key or admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")
    
    try:
        async with get_prisma() as prisma:
            # Check if application exists
            app = await prisma.application.find_unique(
                where={"id": application_id}
            )
            
            if not app:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
            
            # Build query filters
            where_clause = {"applicationId": application_id}
            if environment_id:
                where_clause["environmentId"] = environment_id
            
            # Get logs
            logs = await prisma.healthchecklog.find_many(
                where=where_clause,
                take=20,
                order_by={"createdAt": "desc"}
            )
            
            return [
                HealthCheckLogResponse(
                    id=log.id,
                    applicationId=log.applicationId,
                    environmentId=log.environmentId,
                    status=log.status,
                    statusCode=log.statusCode,
                    responseTime=log.responseTime,
                    message=log.message,
                    createdAt=log.createdAt,
                )
                for log in logs
            ]
    except Exception as e:
        logger.error(f"Error getting health logs: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/applications/{application_id}/check")
async def trigger_application_health_check(
    application_id: str,
    admin_key: str = Header(None, alias="X-Admin-Key")
):
    """
    Manually trigger a health check for an application.
    """
    if not admin_key or admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")
    
    try:
        async with get_prisma() as prisma:
            # Check if application exists
            app = await prisma.application.find_unique(
                where={"id": application_id}
            )
            
            if not app:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
            
            if not app.healthCheckUrl:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Application does not have a health check URL configured"
                )
            
            # Trigger the health check
            await run_health_check_now(application_id)
            
            return {"message": "Health check initiated"}
    except Exception as e:
        logger.error(f"Error triggering health check: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def setup_scheduler(app: FastAPI):
    """
    Setup the scheduler for periodic health checks.
    This should be called during the FastAPI application startup event.
    """
    from datetime import datetime
    
    if not scheduler.running:
        scheduler.add_job(
            check_application_health, 
            'interval', 
            seconds=HEALTH_CHECK_INTERVAL, 
            id='health_check_job',
            next_run_time=datetime.now()  # Run immediately on startup
        )
        scheduler.start()
        logger.info(f"Health check scheduler started. Running every {HEALTH_CHECK_INTERVAL} seconds.")
    
    # Add shutdown event handler to stop the scheduler
    @app.on_event("shutdown")
    async def shutdown_scheduler():
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Health check scheduler stopped.")
