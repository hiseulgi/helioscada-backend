import pytest
import httpx
from sqlalchemy import select
from src.backend.app.models.telemetry import TelemetryLog

VALID_PAYLOAD = {
    "timestamp": "2026-06-11T10:30:00Z",
    "pv": {"v": 18.4, "i": 2.1, "p": 38.6, "t": 52.3},
    "battery": {
        "v": 12.6,
        "i": 1.8,
        "p": 22.7,
        "soc": 78.5,
        "soc_status": "Calibrated via Lookup Table",
        "t": 31.2
    },
    "inverter": {"v_ac": 220.1, "i_ac": 0.12, "p_ac": 26.4, "eff": 95.2},
    "relay": {"fan": False, "lamp": True}
}


async def test_post_telemetry_success_full(test_client: httpx.AsyncClient, db_session):
    """Test logging telemetry with complete valid payload."""
    response = await test_client.post("/api/v1/telemetry", json=VALID_PAYLOAD)
    assert response.status_code == 201
    
    data = response.json()
    assert data["status"] == "success"
    assert "id" in data
    
    # Query DB directly to verify persistence
    db_id = data["id"]
    stmt = select(TelemetryLog).where(TelemetryLog.id == db_id)
    result = await db_session.execute(stmt)
    db_log = result.scalar_one_or_none()
    
    assert db_log is not None
    assert float(db_log.pv_voltage) == 18.4
    assert float(db_log.battery_soc) == 78.5
    assert db_log.battery_soc_status == "Calibrated via Lookup Table"
    assert float(db_log.inverter_voltage_ac) == 220.1
    assert db_log.relay_fan is False
    assert db_log.relay_lamp is True


async def test_post_telemetry_success_no_timestamp(test_client: httpx.AsyncClient, db_session):
    """Test logging telemetry without timestamp uses server default."""
    payload = VALID_PAYLOAD.copy()
    payload.pop("timestamp")
    
    response = await test_client.post("/api/v1/telemetry", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["status"] == "success"
    assert "id" in data
    
    db_id = data["id"]
    stmt = select(TelemetryLog).where(TelemetryLog.id == db_id)
    result = await db_session.execute(stmt)
    db_log = result.scalar_one_or_none()
    
    assert db_log is not None
    assert db_log.timestamp is not None  # Automatically populated


async def test_post_telemetry_invalid_types(test_client: httpx.AsyncClient):
    """Test validation fails when data types are incorrect."""
    payload = VALID_PAYLOAD.copy()
    payload["pv"] = {"v": "not-a-float", "i": 2.1, "p": 38.6, "t": 52.3}
    
    response = await test_client.post("/api/v1/telemetry", json=payload)
    assert response.status_code == 422


async def test_post_telemetry_missing_component(test_client: httpx.AsyncClient):
    """Test validation fails when a required component is missing."""
    payload = VALID_PAYLOAD.copy()
    payload.pop("battery")
    
    response = await test_client.post("/api/v1/telemetry", json=payload)
    assert response.status_code == 422
