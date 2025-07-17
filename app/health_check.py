"""
Health check module for MCP Registry.
This module provides a background service that periodically checks the health of registered applications
and their environments by making HTTP requests to their health check endpoints.
"""

import asyncio
import logging
from datetime import datetime
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from prisma.models import Application, Environment, HealthCheckLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("health_check")

# Constants
MAX_CONSECUTIVE_FAILURES = 3  # Number of consecutive failures before marking an application as INACTIVE
MAX_CONSECUTIVE_SUCCESSES = 2  # Number of consecutive successes before marking an application as ACTIVE
HEALTH_CHECK_TIMEOUT = 10  # Seconds to wait for health check response
HEALTH_CHECK_INTERVAL = 300  # Seconds between health checks (5 minutes)


async def check_application_health(app_id: str = None):
    """
    Perform health checks on all active applications or a specific application.
    
    Args:
        app_id: Optional ID of the application to check. If None, checks all active applications.
    """
    from prisma import Prisma
    db = Prisma()
    await db.connect()
    
    try:
        query_filter = {"status": "ACTIVE"}
        if app_id:
            query_filter["id"] = app_id
        
        applications = await db.application.find_many(
            where=query_filter,
            include={
                "environments": True
            }
        )
        
        for app in applications:
            await process_application_health(db, app)
                
    except Exception as e:
        logger.error(f"Error during health check execution: {str(e)}")
    finally:
        await db.disconnect()


async def process_application_health(db, app):
    """Process health check for a single application and its environments"""
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
        await db.healthchecklog.create(
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
        await db.application.update(
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
                await process_environment_health(db, app, env)


async def process_environment_health(db, app, env):
    """Process health check for a specific environment"""
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
        await db.healthchecklog.create(
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
        await db.environment.update(
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


class HealthCheckScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.running = False
    
    def start(self):
        """Start the health check scheduler"""
        if not self.running:
            self.scheduler.add_job(
                check_application_health, 
                'interval', 
                seconds=HEALTH_CHECK_INTERVAL, 
                id='health_check_job'
            )
            self.scheduler.start()
            self.running = True
            logger.info(f"Health check scheduler started. Running every {HEALTH_CHECK_INTERVAL} seconds.")
    
    def stop(self):
        """Stop the health check scheduler"""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("Health check scheduler stopped.")
    
    async def run_now(self, app_id: str = None):
        """Manually trigger a health check run"""
        await check_application_health(app_id)
        logger.info(f"Manual health check completed for app_id={app_id if app_id else 'all'}")


# Global scheduler instance
scheduler = HealthCheckScheduler()
