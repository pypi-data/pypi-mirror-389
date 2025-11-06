"""Data models for Replicate models and versions."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

class ModelVersion(BaseModel):
    """A specific version of a model on Replicate."""
    id: str = Field(..., description="Unique identifier for this model version")
    created_at: datetime
    cog_version: str
    openapi_schema: Dict[str, Any]
    model: Optional[str] = Field(None, description="Model identifier (owner/name)")
    replicate_version: Optional[str] = Field(None, description="Replicate version identifier")
    hardware: Optional[str] = Field(None, description="Hardware configuration for this version")

class Model(BaseModel):
    """Model information returned from Replicate."""
    id: str = Field(..., description="Unique identifier in format owner/name")
    owner: str = Field(..., description="Owner of the model (user or organization)")
    name: str = Field(..., description="Name of the model")
    description: Optional[str] = Field(None, description="Description of the model's purpose and usage")
    visibility: str = Field("public", description="Model visibility (public/private)")
    github_url: Optional[str] = Field(None, description="URL to model's GitHub repository")
    paper_url: Optional[str] = Field(None, description="URL to model's research paper")
    license_url: Optional[str] = Field(None, description="URL to model's license")
    run_count: Optional[int] = Field(None, description="Number of times this model has been run")
    cover_image_url: Optional[str] = Field(None, description="URL to model's cover image")
    latest_version: Optional[ModelVersion] = Field(None, description="Latest version of the model")
    default_example: Optional[Dict[str, Any]] = Field(None, description="Default example inputs")
    featured: Optional[bool] = Field(None, description="Whether this model is featured")
    tags: Optional[List[str]] = Field(default_factory=list, description="Model tags")
    
    @field_validator("id", mode="before")
    def validate_id(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """Validate and construct ID if not provided."""
        if v:
            return v
        owner = values.get("owner")
        name = values.get("name")
        if owner and name:
            return f"{owner}/{name}"
        raise ValueError("Either id or both owner and name must be provided")

class ModelList(BaseModel):
    """Response format for listing models."""
    models: List[Model]
    next_cursor: Optional[str] = None
    total_count: Optional[int] = None 