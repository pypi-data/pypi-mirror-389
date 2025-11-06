"""Data models for Replicate hardware options."""

from typing import List

from pydantic import BaseModel, Field

class Hardware(BaseModel):
    """A hardware option for running models on Replicate."""
    name: str = Field(..., description="Human-readable name of the hardware")
    sku: str = Field(..., description="SKU identifier for the hardware")

class HardwareList(BaseModel):
    """Response format for listing hardware options."""
    hardware: List[Hardware] 