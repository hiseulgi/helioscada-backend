from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.app.models.control import ControlLog
from src.backend.app.schemas.control import ControlLogCreate


async def create_control_log(db: AsyncSession, log_in: ControlLogCreate) -> ControlLog:
    # Map the Pydantic create schema to the SQLAlchemy DB model
    db_log = ControlLog(
        timestamp=log_in.timestamp,
        device=log_in.device,
        action=log_in.action,
        status=log_in.status
    )
    
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log
