import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.backend.app.models.base import Base
from src.backend.app.api.deps import get_db
from src.backend.app.main import app
import httpx

# In-memory SQLite database connection string for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # check_same_thread is needed for SQLite to avoid thread-sharing errors
    engine = create_async_engine(
        TEST_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
    
    # Create all database tables in the in-memory database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Initialize session factory
    async_session = async_sessionmaker(
        bind=engine, 
        expire_on_commit=False, 
        class_=AsyncSession
    )
    
    async with async_session() as session:
        yield session
        
    # Dispose the engine to clean up SQLite connections
    await engine.dispose()


@pytest.fixture
async def test_client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    # Override the database dependency in FastAPI app
    async def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    
    # Yield an async HTTPX client for ASGI request routing
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), 
        base_url="http://test"
    ) as client:
        yield client
        
    # Clear overrides to avoid pollution in subsequent tests
    app.dependency_overrides.clear()
