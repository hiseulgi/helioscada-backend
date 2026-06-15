import logging
from src.backend.app.db.session import engine
from src.backend.app.models.base import Base

# Import models to register them on Base.metadata
try:
    from src.backend.app.models.telemetry import TelemetryLog  # noqa: F401
    from src.backend.app.models.control import ControlLog  # noqa: F401
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db() -> None:
    logger.info("Initializing database...")
    async with engine.begin() as conn:
        # Creates tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created successfully.")
