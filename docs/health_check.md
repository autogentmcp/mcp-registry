# Health Check System for MCP Registry

## Overview

The Health Check System is a feature of the MCP Registry that monitors the health of registered applications and their environments. It periodically makes HTTP requests to health check endpoints provided by the applications and updates their status based on the responses.

## Features

- **Automatic Health Monitoring**: Periodically checks the health of all active applications and environments
- **Status Tracking**: Tracks health status as ACTIVE, INACTIVE, or UNKNOWN
- **Consecutive Failure/Success Tracking**: Only changes status after multiple consecutive failures/successes
- **Environment-specific Health Checks**: Monitors each environment separately using the baseDomain
- **Manual Health Check Triggering**: API endpoints to manually trigger health checks
- **Health Check History**: API endpoints to view health check logs

## How It Works

1. Applications register a health check URL through the API
2. The system periodically sends requests to these URLs
3. Based on the response, the system updates the health status
4. After multiple consecutive failures, an application is marked as INACTIVE
5. After multiple consecutive successes, an application is marked as ACTIVE
6. Environment health status is tracked separately from application health status

## API Endpoints

### Health Status

- `GET /health-check/applications/{application_id}`: Get the current health status of an application
- `GET /health-check/applications/{application_id}/logs`: Get health check logs for an application
- `POST /health-check/applications/{application_id}/check`: Manually trigger a health check

## Configuration

The health check system can be configured through the following settings:

- `MAX_CONSECUTIVE_FAILURES`: Number of consecutive failures before marking an application as INACTIVE (default: 3)
- `MAX_CONSECUTIVE_SUCCESSES`: Number of consecutive successes before marking an application as ACTIVE (default: 2)
- `HEALTH_CHECK_TIMEOUT`: Seconds to wait for a health check response (default: 10)
- `HEALTH_CHECK_INTERVAL`: Seconds between health checks (default: 300)

## Environment Health Checks

When an environment has a `baseDomain` configured, the system constructs environment-specific health check URLs by combining:

1. The environment's baseDomain (e.g., `api.dev.example.com`)
2. The path from the application's health check URL (e.g., `/health`)

For example, if the application's health check URL is `https://example.com/health` and the environment has a baseDomain of `api.dev.example.com`, the system will check `https://api.dev.example.com/health` for that environment.

## Authentication

All health check API endpoints require an admin API key for authentication, provided in the `X-Admin-Key` header.

## Database Schema

The health check system uses the following database models:

- Application
  - `healthStatus`: Current health status (ACTIVE, INACTIVE, UNKNOWN)
  - `lastHealthCheckAt`: Timestamp of the last health check
  - `consecutiveFailures`: Count of consecutive health check failures
  - `consecutiveSuccesses`: Count of consecutive health check successes
  - `healthCheckUrl`: URL to check for application health

- Environment
  - `healthStatus`: Current health status (ACTIVE, INACTIVE, UNKNOWN)
  - `lastHealthCheckAt`: Timestamp of the last health check
  - `baseDomain`: Base domain used to construct environment-specific health check URLs

- HealthCheckLog
  - Records of all health check attempts with details like status code, response time, and error messages
