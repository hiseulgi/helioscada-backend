from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.app.api.deps import get_db
from src.backend.app.schemas.telemetry import (
    TelemetryLogCreate, 
    TelemetryLogCreateResponse,
    TelemetryListResponse,
    TelemetryLogResponse
)
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


@router.get(
    "/telemetry",
    response_model=TelemetryListResponse,
    response_model_exclude_none=True  # Automatically drops None fields (dynamic component filter)
)
async def read_telemetry_history(
    *,
    db: AsyncSession = Depends(get_db),
    start_time: datetime = Query(..., description="Start of query range (ISO 8601)"),
    end_time: datetime = Query(..., description="End of query range (ISO 8601)"),
    component: Literal["pv", "battery", "inverter", "all"] = Query("all", description="Filter by component"),
    downsample_limit: int = Query(500, description="Max data points to return for chart", ge=1)
) -> TelemetryListResponse:
    # Fetch historical data (incorporates downsampling automatically)
    db_logs = await telemetry_service.get_telemetry_history(
        db=db,
        start_time=start_time,
        end_time=end_time,
        downsample_limit=downsample_limit
    )

    # Convert ORM models to response schemas using dynamic filtering
    mapped_data = [
        TelemetryLogResponse.from_orm_model(db_model=log, component=component)
        for log in db_logs
    ]

    return TelemetryListResponse(
        count=len(mapped_data),
        data=mapped_data
    )

