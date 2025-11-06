"""FastMCP tools for managing Replicate predictions."""

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from ..models.prediction import Prediction, PredictionInput, PredictionStatus
from ..replicate_client import ReplicateClient

mcp = FastMCP()

@mcp.tool(
    name="create_prediction",
    description="Create a new prediction using a Replicate model.",
)
async def create_prediction(input: PredictionInput) -> Prediction:
    """Create a new prediction using a Replicate model.
    
    Args:
        input: PredictionInput containing model, version, and input parameters
        
    Returns:
        Prediction object containing the prediction details and status
        
    Raises:
        RuntimeError: If the Replicate client fails to initialize
        ValueError: If the model or version is not found
        Exception: If the prediction creation fails
    """
    async with ReplicateClient() as client:
        result = await client.predict(
            model=input.model_id,
            version=input.version_id,
            input_data=input.input_data,
            wait=input.wait,
            wait_timeout=input.wait_timeout,
            stream=input.stream
        )
        return Prediction(**result)

@mcp.tool(
    name="get_prediction",
    description="Get the current status and results of a prediction.",
)
async def get_prediction(prediction_id: str) -> Prediction:
    """Get the current status and results of a prediction.
    
    Args:
        prediction_id: The ID of the prediction to retrieve
        
    Returns:
        Prediction object containing the current status and results
        
    Raises:
        RuntimeError: If the Replicate client fails to initialize
        ValueError: If the prediction is not found
        Exception: If the status check fails
    """
    async with ReplicateClient() as client:
        result = client.get_prediction_status(prediction_id)
        return Prediction(**result)

@mcp.tool(
    name="cancel_prediction",
    description="Cancel a running prediction.",
)
async def cancel_prediction(prediction_id: str) -> Prediction:
    """Cancel a running prediction.
    
    Args:
        prediction_id: The ID of the prediction to cancel
        
    Returns:
        Prediction object containing the updated status
        
    Raises:
        RuntimeError: If the Replicate client fails to initialize
        ValueError: If the prediction is not found
        Exception: If the cancellation fails
    """
    async with ReplicateClient() as client:
        result = await client.cancel_prediction(prediction_id)
        return Prediction(**result)

@mcp.tool(
    name="list_predictions",
    description="List recent predictions with optional filtering.",
)
async def list_predictions(
    status: Optional[PredictionStatus] = None,
    limit: int = 10
) -> list[Prediction]:
    """List recent predictions with optional filtering.
    
    Args:
        status: Optional status to filter predictions by
        limit: Maximum number of predictions to return (1-100)
        
    Returns:
        List of Prediction objects
        
    Raises:
        RuntimeError: If the Replicate client fails to initialize
        ValueError: If limit is out of range
        Exception: If the API request fails
    """
    async with ReplicateClient() as client:
        result = await client.list_predictions(
            status=status.value if status else None,
            limit=limit
        )
        return [Prediction(**prediction) for prediction in result] 