from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.app.api.deps import get_db
from src.backend.app.schemas.control import (
    ControlLogCreate,
    ControlLogCreateResponse,
)
from src.backend.app.services import control as control_service

router = APIRouter()


@router.post(
    "/control",
    response_model=ControlLogCreateResponse,
    status_code=status.HTTP_201_CREATED
)
async def log_control(
    *,
    db: AsyncSession = Depends(get_db),
    log_in: ControlLogCreate
) -> ControlLogCreateResponse:
    # Service function handles inserting data and committing transactions
    db_log = await control_service.create_control_log(db=db, log_in=log_in)
    return ControlLogCreateResponse(
        status="success",
        message="Control action logged successfully",
        id=db_log.id
    )
