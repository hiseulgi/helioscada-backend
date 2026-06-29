from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ControlLogCreate(BaseModel):
    timestamp: Optional[datetime] = Field(default=None, description="Timestamp of the control action")
    device: str = Field(..., description="Device that was controlled (e.g., 'fan', 'lamp')")
    action: str = Field(..., description="Action performed (e.g., 'ON', 'OFF')")
    status: str = Field(..., description="Status of the action (e.g., 'SUCCESS', 'FAILED')")


class ControlLogCreateResponse(BaseModel):
    status: str
    message: str
    id: int


class ControlLogResponse(BaseModel):
    id: int
    timestamp: datetime
    device: str
    action: str
    status: str

    model_config = ConfigDict(from_attributes=True)

