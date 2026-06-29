import pytest
import httpx
from datetime import datetime, timezone
from src.backend.app.models.telemetry import TelemetryLog


async def seed_single_telemetry(db_session) -> TelemetryLog:
    """Helper to seed a single telemetry log with specific values."""
    log = TelemetryLog(
        timestamp=datetime(2026, 6, 11, 10, 30, 0, tzinfo=timezone.utc),
        pv_voltage=18.40,
        pv_current=2.10,
        pv_power=38.60,
        pv_temperature=52.3,
        battery_voltage=12.60,
        battery_current=1.80,
        battery_power=22.70,
        battery_soc=78.50,
        battery_soc_status="Calibrated via Lookup Table",
        battery_temperature=31.2,
        inverter_voltage_ac=220.10,
        inverter_current_ac=0.12,
        inverter_power_ac=26.40,
        inverter_efficiency=95.20
    )
    db_session.add(log)
    await db_session.commit()
    return log


async def test_export_csv_success(test_client: httpx.AsyncClient, db_session):
    """Test successful CSV export streaming."""
    await seed_single_telemetry(db_session)
    
    params = {
        "start_time": "2026-06-11T00:00:00Z",
        "end_time": "2026-06-11T23:59:59Z"
    }
    
    response = await test_client.get("/api/v1/telemetry/export", params=params)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert 'filename="telemetry_log_20260611.csv"' in response.headers["content-disposition"]
    
    # Verify CSV content
    content = response.text
    lines = content.strip().splitlines()
    assert len(lines) == 2  # Header + 1 Data Row
    
    # Check headers
    headers = lines[0].split(",")
    assert headers[0] == "Timestamp"
    assert headers[5] == "BAT_Voltage"
    
    # Check data formatting
    data_row = lines[1].split(",")
    assert "2026-06-11T10:30:00Z" in data_row[0]
    assert data_row[1] == "18.40"
    assert data_row[2] == "2.10"
    assert data_row[8] == "78.50"
    assert data_row[9] == "Calibrated via Lookup Table"


async def test_export_csv_missing_params(test_client: httpx.AsyncClient):
    """Test CSV export requires start_time and end_time query params."""
    response = await test_client.get("/api/v1/telemetry/export")
    assert response.status_code == 422
