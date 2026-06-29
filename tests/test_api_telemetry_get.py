import pytest
import httpx
from datetime import datetime, timezone, timedelta
from src.backend.app.models.telemetry import TelemetryLog


async def seed_telemetry_logs(db_session, count: int) -> list[TelemetryLog]:
    """Helper function to seed telemetry logs into the database."""
    base_time = datetime(2026, 6, 11, 10, 0, 0, tzinfo=timezone.utc)
    logs = []
    for i in range(count):
        log = TelemetryLog(
            timestamp=base_time + timedelta(minutes=i),
            
            # PV
            pv_voltage=18.0 + i,
            pv_current=2.0,
            pv_power=36.0,
            pv_temperature=50.0,
            
            # Battery
            battery_voltage=12.5,
            battery_current=1.5,
            battery_power=18.75,
            battery_soc=75.0 + i,
            battery_soc_status="Testing",
            battery_temperature=30.0,
            
            # Inverter
            inverter_voltage_ac=220.0,
            inverter_current_ac=0.1,
            inverter_power_ac=22.0,
            inverter_efficiency=95.0
        )
        db_session.add(log)
        logs.append(log)
        
    await db_session.commit()
    return logs


async def test_get_history_success(test_client: httpx.AsyncClient, db_session):
    """Test retrieving telemetry history with valid parameters."""
    await seed_telemetry_logs(db_session, count=10)
    
    params = {
        "start_time": "2026-06-11T09:00:00Z",
        "end_time": "2026-06-11T11:00:00Z",
        "component": "all",
        "downsample_limit": 100
    }
    
    response = await test_client.get("/api/v1/telemetry", params=params)
    assert response.status_code == 200
    
    data = response.json()
    assert data["count"] == 10
    assert len(data["data"]) == 10
    
    # Check that fields are fully populated
    first_record = data["data"][0]
    assert "timestamp" in first_record
    assert "pv" in first_record
    assert "battery" in first_record
    assert "inverter" in first_record


async def test_get_history_dynamic_filtering(test_client: httpx.AsyncClient, db_session):
    """Test dynamic component filtering strips out non-requested components."""
    await seed_telemetry_logs(db_session, count=1)
    
    params = {
        "start_time": "2026-06-11T09:00:00Z",
        "end_time": "2026-06-11T11:00:00Z",
        "component": "pv"
    }
    
    response = await test_client.get("/api/v1/telemetry", params=params)
    assert response.status_code == 200
    
    data = response.json()
    first_record = data["data"][0]
    
    assert "timestamp" in first_record
    assert "pv" in first_record
    
    # Other components should be absent due to dynamic filtering + response_model_exclude_none
    assert "battery" not in first_record
    assert "inverter" not in first_record
    assert "relay" not in first_record


async def test_get_history_downsampling(test_client: httpx.AsyncClient, db_session):
    """Test systematic downsampling limits number of records returned."""
    # Seed 20 logs
    await seed_telemetry_logs(db_session, count=20)
    
    params = {
        "start_time": "2026-06-11T09:00:00Z",
        "end_time": "2026-06-11T11:00:00Z",
        "downsample_limit": 5
    }
    
    response = await test_client.get("/api/v1/telemetry", params=params)
    assert response.status_code == 200
    
    data = response.json()
    # Should be capped at downsample_limit
    assert len(data["data"]) <= 5
    assert data["count"] <= 5


async def test_get_history_missing_params(test_client: httpx.AsyncClient):
    """Test API rejects request missing mandatory query parameters."""
    response = await test_client.get("/api/v1/telemetry")
    assert response.status_code == 422
