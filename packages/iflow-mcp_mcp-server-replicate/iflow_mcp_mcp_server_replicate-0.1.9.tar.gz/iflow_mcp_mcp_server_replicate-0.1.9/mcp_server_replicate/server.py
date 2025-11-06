"""FastMCP server implementation for Replicate API."""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import webbrowser
from collections.abc import Sequence
from typing import Any

import httpx
import jsonschema
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts.base import Message, TextContent, UserMessage
from mcp.server.session import ServerSession
from mcp.types import (
    AnyUrl,
    BlobResourceContents,
    EmptyResult,
    ResourceUpdatedNotification,
    TextResourceContents,
)
from pydantic import BaseModel, Field, field_validator

from .models.collection import Collection, CollectionList
from .models.hardware import Hardware, HardwareList
from .models.model import Model, ModelList
from .models.webhook import WebhookPayload
from .replicate_client import ReplicateClient
from .templates.parameters.common_configs import QUALITY_PRESETS, STYLE_PRESETS, TEMPLATES

logger = logging.getLogger(__name__)


class SubscriptionRequest(BaseModel):
    """Request model for subscription operations."""

    uri: str = Field(..., description="Resource URI to subscribe to")
    session_id: str = Field(..., description="ID of the session making the request")


class GenerationSubscriptionManager:
    """Manages subscriptions to generation resources."""

    def __init__(self):
        self._subscriptions: dict[str, set[ServerSession]] = {}
        self._check_task: asyncio.Task | None = None

    async def subscribe(self, uri: str, session: ServerSession):
        """Subscribe a session to generation updates."""
        prediction_id = uri.replace("generations://", "")
        if prediction_id not in self._subscriptions:
            self._subscriptions[prediction_id] = set()
        self._subscriptions[prediction_id].add(session)

        # Start checking if not already running
        if not self._check_task:
            self._check_task = asyncio.create_task(self._check_generations())

    async def unsubscribe(self, uri: str, session: ServerSession):
        """Unsubscribe a session from generation updates."""
        prediction_id = uri.replace("generations://", "")
        if prediction_id in self._subscriptions:
            self._subscriptions[prediction_id].discard(session)
            if not self._subscriptions[prediction_id]:
                del self._subscriptions[prediction_id]

        # Stop checking if no more subscriptions
        if not self._subscriptions and self._check_task:
            self._check_task.cancel()
            self._check_task = None

    async def _check_generations(self):
        """Periodically check subscribed generations and notify of updates."""
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            while True:
                try:
                    for prediction_id, sessions in list(self._subscriptions.items()):
                        try:
                            result = await client.get_prediction_status(prediction_id)
                            # Notify on completion or failure
                            if result["status"] in ["succeeded", "failed", "canceled"]:
                                # For succeeded generations with image output
                                if result["status"] == "succeeded" and result.get("output"):
                                    # For image generation models, output is typically a list with the image URL as first item
                                    image_url = (
                                        result["output"][0] if isinstance(result["output"], list) else result["output"]
                                    )

                                    # First send a notification with just the URL and metadata
                                    notification = ResourceUpdatedNotification(
                                        method="notifications/resources/updated",
                                        params={"uri": f"generations://{prediction_id}"},
                                    )

                                    # Create text resource with metadata and URL
                                    text_resource = TextResourceContents(
                                        type="text",
                                        uri=f"generations://{prediction_id}",
                                        mimeType="application/json",
                                        text=json.dumps(
                                            {
                                                "status": "succeeded",
                                                "image_url": image_url,
                                                "created_at": result.get("created_at"),
                                                "completed_at": result.get("completed_at"),
                                                "metrics": result.get("metrics", {}),
                                                "urls": result.get("urls", {}),
                                                "input": result.get("input", {}),
                                            },
                                            indent=2,
                                        ),
                                    )

                                    # Send notification and text resource to all sessions
                                    for session in sessions:
                                        await session.send_notification(notification)
                                        await session.send_resource(text_resource)

                                    # Remove from subscriptions since we've notified
                                    del self._subscriptions[prediction_id]
                                else:
                                    # For failed or canceled generations, create text resource
                                    resource = TextResourceContents(
                                        uri=f"generations://{prediction_id}",
                                        mimeType="application/json",
                                        text=json.dumps(
                                            {
                                                "status": result["status"],
                                                "error": result.get("error"),
                                                "created_at": result.get("created_at"),
                                                "completed_at": result.get("completed_at"),
                                                "metrics": result.get("metrics", {}),
                                                "urls": result.get("urls", {}),
                                            },
                                            indent=2,
                                        ),
                                    )

                                # Send notification with the resource
                                notification = ResourceUpdatedNotification(
                                    method="notifications/resources/updated",
                                    params={"uri": AnyUrl(f"generations://{prediction_id}")},
                                )
                                for session in sessions:
                                    await session.send_notification(notification)
                                    # Also send the resource directly
                                    await session.send_resource(resource)

                                # Remove completed/failed generation from subscriptions
                                del self._subscriptions[prediction_id]
                        except Exception as e:
                            logger.error(f"Error checking generation {prediction_id}: {e}")

                    if not self._subscriptions:
                        break

                    await asyncio.sleep(2.0)  # Poll every 2 seconds
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in generation check loop: {e}")
                    await asyncio.sleep(5.0)  # Back off on errors


