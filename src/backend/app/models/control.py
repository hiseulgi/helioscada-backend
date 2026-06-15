import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.backend.app.models.base import Base


class ControlLog(Base):
    __tablename__ = "control_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    device: Mapped[str] = mapped_column(String(20), nullable=False)  # 'fan' or 'lamp'
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # 'ON' or 'OFF'
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # 'SUCCESS' or 'FAILED'
