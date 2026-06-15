from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.backend.app.api.routers import health, telemetry
from src.backend.app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run database initialization at startup to ensure all tables exist
    await init_db()
    yield


app = FastAPI(
    title="HELIOSCADA Solar Monitoring API",
    description="FastAPI Backend for Solar Energy Monitoring and IoT Control System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware configuration (crucial for web clients and cross-origin mobile app dev testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with their respective prefixes and tags
app.include_router(health.router, tags=["Health"])
app.include_router(telemetry.router, prefix="/api/v1", tags=["Telemetry"])
