from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.backend.app.api.deps import get_db
from src.backend.app.schemas.health import HealthCheck

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthCheck:
    try:
        # Test connection by executing a simple query
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        # Raise 503 Service Unavailable if database connection fails
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    return HealthCheck(
        status="healthy",
        database=db_status,
        timestamp=datetime.now(timezone.utc)
    )
