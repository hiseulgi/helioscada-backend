import pytest
import httpx
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession


async def test_health_success(test_client: httpx.AsyncClient):
    """Test successful health check endpoint when database is connected."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data


async def test_health_failure_db_error(test_client: httpx.AsyncClient, db_session: AsyncSession):
    """Test health check failure when database connection fails."""
    # Patch the db_session.execute method to simulate DB error
    with patch.object(db_session, "execute", side_effect=Exception("Connection refused")):
        response = await test_client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unhealthy"
        assert data["detail"]["database"] == "disconnected"
        assert "timestamp" in data["detail"]
