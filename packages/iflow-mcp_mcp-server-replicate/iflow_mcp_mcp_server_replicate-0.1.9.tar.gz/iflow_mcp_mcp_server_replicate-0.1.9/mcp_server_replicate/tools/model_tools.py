"""FastMCP tools for interacting with Replicate models."""

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from ..models.model import Model, ModelVersion, ModelList
from ..replicate_client import ReplicateClient

mcp = FastMCP()

@mcp.tool(
    name="list_models",
    description="List available models on Replicate with optional filtering by owner.",
)
async def list_models(owner: Optional[str] = None) -> ModelList:
    """List available models on Replicate.
    
    Args:
        owner: Optional owner username to filter models by
        
    Returns:
        ModelList containing the available models and pagination info
        
    Raises:
        RuntimeError: If the Replicate client fails to initialize
        Exception: If the API request fails
    """
    async with ReplicateClient() as client:
        result = client.list_models(owner=owner)
        return ModelList(
            models=[Model(**model) for model in result["models"]],
            next_cursor=result.get("next_cursor"),
            total_count=result.get("total_models")
        )

@mcp.tool(
    name="search_models",
    description="Search for models using semantic search.",
)
async def search_models(query: str) -> ModelList:
    """Search for models using semantic search.
    
    Args:
        query: Search query string
        
    Returns:
        ModelList containing the matching models and pagination info
        
    Raises:
        RuntimeError: If the Replicate client fails to initialize
        Exception: If the API request fails
    """
    async with ReplicateClient() as client:
        result = await client.search_models(query)
        return ModelList(
            models=[Model(**model) for model in result["models"]],
            next_cursor=result.get("next_cursor"),
            total_count=result.get("total_models")
        )

@mcp.tool(
    name="get_model_details",
    description="Get detailed information about a specific model.",
)
async def get_model_details(model_id: str) -> Model:
    """Get detailed information about a specific model.
    
    Args:
        model_id: Model identifier in format 'owner/model'
        
    Returns:
        Model object containing detailed model information
        
    Raises:
        RuntimeError: If the Replicate client fails to initialize
        ValueError: If the model is not found
        Exception: If the API request fails
    """
    owner, name = model_id.split("/")
    async with ReplicateClient() as client:
        # First try to find the model in the owner's models
        result = client.list_models(owner=owner)
        for model in result["models"]:
            if model["name"] == name:
                return Model(**model)
        
        # If not found, try searching for it
        search_result = await client.search_models(model_id)
        for model in search_result["models"]:
            if f"{model['owner']}/{model['name']}" == model_id:
                return Model(**model)
        
        raise ValueError(f"Model not found: {model_id}")

@mcp.tool(
    name="get_model_versions",
    description="Get available versions for a model.",
)
async def get_model_versions(model_id: str) -> list[ModelVersion]:
    """Get available versions for a model.
    
    Args:
        model_id: Model identifier in format 'owner/model'
        
    Returns:
        List of ModelVersion objects containing version metadata
        
    Raises:
        RuntimeError: If the Replicate client fails to initialize
        ValueError: If the model is not found
        Exception: If the API request fails
    """
    async with ReplicateClient() as client:
        versions = client.get_model_versions(model_id)
        return [ModelVersion(**version) for version in versions] 