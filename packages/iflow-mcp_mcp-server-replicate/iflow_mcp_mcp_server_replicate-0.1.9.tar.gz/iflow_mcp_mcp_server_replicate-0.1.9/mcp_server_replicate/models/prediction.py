"""Data models for Replicate predictions."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

class PredictionStatus(str, Enum):
    """Status of a prediction."""
    STARTING = "starting"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"

class PredictionInput(BaseModel):
    """Input parameters for creating a prediction."""
    model_version: str = Field(..., description="Model version to use for prediction")
    input: Dict[str, Any] = Field(..., description="Model-specific input parameters")
    template_id: Optional[str] = Field(None, description="Optional template ID to use")
    webhook_url: Optional[str] = Field(None, description="URL for webhook notifications")
    webhook_events: Optional[List[str]] = Field(None, description="Events to trigger webhooks")
    wait: bool = Field(False, description="Whether to wait for prediction completion")
    wait_timeout: Optional[int] = Field(None, description="Max seconds to wait if wait=True (1-60)")
    stream: bool = Field(False, description="Whether to request streaming output")

class Prediction(BaseModel):
    """A prediction (model run) on Replicate."""
    id: str = Field(..., description="Unique identifier for this prediction")
    version: str = Field(..., description="Model version used for this prediction")
    status: PredictionStatus = Field(..., description="Current status of the prediction")
    input: Dict[str, Any] = Field(..., description="Input parameters used for the prediction")
    output: Optional[Any] = Field(None, description="Output from the prediction if completed")
    error: Optional[str] = Field(None, description="Error message if prediction failed")
    logs: Optional[str] = Field(None, description="Execution logs from the prediction")
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    urls: Dict[str, str] = Field(..., description="Related API URLs for this prediction")
    metrics: Optional[Dict[str, float]] = Field(None, description="Performance metrics if available")
    stream_url: Optional[str] = Field(None, description="URL for streaming output if requested") 