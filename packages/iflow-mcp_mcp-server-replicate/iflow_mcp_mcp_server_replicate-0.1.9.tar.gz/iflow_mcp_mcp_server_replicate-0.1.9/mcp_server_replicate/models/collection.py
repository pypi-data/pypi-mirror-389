"""Data models for Replicate collections."""

from typing import List, Optional

from pydantic import BaseModel, Field

from .model import Model

class Collection(BaseModel):
    """A collection of related models on Replicate."""
    name: str = Field(..., description="Name of the collection")
    slug: str = Field(..., description="URL-friendly identifier for the collection")
    description: Optional[str] = Field(None, description="Description of the collection's purpose")
    models: List[Model] = Field(default_factory=list, description="Models in this collection")

class CollectionList(BaseModel):
    """Response format for listing collections."""
    collections: List[Collection]
    next_cursor: Optional[str] = None 