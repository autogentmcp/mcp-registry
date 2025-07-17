"""
Health check API routes for the MCP Registry.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from prisma.errors import PrismaError
from typing import List, Optional

from app.auth import get_current_user
from app.health_check import scheduler
from app.models import (
    HealthCheckLogResponse,
    ApplicationHealthStatusResponse,
    EnvironmentHealthStatusResponse,
)

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("/applications/{application_id}", response_model=ApplicationHealthStatusResponse)
async def get_application_health_status(
    application_id: str,
    current_user=Depends(get_current_user),
):
    """
    Get the current health status of an application.
    """
    try:
        app = await current_user.prisma.application.find_unique(
            where={"id": application_id},
            include={"environments": True}
        )
        
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Check if the current user has access to this application
        if app.userId != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
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
    except PrismaError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{application_id}/logs", response_model=List[HealthCheckLogResponse])
async def get_application_health_logs(
    application_id: str,
    environment_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
):
    """
    Get health check logs for an application.
    """
    try:
        # First, check if the user has access to this application
        app = await current_user.prisma.application.find_unique(
            where={"id": application_id}
        )
        
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if app.userId != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build query filters
        where_clause = {"applicationId": application_id}
        if environment_id:
            where_clause["environmentId"] = environment_id
        
        # Get logs
        logs = await current_user.prisma.healthchecklog.find_many(
            where=where_clause,
            take=limit,
            skip=offset,
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
    except PrismaError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications/{application_id}/check")
async def trigger_application_health_check(
    application_id: str,
    current_user=Depends(get_current_user),
):
    """
    Manually trigger a health check for an application.
    """
    try:
        # First, check if the user has access to this application
        app = await current_user.prisma.application.find_unique(
            where={"id": application_id}
        )
        
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        
        if app.userId != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not app.healthCheckUrl:
            raise HTTPException(
                status_code=400, 
                detail="Application does not have a health check URL configured"
            )
        
        # Trigger the health check
        await scheduler.run_now(application_id)
        
        return {"message": "Health check initiated"}
    except PrismaError as e:
        raise HTTPException(status_code=500, detail=str(e))