async def select_model_for_task(
    task: str,
    style: str | None = None,
    quality: str = "balanced",
) -> tuple[Model, dict[str, Any]]:
    """Select the best model for a given task and get optimal parameters.

    Args:
        task: Task description/prompt
        style: Optional style preference
        quality: Quality preset (draft, balanced, quality, extreme)

    Returns:
        Tuple of (selected model, optimized parameters)
    """
    # Build search query
    search_query = task
    if style:
        search_query = f"{style} style {search_query}"

    # Search for models
    async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
        result = await client.search_models(search_query)

        if not result["models"]:
            raise ValueError("No suitable models found for the task")

        # Score and rank models
        scored_models = []
        for model in result["models"]:
            score = 0

            # Popularity score (0-50)
            run_count = model.get("run_count", 0)
            score += min(50, (run_count / 1000) * 50)

            # Featured bonus
            if model.get("featured"):
                score += 20

            # Version stability
            if model.get("latest_version"):
                score += 10

            # Tag matching
            tags = model.get("tags", [])
            if style and any(style.lower() in tag.lower() for tag in tags):
                score += 15
            if "image" in tags or "text-to-image" in tags:
                score += 15

            scored_models.append((model, score))

        # Sort by score
        scored_models.sort(key=lambda x: x[1], reverse=True)
        selected_model = scored_models[0][0]

        # Get quality preset
        quality_preset = TEMPLATES["quality-presets"]["presets"].get(
            quality, TEMPLATES["quality-presets"]["presets"]["balanced"]
        )

        # Get style preset if specified
        parameters = quality_preset["parameters"].copy()
        if style:
            style_preset = TEMPLATES["style-presets"]["presets"].get(
                style.lower(), TEMPLATES["style-presets"]["presets"].get("photorealistic")
            )
            if style_preset:
                parameters.update(style_preset["parameters"])

        return Model(**selected_model), parameters


