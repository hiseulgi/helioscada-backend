import pytest
import httpx
from sqlalchemy import select
from src.backend.app.models.control import ControlLog

VALID_PAYLOAD = {
    "timestamp": "2026-06-11T10:30:00Z",
    "device": "fan",
    "action": "ON",
    "status": "SUCCESS"
}


async def test_post_control_success(test_client: httpx.AsyncClient, db_session):
    """Test logging control action with complete valid payload."""
    response = await test_client.post("/api/v1/control", json=VALID_PAYLOAD)
    assert response.status_code == 201
    
    data = response.json()
    assert data["status"] == "success"
    assert "id" in data
    
    # Query DB directly to verify persistence
    db_id = data["id"]
    stmt = select(ControlLog).where(ControlLog.id == db_id)
    result = await db_session.execute(stmt)
    db_log = result.scalar_one_or_none()
    
    assert db_log is not None
    assert db_log.device == "fan"
    assert db_log.action == "ON"
    assert db_log.status == "SUCCESS"


async def test_post_control_success_no_timestamp(test_client: httpx.AsyncClient, db_session):
    """Test logging control action without timestamp uses server default."""
    payload = VALID_PAYLOAD.copy()
    payload.pop("timestamp")
    
    response = await test_client.post("/api/v1/control", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["status"] == "success"
    assert "id" in data
    
    db_id = data["id"]
    stmt = select(ControlLog).where(ControlLog.id == db_id)
    result = await db_session.execute(stmt)
    db_log = result.scalar_one_or_none()
    
    assert db_log is not None
    assert db_log.timestamp is not None  # Automatically populated


async def test_post_control_missing_field(test_client: httpx.AsyncClient):
    """Test validation fails when a required field is missing."""
    payload = VALID_PAYLOAD.copy()
    payload.pop("action")
    
    response = await test_client.post("/api/v1/control", json=payload)
    assert response.status_code == 422
