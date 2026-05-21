from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import redis.asyncio as aioredis
import json
import httpx
from typing import Dict, List, Optional
import os


# ─── Settings ────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    django_api_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"

settings = Settings()


# ─── App Lifespan ─────────────────────────────────────────────────────────────

redis_client: Optional[aioredis.Redis] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = await aioredis.from_url(settings.redis_url, decode_responses=True)
    print("✅ Redis connected")
    yield
    await redis_client.close()
    print("❌ Redis disconnected")


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="DevBoard Real-Time Service",
    description="WebSocket, notifications, and analytics for DevBoard",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── WebSocket Connection Manager ─────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        self.rooms.setdefault(room, []).append(websocket)
        print(f"🔌 Client joined room: {room} (total: {len(self.rooms[room])})")

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.rooms:
            self.rooms[room].remove(websocket)
            if not self.rooms[room]:
                del self.rooms[room]
        print(f"🔌 Client left room: {room}")

    async def broadcast(self, message: dict, room: str):
        if room in self.rooms:
            dead = []
            for ws in self.rooms[room]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.rooms[room].remove(ws)

    def get_room_count(self, room: str) -> int:
        return len(self.rooms.get(room, []))

    def get_all_rooms(self) -> dict:
        return {room: len(conns) for room, conns in self.rooms.items()}


manager = ConnectionManager()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class BroadcastPayload(BaseModel):
    project_id: str
    event_type: str
    message: str
    user_id: Optional[str] = None
    data: Optional[dict] = None


# ─── WebSocket Endpoint ───────────────────────────────────────────────────────

@app.websocket("/ws/project/{project_id}")
async def project_websocket(websocket: WebSocket, project_id: str):
    """
    Connect to a project's real-time room.
    Clients can send events and receive broadcasts from other members.
    """
    await manager.connect(websocket, project_id)

    # Notify room that a new user connected
    await manager.broadcast(
        {"type": "user_joined", "project_id": project_id, "online_count": manager.get_room_count(project_id)},
        project_id
    )

    try:
        while True:
            data = await websocket.receive_json()
            event = {
                "type": data.get("type", "generic"),
                "payload": data.get("payload", {}),
                "project_id": project_id,
            }
            # Broadcast to all members in this project's room
            await manager.broadcast(event, project_id)

            # Store event in Redis (keep last 100 events per project)
            await redis_client.lpush(f"events:{project_id}", json.dumps(event))
            await redis_client.ltrim(f"events:{project_id}", 0, 99)

    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
        await manager.broadcast(
            {"type": "user_left", "project_id": project_id, "online_count": manager.get_room_count(project_id)},
            project_id
        )


# ─── Analytics Endpoints ──────────────────────────────────────────────────────

@app.get("/analytics/project/{project_id}/activity")
async def get_project_activity(project_id: str, limit: int = 50):
    """Get recent real-time activity events for a project."""
    raw_events = await redis_client.lrange(f"events:{project_id}", 0, limit - 1)
    events = [json.loads(e) for e in raw_events]
    return {
        "project_id": project_id,
        "event_count": len(events),
        "events": events,
    }


@app.get("/analytics/online/{project_id}")
async def get_online_users(project_id: str):
    """Get the number of users currently connected to a project room."""
    count = manager.get_room_count(project_id)
    return {"project_id": project_id, "online_users": count}


@app.get("/analytics/rooms")
async def get_all_active_rooms():
    """Get all active WebSocket rooms and their connection counts."""
    return {"rooms": manager.get_all_rooms(), "total_connections": sum(manager.get_all_rooms().values())}


# ─── Notification Endpoint ────────────────────────────────────────────────────

@app.post("/notify/broadcast")
async def broadcast_notification(payload: BroadcastPayload):
    """
    Broadcast a notification to all users in a project room.
    Called by Django (e.g., from a Celery task or signal) to push real-time updates.
    """
    event = {
        "type": payload.event_type,
        "message": payload.message,
        "user_id": payload.user_id,
        "data": payload.data or {},
    }
    await manager.broadcast(event, payload.project_id)

    # Also publish to Redis pub/sub for other consumers
    await redis_client.publish(f"channel:{payload.project_id}", json.dumps(event))

    return {"status": "broadcasted", "room": payload.project_id, "recipients": manager.get_room_count(payload.project_id)}


# ─── Cache Endpoints ──────────────────────────────────────────────────────────

@app.get("/cache/set")
async def set_cache(key: str, value: str, ttl: int = 300):
    """Simple key-value cache endpoint."""
    await redis_client.setex(key, ttl, value)
    return {"status": "ok", "key": key, "ttl": ttl}


@app.get("/cache/get")
async def get_cache(key: str):
    """Retrieve a cached value."""
    value = await redis_client.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Key not found in cache.")
    return {"key": key, "value": value}


# ─── Health & Root ────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    try:
        await redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    return {
        "status": "healthy",
        "service": "DevBoard Real-Time Service",
        "redis": redis_status,
    }


@app.get("/")
async def root():
    return {
        "service": "DevBoard FastAPI Real-Time Service",
        "docs": "/docs",
        "health": "/health",
    }