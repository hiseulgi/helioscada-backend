import datetime
from decimal import Decimal
from sqlalchemy import Numeric, String, Boolean, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.backend.app.models.base import Base


class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    # Solar Panel (PV) Parameters
    pv_voltage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    pv_current: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    pv_power: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    pv_temperature: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)

    # Battery & SoC Parameters
    battery_voltage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    battery_current: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # (+) charging, (-) discharging
    battery_power: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    battery_soc: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    battery_soc_status: Mapped[str] = mapped_column(String(50), nullable=False)
    battery_temperature: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)

    # Inverter (AC) Parameters
    inverter_voltage_ac: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    inverter_current_ac: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    inverter_power_ac: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    inverter_efficiency: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # Actuator Relay Parameters
    relay_fan: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    relay_lamp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


# Explicit index for timestamp descending for optimized time-series queries
Index("idx_telemetry_timestamp", TelemetryLog.timestamp.desc())
