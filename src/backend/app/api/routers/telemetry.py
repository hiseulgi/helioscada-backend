from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.app.api.deps import get_db
from src.backend.app.schemas.telemetry import TelemetryLogCreate, TelemetryLogCreateResponse
from src.backend.app.services import telemetry as telemetry_service

router = APIRouter()


@router.post(
    "/telemetry", 
    response_model=TelemetryLogCreateResponse, 
    status_code=status.HTTP_201_CREATED
)
async def log_telemetry(
    *,
    db: AsyncSession = Depends(get_db),
    log_in: TelemetryLogCreate
) -> TelemetryLogCreateResponse:
    # Service function handles inserting data and committing transactions
    db_log = await telemetry_service.create_telemetry_log(db=db, log_in=log_in)
    return TelemetryLogCreateResponse(
        status="success",
        message="Data telemetry logged successfully",
        id=db_log.id
    )
