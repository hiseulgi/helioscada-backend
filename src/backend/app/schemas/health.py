from datetime import datetime
from pydantic import BaseModel


class HealthCheck(BaseModel):
    status: str
    database: str
    timestamp: datetime
