"""FastMCP tools for managing Replicate webhooks."""

from typing import Any

from mcp.server.fastmcp import FastMCP
from ..models.webhook import WebhookEvent, WebhookPayload

mcp = FastMCP()

@mcp.tool(
    name="get_webhook_secret",
    description="Get the signing secret for verifying webhook requests.",
)
async def get_webhook_secret() -> str:
    """Get webhook signing secret."""
    raise NotImplementedError

@mcp.tool(
    name="verify_webhook",
    description="Verify that a webhook request came from Replicate.",
)
async def verify_webhook(
    payload: WebhookPayload,
    signature: str,
    secret: str,
) -> bool:
    """Verify webhook signature."""
    raise NotImplementedError 