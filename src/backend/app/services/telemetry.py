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
        
        # Relay Actuator Statuses
        relay_fan=log_in.relay.fan,
        relay_lamp=log_in.relay.lamp,
    )
    
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log
