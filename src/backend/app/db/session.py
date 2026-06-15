from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.backend.app.core.config import settings

# Create asynchronous database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,  # Helps detect disconnected connections
)

# Create async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
