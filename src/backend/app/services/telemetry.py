import csv
import io
from datetime import datetime, timezone
from typing import Sequence, AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.app.models.telemetry import TelemetryLog
from src.backend.app.schemas.telemetry import TelemetryLogCreate


async def create_telemetry_log(db: AsyncSession, log_in: TelemetryLogCreate) -> TelemetryLog:
    # Map the Pydantic create schema to the SQLAlchemy DB model
    db_log = TelemetryLog(
        timestamp=log_in.timestamp,  # Defaults to server time in DB if None
        
        # Solar Panel (PV) Parameters
        pv_voltage=log_in.pv.v,
        pv_current=log_in.pv.i,
        pv_power=log_in.pv.p,
        pv_temperature=log_in.pv.t,
        
        # Battery Parameters
        battery_voltage=log_in.battery.v,
        battery_current=log_in.battery.i,
        battery_power=log_in.battery.p,
        battery_soc=log_in.battery.soc,
        battery_soc_status=log_in.battery.soc_status,
        battery_temperature=log_in.battery.t,
        
        # Inverter Parameters
        inverter_voltage_ac=log_in.inverter.v_ac,
        inverter_current_ac=log_in.inverter.i_ac,
        inverter_power_ac=log_in.inverter.p_ac,
        inverter_efficiency=log_in.inverter.eff,
    )
    
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def get_telemetry_history(
    db: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    downsample_limit: int = 500
) -> Sequence[TelemetryLog]:
    query = (
        select(TelemetryLog)
        .where(TelemetryLog.timestamp >= start_time)
        .where(TelemetryLog.timestamp <= end_time)
        .order_by(TelemetryLog.timestamp.asc())  # Order chronologically for charts
    )
    result = await db.execute(query)
    logs = result.scalars().all()
    
    total_count = len(logs)
    if total_count <= downsample_limit or downsample_limit <= 0:
        return logs
        
    # Systematic downsampling: select every K-th element
    step = total_count // downsample_limit
    if step < 1:
        step = 1
        
    downsampled_logs = [logs[i] for i in range(0, total_count, step)]
    return downsampled_logs[:downsample_limit]


async def generate_telemetry_csv(
    db: AsyncSession,
    start_time: datetime,
    end_time: datetime
) -> AsyncGenerator[str, None]:
    query = (
        select(TelemetryLog)
        .where(TelemetryLog.timestamp >= start_time)
        .where(TelemetryLog.timestamp <= end_time)
        .order_by(TelemetryLog.timestamp.asc())
    )

    headers = [
        "Timestamp", "PV_Voltage", "PV_Current", "PV_Power", "PV_Temp",
        "BAT_Voltage", "BAT_Current", "BAT_Power", "BAT_SoC", "BAT_SoC_Status", "BAT_Temp",
        "INV_VoltageAC", "INV_CurrentAC", "INV_PowerAC", "INV_Eff"
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    yield output.getvalue()
    output.seek(0)
    output.truncate(0)

    # Use streaming to avoid loading large datasets into memory
    result = await db.stream(query)
    async for row in result:
        log = row[0]
        ts = log.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts_str = ts.isoformat()
        if ts_str.endswith("+00:00"):
            ts_str = ts_str[:-6] + "Z"
        elif not ts_str.endswith("Z"):
            ts_str += "Z"
        
        writer.writerow([
            ts_str,
            f"{log.pv_voltage:.2f}",
            f"{log.pv_current:.2f}",
            f"{log.pv_power:.2f}",
            f"{log.pv_temperature:.1f}",
            f"{log.battery_voltage:.2f}",
            f"{log.battery_current:.2f}",
            f"{log.battery_power:.2f}",
            f"{log.battery_soc:.2f}",
            log.battery_soc_status,
            f"{log.battery_temperature:.1f}",
            f"{log.inverter_voltage_ac:.2f}",
            f"{log.inverter_current_ac:.2f}",
            f"{log.inverter_power_ac:.2f}",
            f"{log.inverter_efficiency:.2f}"
        ])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)


