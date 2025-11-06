"""Data models for Replicate webhooks."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

class WebhookEventType(str, Enum):
    """Types of events that can trigger webhooks."""
    START = "start"
    OUTPUT = "output"
    LOGS = "logs"
    COMPLETED = "completed"

class WebhookEvent(BaseModel):
    """A webhook event from Replicate."""
    type: WebhookEventType
    prediction_id: str = Field(..., description="ID of the prediction that triggered this event")
    timestamp: datetime = Field(..., description="When this event occurred")
    data: Dict[str, Any] = Field(..., description="Event-specific data payload")

class WebhookPayload(BaseModel):
    """The full payload of a webhook request."""
    event: WebhookEvent
    prediction: Dict[str, Any] = Field(..., description="Full prediction object at time of event") 