class TemplateInput(BaseModel):
    """Input for template-based operations."""

    template: str = Field(..., description="Template identifier")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Template parameters")

    @field_validator("template")
    def validate_template(cls, v: str) -> str:
        """Validate template identifier."""
        if v not in TEMPLATES:
            raise ValueError(f"Unknown template: {v}")
        return v

    @field_validator("parameters")
    def validate_parameters(cls, v: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
        """Validate template parameters."""
        if "template" not in values:
            return v

        template = TEMPLATES[values["template"]]
        try:
            jsonschema.validate(v, template["parameter_schema"])
        except jsonschema.exceptions.ValidationError as e:
            raise ValueError(f"Invalid parameters: {e.message}") from e
        return v


class PredictionInput(BaseModel):
    """Input for prediction operations."""

    version: str = Field(..., description="Model version ID")
    input: dict[str, Any] = Field(..., description="Model input parameters")
    webhook: str | None = Field(None, description="Webhook URL for prediction updates")

    @field_validator("input")
    def validate_input(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate prediction input."""
        if not isinstance(v, dict):
            raise ValueError("Input must be a dictionary")
        return v


def create_server(*, log_level: int = logging.WARNING) -> FastMCP:
    """Create and configure the FastMCP server.

    Args:
        log_level: The logging level to use. Defaults to WARNING.

    Returns:
        Configured FastMCP server instance.
    """
    # Configure logging
    logging.basicConfig(level=log_level)
    logger.setLevel(log_level)

    # Verify API token is available
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        raise ValueError(
            "REPLICATE_API_TOKEN environment variable is required. " "Get your token from https://replicate.com/account"
        )

    # Create server instance
    mcp = FastMCP("Replicate Server")

    # Add resources
    @mcp.resource("templates://list")
    def list_available_templates() -> str:
        """List all available templates with descriptions."""
        template_info = []
        for name, template in TEMPLATES.items():
            template_info.append(
                f"Template: {name}\n"
                f"Description: {template.get('description', 'No description')}\n"
                f"Version: {template.get('version', '1.0.0')}\n"
                "---"
            )
        return "\n".join(template_info)

    @mcp.resource("templates://{name}")
    def get_template_details(name: str) -> str:
        """Get detailed information about a specific template."""
        if name not in TEMPLATES:
            raise ValueError(f"Template not found: {name}")

        template = TEMPLATES[name]
        return json.dumps(
            {
                "name": name,
                "description": template.get("description", ""),
                "version": template.get("version", "1.0.0"),
                "parameter_schema": template["parameter_schema"],
                "examples": template.get("examples", []),
            },
            indent=2,
        )

    @mcp.resource("generations://{prediction_id}")
    async def get_generation(prediction_id: str) -> TextResourceContents | BlobResourceContents:
        """Get a specific image generation result."""
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            result = await client.get_prediction_status(prediction_id)

            # If not succeeded, return status info
            if result["status"] != "succeeded":
                return TextResourceContents(
                    uri=f"generations://{prediction_id}",
                    mimeType="application/json",
                    text=json.dumps(
                        {
                            "status": result["status"],
                            "created_at": result.get("created_at"),
                            "started_at": result.get("started_at"),
                            "completed_at": result.get("completed_at"),
                            "error": result.get("error"),
                            "logs": result.get("logs"),
                            "urls": result.get("urls", {}),
                            "metrics": result.get("metrics", {}),
                        }
                    ),
                )

            # For succeeded generations, return image URL and metadata
            image_url = result["output"][0] if isinstance(result["output"], list) else result["output"]
            return TextResourceContents(
                uri=f"generations://{prediction_id}",
                mimeType="application/json",
                text=json.dumps(
                    {
                        "status": "succeeded",
                        "image_url": image_url,
                        "created_at": result.get("created_at"),
                        "completed_at": result.get("completed_at"),
                        "metrics": result.get("metrics", {}),
                        "urls": result.get("urls", {}),
                        "input": result.get("input", {}),
                    }
                ),
            )

    @mcp.resource("generations://list")
    async def list_generations() -> TextResourceContents:
        """List all available generations with their details and resource URIs."""
        async with ReplicateClient() as client:
            predictions = await client.list_predictions(limit=100)
            return TextResourceContents(
                uri="generations://list",
                mimeType="application/json",
                text=json.dumps(
                    {
                        "total_count": len(predictions),
                        "generations": [
                            {
                                "id": p["id"],
                                "status": p["status"],
                                "created_at": p.get("created_at"),
                                "completed_at": p.get("completed_at"),
                                "prompt": p.get("input", {}).get("prompt"),  # Extract prompt for easy reference
                                "style": p.get("input", {}).get("style"),  # Extract style for filtering
                                "quality": p.get("input", {}).get("quality", "balanced"),
                                "error": p.get("error"),
                                "resource_uri": f"generations://{p['id']}",
                                "metrics": p.get("metrics", {}),  # Include performance metrics
                                "urls": p.get("urls", {}),  # Include direct URLs
                            }
                            for p in predictions
                        ],
                    },
                    indent=2,
                ),
            )

    @mcp.resource("generations://search/{query}")
    async def search_generations(query: str) -> TextResourceContents:
        """Search through available generations by prompt text or metadata."""
        async with ReplicateClient() as client:
            predictions = await client.list_predictions(limit=100)
            # Improved search - check prompt, style, and quality
            filtered = []
            query_lower = query.lower()
            for p in predictions:
                input_data = p.get("input", {})
                searchable_text = (
                    f"{input_data.get('prompt', '')} {input_data.get('style', '')} {input_data.get('quality', '')}"
                )
                if query_lower in searchable_text.lower():
                    filtered.append(p)

            return TextResourceContents(
                uri=f"generations://search/{query}",
                mimeType="application/json",
                text=json.dumps(
                    {
                        "query": query,
                        "total_count": len(filtered),
                        "generations": [
                            {
                                "id": p["id"],
                                "status": p["status"],
                                "created_at": p.get("created_at"),
                                "completed_at": p.get("completed_at"),
                                "prompt": p.get("input", {}).get("prompt"),
                                "style": p.get("input", {}).get("style"),
                                "quality": p.get("input", {}).get("quality", "balanced"),
                                "error": p.get("error"),
                                "resource_uri": f"generations://{p['id']}",
                                "metrics": p.get("metrics", {}),
                                "urls": p.get("urls", {}),
                            }
                            for p in filtered
                        ],
                    },
                    indent=2,
                ),
            )

    @mcp.resource("generations://status/{status}")
    async def filter_generations_by_status(status: str) -> TextResourceContents:
        """Get generations filtered by status (starting, processing, succeeded, failed, canceled)."""
        async with ReplicateClient() as client:
            predictions = await client.list_predictions(status=status, limit=100)
            return TextResourceContents(
                uri=f"generations://status/{status}",
                mimeType="application/json",
                text=json.dumps(
                    {
                        "status": status,
                        "total_count": len(predictions),
                        "generations": [
                            {
                                "id": p["id"],
                                "created_at": p.get("created_at"),
                                "completed_at": p.get("completed_at"),
                                "prompt": p.get("input", {}).get("prompt"),
                                "style": p.get("input", {}).get("style"),
                                "quality": p.get("input", {}).get("quality", "balanced"),
                                "error": p.get("error"),
                                "resource_uri": f"generations://{p['id']}",
                                "metrics": p.get("metrics", {}),
                                "urls": p.get("urls", {}),
                            }
                            for p in predictions
                        ],
                    },
                    indent=2,
                ),
            )

    @mcp.resource("models://popular")
    async def get_popular_models() -> str:
        """Get a list of popular models on Replicate."""
        async with ReplicateClient() as client:
            models = await client.list_models()
            return json.dumps(
                {
                    "models": models["models"],
                    "total": models.get("total_models", 0),
                },
                indent=2,
            )

    # Add prompts
    @mcp.prompt()
    def text_to_image() -> Sequence[Message]:
        """Generate an image from text using available models."""
        return [
            UserMessage(
                content=TextContent(
                    type="text",
                    text=(
                        "I'll help you create an image using Replicate's SDXL model. "
                        "To get the best results, please tell me:\n\n"
                        "1. What you want to see in the image (be specific)\n"
                        "2. Style preferences (e.g., photorealistic, anime, oil painting)\n"
                        "3. Quality level (draft=fast, balanced=default, quality=better, extreme=best)\n"
                        "4. Any specific requirements (size, aspect ratio, etc.)\n\n"
                        "For example: 'Create a photorealistic mountain landscape at sunset with snow-capped peaks, "
                        "quality level, 16:9 aspect ratio'\n\n"
                        "Once you provide these details:\n"
                        "- I'll start the generation and provide real-time updates\n"
                        "- You can wait for completion or start another generation\n"
                        "- When ready, I can show you the image or open it on your system\n"
                        "- You can also browse, search, or manage your generations"
                    ),
                )
            )
        ]

    @mcp.prompt()
    def image_to_image() -> Sequence[Message]:
        """Transform an existing image using various models."""
        return [
            UserMessage(
                content=TextContent(
                    type="text",
                    text=(
                        "I'll help you transform an existing image using Replicate's models. "
                        "Please provide:\n\n"
                        "1. The URL or path to your source image\n"
                        "2. The type of transformation you want (e.g., style transfer, upscaling, inpainting)\n"
                        "3. Any specific settings or parameters\n\n"
                        "I'll help you choose the right model and format your request."
                    ),
                )
            )
        ]

    @mcp.prompt()
    def model_selection(task: str | None = None) -> Sequence[Message]:
        """Help choose the right model for a specific task."""
        base_prompt = (
            "I'll help you select the best Replicate model for your needs. "
            "Please tell me about your task and requirements, including:\n\n"
            "1. The type of input you have\n"
            "2. Your desired output\n"
            "3. Any specific quality or performance requirements\n"
            "4. Any budget or hardware constraints\n\n"
        )

        if task:
            base_prompt += f"\nFor {task}, I recommend considering these aspects:\n"
            if "image" in task.lower():
                base_prompt += (
                    "- Input/output image dimensions\n"
                    "- Style and quality requirements\n"
                    "- Processing speed needs\n"
                )
            elif "text" in task.lower():
                base_prompt += (
                    "- Input length considerations\n" "- Output format requirements\n" "- Specific language needs\n"
                )

        return [UserMessage(content=TextContent(type="text", text=base_prompt))]

    @mcp.prompt()
    def parameter_help(template: str | None = None) -> Sequence[Message]:
        """Get help with model parameters and templates."""
        if template and template in TEMPLATES:
            tmpl = TEMPLATES[template]
            text = (
                f"I'll help you with the {template} template.\n\n"
                f"Description: {tmpl.get('description', 'No description')}\n"
                "Required Parameters:\n"
                + "\n".join(
                    f"- {param}: {schema.get('description', 'No description')}"
                    for param, schema in tmpl["parameter_schema"]["properties"].items()
                    if param in tmpl["parameter_schema"].get("required", [])
                )
                + "\n\nOptional Parameters:\n"
                + "\n".join(
                    f"- {param}: {schema.get('description', 'No description')}"
                    for param, schema in tmpl["parameter_schema"]["properties"].items()
                    if param not in tmpl["parameter_schema"].get("required", [])
                )
            )
        else:
            text = (
                "I'll help you understand and configure model parameters. "
                "Please provide:\n\n"
                "1. The model or template you're using\n"
                "2. Any specific parameters you need help with\n"
                "3. Your use case or requirements\n\n"
                "I'll explain the parameters and suggest appropriate values."
            )

        return [UserMessage(content=TextContent(type="text", text=text))]

    @mcp.prompt()
    def after_generation() -> Sequence[Message]:
        """Prompt shown after starting an image generation."""
        return [
            UserMessage(
                content=TextContent(
                    type="text",
                    text=(
                        "Your image generation has started! You have several options:\n\n"
                        "1. Wait here - I'll check the progress and show you the image when it's ready\n"
                        "2. Browse your generations - I can show you a list of all your generations\n"
                        "3. Start another generation - We can create more images while this one processes\n\n"
                        "When the image is ready, I can:\n"
                        "- Show you the image directly\n"
                        "- Open it with your system's default image viewer\n"
                        "- Save it or share it\n"
                        "- Create variations or apply transformations\n\n"
                        "What would you like to do?"
                    ),
                )
            )
        ]

    # Model Discovery Tools
    @mcp.tool()
    async def list_models(owner: str | None = None) -> ModelList:
        """List available models on Replicate with optional filtering by owner."""
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            result = await client.list_models(owner=owner)
            return ModelList(
                models=[Model(**model) for model in result["models"]],
                next_cursor=result.get("next_cursor"),
                total_count=result.get("total_models"),
            )

    @mcp.tool()
    async def search_models(query: str) -> ModelList:
        """Search for models using semantic search."""
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            result = await client.search_models(query)
            models = [Model(**model) for model in result["models"]]

            # Sort by run count as a proxy for popularity/reliability
            models.sort(key=lambda m: m.run_count if m.run_count else 0, reverse=True)

            return ModelList(
                models=models, next_cursor=result.get("next_cursor"), total_count=result.get("total_models")
            )

    # Collection Management Tools
    @mcp.tool()
    async def list_collections() -> CollectionList:
        """List available model collections on Replicate."""
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            result = await client.list_collections()
            return CollectionList(collections=[Collection(**collection) for collection in result])

    @mcp.tool()
    async def get_collection_details(collection_slug: str) -> Collection:
        """Get detailed information about a specific collection."""
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            result = await client.get_collection(collection_slug)
            return Collection(**result)

    # Hardware Tools
    @mcp.tool()
    async def list_hardware() -> HardwareList:
        """List available hardware options for running models."""
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            result = await client.list_hardware()
            return HardwareList(hardware=[Hardware(**hw) for hw in result])

    # Template Tools
    @mcp.tool()
    def list_templates() -> dict[str, Any]:
        """List all available templates with their schemas."""
        return {
            name: {
                "schema": template["parameter_schema"],
                "description": template.get("description", ""),
                "version": template.get("version", "1.0.0"),
            }
            for name, template in TEMPLATES.items()
        }

    @mcp.tool()
    def validate_template_parameters(input: dict[str, Any]) -> bool:
        """Validate parameters against a template schema."""
        template_input = TemplateInput(**input)
        return True  # If we get here, validation passed

    # Prediction Tools
    @mcp.tool()
    async def create_prediction(input: dict[str, Any], confirmed: bool = False) -> dict[str, Any]:
        """Create a new prediction using a specific model version on Replicate.

        Args:
            input: Model input parameters including version or model details
            confirmed: Whether the user has explicitly confirmed the generation

        Returns:
            Prediction details if confirmed, or a confirmation request if not
        """
        # If not confirmed, return info about what will be generated
        if not confirmed:
            # Extract model info for display
            model_info = ""
            if "version" in input:
                model_info = f"version: {input['version']}"
            elif "model_owner" in input and "model_name" in input:
                model_info = f"model: {input['model_owner']}/{input['model_name']}"

            return {
                "requires_confirmation": True,
                "message": (
                    "⚠️ This will use Replicate credits to generate an image with these parameters:\n\n"
                    f"Model: {model_info}\n"
                    f"Prompt: {input.get('prompt', 'Not specified')}\n"
                    f"Quality: {input.get('quality', 'balanced')}\n\n"
                    "Please confirm if you want to proceed with the generation."
                ),
            }

        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            # If version is provided directly, use it
            if "version" in input:
                version = input.pop("version")
            # Otherwise, try to find the model and get its latest version
            elif "model_owner" in input and "model_name" in input:
                model_id = f"{input.pop('model_owner')}/{input.pop('model_name')}"
                search_result = await client.search_models(model_id)
                if not search_result["models"]:
                    raise ValueError(f"Model not found: {model_id}")
                model = search_result["models"][0]
                if not model.get("latest_version"):
                    raise ValueError(f"No versions found for model: {model_id}")
                version = model["latest_version"]["id"]
            else:
                raise ValueError("Must provide either 'version' or both 'model_owner' and 'model_name'")

            # Create prediction with remaining parameters as input
            result = await client.create_prediction(version=version, input=input, webhook=input.pop("webhook", None))

            # Return result with prompt about waiting
            return {
                **result,
                "_next_prompt": "after_generation",  # Signal to show the waiting prompt
            }

    @mcp.tool()
    async def get_prediction(prediction_id: str, wait: bool = False, max_retries: int | None = None) -> dict[str, Any]:
        """Get the status and results of a prediction."""
        consecutive_errors = 0

        while True:
            try:
                async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
                    response = await client.http_client.get(
                        f"/predictions/{prediction_id}",
                        headers={
                            "Authorization": f"Bearer {client.api_token}",
                            "Content-Type": "application/json",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    # Build URL message with all available links
                    urls_msg = []

                    # Add streaming URL if available
                    if data.get("urls", {}).get("stream"):
                        urls_msg.append(f"🔄 Stream URL: {data['urls']['stream']}")

                    # Add get URL if available
                    if data.get("urls", {}).get("get"):
                        urls_msg.append(f"📡 Status URL: {data['urls']['get']}")

                    # Add cancel URL if available and still processing
                    if data.get("urls", {}).get("cancel") and data["status"] in ["starting", "processing"]:
                        urls_msg.append(f"🛑 Cancel URL: {data['urls']['cancel']}")

                    # If prediction is complete and has an image output
                    if data["status"] == "succeeded" and data.get("output"):
                        # For image generation models, output is typically a list with the image URL as first item
                        image_url = data["output"][0] if isinstance(data["output"], list) else data["output"]

                        return {
                            "id": data["id"],
                            "status": "succeeded",
                            "image_url": image_url,
                            "resource_uri": f"generations://{prediction_id}",
                            "image_resource_uri": f"generations://{prediction_id}/image",
                            "created_at": data.get("created_at"),
                            "completed_at": data.get("completed_at"),
                            "metrics": data.get("metrics", {}),
                            "urls": data.get("urls", {}),
                            "message": (
                                "🎨 Generation completed successfully!\n\n"
                                f"You can:\n"
                                f"1. View the image at: {image_url}\n"
                                f"2. Open it with your system viewer (just ask me to open it)\n"
                                f"3. Access image data at: generations://{prediction_id}/image\n"
                                f"4. Get metadata at: generations://{prediction_id}\n"
                                f"5. Create variations or apply transformations\n\n"
                                "Would you like me to open the image for you?\n\n"
                                "Available URLs:\n" + "\n".join(urls_msg)
                            ),
                        }

                    # If prediction failed or was cancelled
                    if data["status"] in ["failed", "canceled"]:
                        error_msg = data.get("error", "No error details available")
                        return {
                            "id": data["id"],
                            "status": data["status"],
                            "error": error_msg,
                            "resource_uri": f"generations://{prediction_id}",
                            "created_at": data.get("created_at"),
                            "completed_at": data.get("completed_at"),
                            "metrics": data.get("metrics", {}),
                            "urls": data.get("urls", {}),
                            "message": (
                                f"❌ Generation {data['status']}: {error_msg}\n\n"
                                "Available URLs:\n" + "\n".join(urls_msg)
                            ),
                        }

                    # If we're still processing and not waiting, return status
                    if not wait:
                        return {
                            "id": data["id"],
                            "status": data["status"],
                            "resource_uri": f"generations://{prediction_id}",
                            "created_at": data.get("created_at"),
                            "started_at": data.get("started_at"),
                            "metrics": data.get("metrics", {}),
                            "urls": data.get("urls", {}),
                            "message": (
                                f"⏳ Generation is {data['status']}...\n"
                                "You can:\n"
                                "1. Keep waiting (I'll check again)\n"
                                "2. Use the URLs above to check progress yourself\n"
                                "3. Cancel the generation if needed"
                            ),
                        }

                    # Reset error count on successful request
                    consecutive_errors = 0

                    # Wait before polling again
                    await asyncio.sleep(2.0)  # Increased poll interval to reduce API load

            except Exception as e:
                logger.error(f"Error checking prediction status: {str(e)}")
                consecutive_errors += 1

                # Only stop if we have a max_retries set and exceeded it
                if max_retries is not None and consecutive_errors >= max_retries:
                    return {
                        "id": prediction_id,
                        "status": "error",
                        "error": str(e),
                        "resource_uri": f"generations://{prediction_id}",
                        "message": (
                            f"⚠️ Having trouble checking the prediction status (tried {consecutive_errors} times).\n\n"
                            f"The prediction might still be running! You can:\n"
                            "1. Try checking again in a few minutes\n"
                            "2. Visit the status URL directly: "
                            f"https://replicate.com/p/{prediction_id}\n"
                            "3. Start a new check with a higher retry limit\n\n"
                            f"Last error: {str(e)}"
                        ),
                    }

                # Wait with exponential backoff before retrying
                await asyncio.sleep(min(30, 2.0**consecutive_errors))  # Cap at 30 seconds

    @mcp.tool()
    async def cancel_prediction(prediction_id: str) -> dict[str, Any]:
        """Cancel a running prediction."""
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            response = await client.cancel_prediction(prediction_id)
            return await response.json()

    # Webhook Tools
    @mcp.tool()
    async def get_webhook_secret() -> str:
        """Get the signing secret for verifying webhook requests."""
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            return await client.get_webhook_secret()

    @mcp.tool()
    def verify_webhook(payload: WebhookPayload, signature: str, secret: str) -> bool:
        """Verify that a webhook request came from Replicate using HMAC-SHA256.

        Args:
            payload: The webhook payload to verify
            signature: The signature from the X-Replicate-Signature header
            secret: The webhook signing secret from get_webhook_secret

        Returns:
            True if signature is valid, False otherwise
        """
        if not signature or not secret:
            return False

        # Convert payload to canonical JSON string
        payload_str = json.dumps(payload.model_dump(), sort_keys=True)

        # Calculate expected signature
        expected = hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()

        # Compare signatures using constant-time comparison
        return hmac.compare_digest(signature, expected)

    @mcp.tool()
    async def search_available_models(
        query: str,
        style: str | None = None,
    ) -> ModelList:
        """Search for available models matching the query.

        Args:
            query: Search query describing the desired model
            style: Optional style to filter by

        Returns:
            List of matching models with scores
        """
        search_query = query
        if style:
            search_query = f"{style} style {search_query}"

        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            result = await client.search_models(search_query)
            models = [Model(**model) for model in result["models"]]

            # Score models but don't auto-select
            scored_models = []
            for model in models:
                score = 0
                run_count = getattr(model, "run_count", 0) or 0
                score += min(50, (run_count / 1000) * 50)
                if getattr(model, "featured", False):
                    score += 20
                if model.latest_version:
                    score += 10
                tags = getattr(model, "tags", [])
                if style and any(style.lower() in tag.lower() for tag in tags):
                    score += 15
                if "image" in tags or "text-to-image" in tags:
                    score += 15
                scored_models.append((model, score))

            # Sort by score but return all for user selection
            scored_models.sort(key=lambda x: x[1], reverse=True)
            return ModelList(
                models=[m[0] for m in scored_models],
                next_cursor=result.get("next_cursor"),
                total_count=result.get("total_count"),
            )

    @mcp.tool()
    async def get_model_details(model_id: str) -> Model:
        """Get detailed information about a specific model.

        Args:
            model_id: Model identifier in format owner/name

        Returns:
            Detailed model information
        """
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            result = await client.get_model_details(model_id)
            return Model(**result)

    @mcp.tool()
    async def generate_image(
        prompt: str,
        style: str | None = None,
        quality: str = "balanced",
        width: int | None = None,
        height: int | None = None,
        num_outputs: int = 1,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """Generate an image using the specified parameters."""
        # Get quality preset parameters
        if quality not in QUALITY_PRESETS["presets"]:
            quality = "balanced"
        parameters = QUALITY_PRESETS["presets"][quality]["parameters"].copy()

        # Apply style preset if specified
        if style:
            if style in STYLE_PRESETS["presets"]:
                style_params = STYLE_PRESETS["presets"][style]["parameters"]
                # Merge prompt prefixes
                if "prompt_prefix" in style_params:
                    prompt = f"{style_params['prompt_prefix']}, {prompt}"
                # Copy other parameters
                for k, v in style_params.items():
                    if k != "prompt_prefix":
                        parameters[k] = v

        # Override size if specified
        if width:
            parameters["width"] = width
        if height:
            parameters["height"] = height

        # Add other parameters
        parameters.update(
            {
                "prompt": prompt,
                "num_outputs": num_outputs,
            }
        )
        if seed is not None:
            parameters["seed"] = seed

        # Create prediction with SDXL model
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            result = await client.create_prediction(
                version="39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",  # SDXL v1.0
                input=parameters,
            )

            # Return resource information
            return {
                "resource_uri": f"generations://{result['id']}",
                "status": result["status"],
                "message": (
                    "🎨 Starting your image generation...\n\n"
                    f"Prompt: {prompt}\n"
                    f"Style: {style or 'Default'}\n"
                    f"Quality: {quality}\n\n"
                    "Let me check the status of your generation. I'll use:\n"
                    f"`get_prediction(\"{result['id']}\", wait=true)`\n\n"
                    "This will let me monitor the progress and show you the image as soon as it's ready."
                ),
                "next_prompt": "after_generation",
                "metadata": {  # Add metadata for client use
                    "prompt": prompt,
                    "style": style,
                    "quality": quality,
                    "width": width,
                    "height": height,
                    "seed": seed,
                    "model": "SDXL v1.0",
                    "created_at": result.get("created_at"),
                },
            }

    # Initialize subscription manager
    subscription_manager = GenerationSubscriptionManager()

    @mcp.tool()
    async def subscribe_to_generation(request: SubscriptionRequest) -> EmptyResult:
        """Handle resource subscription requests."""
        if request.uri.startswith("generations://"):
            session = ServerSession(request.session_id)
            await subscription_manager.subscribe(request.uri, session)
        return EmptyResult()

    @mcp.tool()
    async def unsubscribe_from_generation(request: SubscriptionRequest) -> EmptyResult:
        """Handle resource unsubscribe requests."""
        if request.uri.startswith("generations://"):
            session = ServerSession(request.session_id)
            await subscription_manager.unsubscribe(request.uri, session)
        return EmptyResult()

    @mcp.resource("generations://{prediction_id}/image")
    async def get_generation_image(prediction_id: str) -> BlobResourceContents:
        """Get the image data for a completed generation."""
        async with ReplicateClient(api_token=os.getenv("REPLICATE_API_TOKEN")) as client:
            result = await client.get_prediction_status(prediction_id)

            if result["status"] != "succeeded":
                raise ValueError(f"Generation not completed: {result['status']}")

            if not result.get("output"):
                raise ValueError("No image output available")

            # Get image URL
            image_url = result["output"][0] if isinstance(result["output"], list) else result["output"]

            # Download image
            async with httpx.AsyncClient() as http_client:
                img_response = await http_client.get(image_url)
                img_response.raise_for_status()

                # Determine mime type from URL extension
                ext = image_url.split(".")[-1].lower()
                mime_type = {
                    "png": "image/png",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "gif": "image/gif",
                    "webp": "image/webp",
                }.get(ext, "image/png")

                # Return blob contents
                return BlobResourceContents(
                    type="blob",
                    mimeType=mime_type,
                    uri=image_url,
                    blob=base64.b64encode(img_response.content).decode("ascii"),
                    description="Generated image data",
                )

    @mcp.tool()
    async def open_image_with_system(image_url: str) -> dict[str, Any]:
        """Open an image URL with the system's default application.

        Args:
            image_url: URL of the image to open

        Returns:
            Dict containing status of the operation
        """
        try:
            # Open URL directly with system default
            webbrowser.open(image_url)

            return {"status": "success", "message": "Image opened with system default application", "url": image_url}
        except Exception as e:
            logger.error(f"Failed to open image: {str(e)}")
            return {"status": "error", "message": f"Failed to open image: {str(e)}", "url": image_url}

    return mcp
