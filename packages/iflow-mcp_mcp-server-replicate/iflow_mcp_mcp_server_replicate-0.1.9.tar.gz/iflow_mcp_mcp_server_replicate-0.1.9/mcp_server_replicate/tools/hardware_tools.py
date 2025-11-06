"""FastMCP tools for managing Replicate hardware options."""

from mcp.server.fastmcp import FastMCP
from ..models.hardware import Hardware, HardwareList
from ..replicate_client import ReplicateClient

mcp = FastMCP()

@mcp.tool(
    name="list_hardware",
    description="List available hardware options for running models.",
)
async def list_hardware() -> HardwareList:
    """List available hardware options for running models.
    
    Returns:
        HardwareList containing available hardware options
        
    Raises:
        RuntimeError: If the Replicate client fails to initialize
        Exception: If the API request fails
    """
    async with ReplicateClient() as client:
        result = await client.list_hardware()
        return HardwareList(hardware=[Hardware(**hw) for hw in result]) 