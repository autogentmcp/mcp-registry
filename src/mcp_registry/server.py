import asyncio
import os
import json
import redis.asyncio as aioredis
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .config import REDIS_URL

app = FastAPI()

APP_KEY_PREFIX = "app:"
HEARTBEAT_TTL = 60  # seconds

def app_key(app_key):
    return f"{APP_KEY_PREFIX}{app_key}"

def endpoint_key(app_key):
    return f"{APP_KEY_PREFIX}{app_key}:endpoints"

async def get_redis():
    return await aioredis.from_url(REDIS_URL, decode_responses=True)

class ApplicationRegistration(BaseModel):
    app_key: str
    app_description: str
    base_domain: str = ""
    app_healthcheck_endpoint: str = ""

class EndpointRegistration(BaseModel):
    app_key: str
    endpoint_uri: str
    endpoint_description: str = ""
    parameter_details: dict = {}  # Example: {"param1": {"type": "string", "description": "The user's name"}}
    security: dict = {}

@app.post("/register_application")
async def register_application(data: ApplicationRegistration):
    redis = await get_redis()
    app_data = data.dict()
    app_data["status"] = "enabled"
    await redis.set(app_key(data.app_key), json.dumps(app_data))
    await redis.expire(app_key(data.app_key), HEARTBEAT_TTL)
    return {"message": f"Registered application '{data.app_key}'"}

@app.post("/register_endpoint")
async def register_endpoint(data: EndpointRegistration):
    redis = await get_redis()
    endpoint_data = data.dict()
    await redis.rpush(endpoint_key(data.app_key), json.dumps(endpoint_data))
    return {"message": f"Registered endpoint '{data.endpoint_uri}' for app '{data.app_key}'"}

@app.get("/list_endpoints")
async def list_endpoints():
    redis = await get_redis()
    keys = await redis.keys(f"{APP_KEY_PREFIX}*")
    resources = []
    for key in keys:
        if key.endswith(":endpoints"):
            continue
        app_data = await redis.get(key)
        if app_data:
            app = json.loads(app_data)
            endpoints = await redis.lrange(endpoint_key(app["app_key"]), 0, -1)
            for ep_json in endpoints:
                ep = json.loads(ep_json)
                resources.append({
                    "app_key": app["app_key"],
                    "endpoint_uri": ep["endpoint_uri"],
                    "endpoint_description": ep.get("endpoint_description", ""),
                    "parameter_details": ep.get("parameter_details", {}),
                    "security": ep.get("security", {})
                })
    return resources

@app.post("/heartbeat")
async def heartbeat(app_key: str):
    redis = await get_redis()
    key = app_key(app_key)
    data = await redis.get(key)
    if not data:
        raise HTTPException(status_code=404, detail="Application not found")
    app = json.loads(data)
    app["status"] = "enabled"
    await redis.set(key, json.dumps(app))
    await redis.expire(key, HEARTBEAT_TTL)
    return {"message": f"Heartbeat received for '{app_key}'"}

async def monitor_heartbeats_and_health():
    redis = await get_redis()
    while True:
        keys = await redis.keys(f"{APP_KEY_PREFIX}*")
        for key in keys:
            if key.endswith(":endpoints"):
                continue
            ttl = await redis.ttl(key)
            data = await redis.get(key)
            if not data:
                continue
            app = json.loads(data)
            if ttl == -2 or ttl <= 0:
                app["status"] = "disabled"
                await redis.set(key, json.dumps(app))
                continue
            health_url = app.get("app_healthcheck_endpoint")
            if health_url:
                try:
                    async with httpx.AsyncClient(timeout=5) as client:
                        resp = await client.get(health_url)
                        if resp.status_code != 200:
                            app["status"] = "disabled"
                            await redis.set(key, json.dumps(app))
                except Exception:
                    app["status"] = "disabled"
                    await redis.set(key, json.dumps(app))
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_heartbeats_and_health())