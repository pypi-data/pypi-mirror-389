"""FastMCP tools for browsing Replicate collections."""

from typing import Any

from mcp.server.fastmcp import FastMCP
from ..models.collection import Collection, CollectionList
from ..replicate_client import ReplicateClient

mcp = FastMCP()

@mcp.tool(
    name="list_collections",
    description="List available model collections on Replicate.",
)
async def list_collections() -> CollectionList:
    """List available model collections on Replicate.
    
    Returns:
        CollectionList containing available collections
        
    Raises:
        RuntimeError: If the Replicate client fails to initialize
        Exception: If the API request fails
    """
    async with ReplicateClient() as client:
        result = await client.list_collections()
        return CollectionList(collections=[Collection(**collection) for collection in result])

@mcp.tool(
    name="get_collection_details",
    description="Get detailed information about a specific collection.",
)
async def get_collection_details(collection_slug: str) -> Collection:
    """Get detailed information about a specific collection.
    
    Args:
        collection_slug: The slug identifier of the collection
        
    Returns:
        Collection object containing detailed collection information
        
    Raises:
        RuntimeError: If the Replicate client fails to initialize
        ValueError: If the collection is not found
        Exception: If the API request fails
    """
    async with ReplicateClient() as client:
        result = await client.get_collection(collection_slug)
        return Collection(**result) 