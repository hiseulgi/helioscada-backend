from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class PVData(BaseModel):
    v: float = Field(..., description="PV Voltage in Volts (V)", ge=0.0)
    i: float = Field(..., description="PV Current in Amperes (A)", ge=0.0)
    p: float = Field(..., description="PV Power in Watts (W)", ge=0.0)
    t: float = Field(..., description="PV Temperature in Celsius (°C)")


class BatteryData(BaseModel):
    v: float = Field(..., description="Battery Voltage in Volts (V)", ge=0.0)
    i: float = Field(..., description="Battery Current in Amperes (A). Positive is charging, negative is discharging")
    p: float = Field(..., description="Battery Power in Watts (W)")
    soc: float = Field(..., description="Battery State of Charge in percentage (%)", ge=0.0, le=100.0)
    soc_status: str = Field(..., description="Algorithm/method used for SoC estimation")
    t: float = Field(..., description="Battery Temperature/Ambient in Celsius (°C)")


class InverterData(BaseModel):
    v_ac: float = Field(..., description="Inverter AC Output Voltage in Volts (V)", ge=0.0)
    i_ac: float = Field(..., description="Inverter AC Output Current in Amperes (A)", ge=0.0)
    p_ac: float = Field(..., description="Inverter AC Output Power in Watts (W)", ge=0.0)
    eff: float = Field(..., description="Inverter efficiency in percentage (%)", ge=0.0, le=100.0)


class RelayData(BaseModel):
    fan: bool = Field(..., description="Cooling fan actuator relay status (True=ON, False=OFF)")
    lamp: bool = Field(..., description="Load light bulb actuator relay status (True=ON, False=OFF)")


class TelemetryLogCreate(BaseModel):
    timestamp: Optional[datetime] = Field(default=None, description="Timestamp of the log. Defaults to server time if null")
    pv: PVData
    battery: BatteryData
    inverter: InverterData
    relay: RelayData


class TelemetryLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    pv: Optional[PVData] = None
    battery: Optional[BatteryData] = None
    inverter: Optional[InverterData] = None
    relay: Optional[RelayData] = None

    @classmethod
    def from_orm_model(cls, db_model, component: Literal["pv", "battery", "inverter", "all"] = "all") -> "TelemetryLogResponse":
        pv_data = PVData(
            v=float(db_model.pv_voltage),
            i=float(db_model.pv_current),
            p=float(db_model.pv_power),
            t=float(db_model.pv_temperature)
        ) if component in ("pv", "all") else None

        battery_data = BatteryData(
            v=float(db_model.battery_voltage),
            i=float(db_model.battery_current),
            p=float(db_model.battery_power),
            soc=float(db_model.battery_soc),
            soc_status=db_model.battery_soc_status,
            t=float(db_model.battery_temperature)
        ) if component in ("battery", "all") else None

        inverter_data = InverterData(
            v_ac=float(db_model.inverter_voltage_ac),
            i_ac=float(db_model.inverter_current_ac),
            p_ac=float(db_model.inverter_power_ac),
            eff=float(db_model.inverter_efficiency)
        ) if component in ("inverter", "all") else None

        relay_data = RelayData(
            fan=db_model.relay_fan,
            lamp=db_model.relay_lamp
        ) if component == "all" else None

        return cls(
            timestamp=db_model.timestamp,
            pv=pv_data,
            battery=battery_data,
            inverter=inverter_data,
            relay=relay_data
        )


class TelemetryListResponse(BaseModel):
    count: int
    data: list[TelemetryLogResponse]
