"""Replicate API client implementation."""

import logging
import os
import time
from typing import Any, Optional, Dict, AsyncGenerator
import asyncio
import random

import httpx
import replicate

logger = logging.getLogger(__name__)

# Constants
REPLICATE_API_BASE = "https://api.replicate.com/v1"
DEFAULT_TIMEOUT = 60.0
MAX_RETRIES = 3
MIN_RETRY_DELAY = 1.0
MAX_RETRY_DELAY = 10.0
DEFAULT_RATE_LIMIT = 100  # requests per minute

class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: float):
        """Initialize with retry after duration."""
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")

class ReplicateClient:
    """Client for interacting with the Replicate API."""

    def __init__(self, api_token: str | None = None) -> None:
        """Initialize the Replicate client.

        Args:
            api_token: Replicate API token for authentication
        """
        self.client = None
        self.error = None
        self.api_token = api_token
        self._rate_limit = DEFAULT_RATE_LIMIT
        self._request_times: list[float] = []
        self._retry_count = 0
        self.http_client = None  # Initialize to None, will be set up in __aenter__

        if not api_token or not api_token.strip():
            self.error = "Replicate API token is required"
            return

        os.environ["REPLICATE_API_TOKEN"] = api_token
        self.client = replicate.Client()

    async def __aenter__(self):
        """Async context manager entry."""
        # Initialize httpx client for direct API calls
        self.http_client = httpx.AsyncClient(
            base_url=REPLICATE_API_BASE,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            timeout=DEFAULT_TIMEOUT
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None

    async def _ensure_http_client(self):
        """Ensure http_client is initialized."""
        if not self.http_client:
            self.http_client = httpx.AsyncClient(
                base_url=REPLICATE_API_BASE,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                },
                timeout=DEFAULT_TIMEOUT
            )

    async def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to comply with rate limiting."""
        now = time.time()
        
        # Remove request times older than 1 minute
        self._request_times = [t for t in self._request_times if now - t <= 60]
        
        if len(self._request_times) >= self._rate_limit:
            # Calculate wait time based on oldest request
            wait_time = 60 - (now - self._request_times[0])
            if wait_time > 0:
                logger.debug(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        self._request_times.append(now)

    async def _handle_response(self, response: httpx.Response) -> None:
        """Handle rate limits and other response headers.
        
        Args:
            response: The HTTP response to handle
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        # Update rate limit from headers if available
        if "X-RateLimit-Limit" in response.headers:
            self._rate_limit = int(response.headers["X-RateLimit-Limit"])
        
        # Handle rate limit exceeded
        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", 60))
            raise RateLimitExceeded(retry_after)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any
    ) -> httpx.Response:
        """Make an HTTP request with retries and rate limiting.
        
        Args:
            method: HTTP method to use
            endpoint: API endpoint to call
            **kwargs: Additional arguments to pass to httpx
            
        Returns:
            HTTP response
            
        Raises:
            Exception: If the request fails after retries
        """
        await self._wait_for_rate_limit()
        
        for attempt in range(MAX_RETRIES):
            try:
                response = await self.http_client.request(method, endpoint, **kwargs)
                await self._handle_response(response)
                response.raise_for_status()
                self._retry_count = 0  # Reset on success
                return response
                
            except RateLimitExceeded as e:
                logger.warning(f"Rate limit exceeded. Waiting {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after)
                continue
                
            except httpx.HTTPError as e:
                self._retry_count += 1
                if attempt == MAX_RETRIES - 1:
                    raise
                
                # Calculate exponential backoff with jitter
                delay = min(
                    MAX_RETRY_DELAY,
                    MIN_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                )
                logger.warning(
                    f"Request failed: {str(e)}. "
                    f"Retrying in {delay:.2f} seconds "
                    f"(attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(delay)
                continue

    def list_models(self, owner: str | None = None, cursor: str | None = None) -> dict[str, Any]:
        """List available models on Replicate with pagination.

        Args:
            owner: Optional owner username to filter models
            cursor: Pagination cursor from previous response

        Returns:
            Dict containing models list, next cursor, and total count

        Raises:
            Exception: If the API request fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        try:
            # Build params dict only including cursor if provided
            params = {}
            if cursor:
                params["cursor"] = cursor
            
            # Get models collection with pagination
            models = self.client.models.list(**params)

            # Get pagination info
            next_cursor = models.next_cursor if hasattr(models, "next_cursor") else None
            total_models = models.total if hasattr(models, "total") else None

            # Filter by owner if specified
            if owner:
                models = [m for m in models if m.owner == owner]

            # Format models with complete structure
            formatted_models = []
            for model in models:
                model_data = {
                    "id": f"{model.owner}/{model.name}",
                    "owner": model.owner,
                    "name": model.name,
                    "description": model.description,
                    "visibility": model.visibility,
                    "github_url": getattr(model, "github_url", None),
                    "paper_url": getattr(model, "paper_url", None),
                    "license_url": getattr(model, "license_url", None),
                    "run_count": getattr(model, "run_count", None),
                    "cover_image_url": getattr(model, "cover_image_url", None),
                    "default_example": getattr(model, "default_example", None),
                    "featured": getattr(model, "featured", None),
                    "tags": getattr(model, "tags", []),
                }

                # Add latest version info if available
                if model.latest_version:
                    model_data["latest_version"] = {
                        "id": model.latest_version.id,
                        "created_at": model.latest_version.created_at,
                        "cog_version": model.latest_version.cog_version,
                        "openapi_schema": model.latest_version.openapi_schema,
                        "model": f"{model.owner}/{model.name}",
                        "replicate_version": getattr(model.latest_version, "replicate_version", None),
                        "hardware": getattr(model.latest_version, "hardware", None),
                    }

                formatted_models.append(model_data)

            return {
                "models": formatted_models,
                "next_cursor": next_cursor,
                "total_count": total_models,
            }

        except Exception as err:
            logger.error(f"Failed to list models: {str(err)}")
            raise Exception(f"Failed to list models: {str(err)}") from err

    def get_model_versions(self, model: str) -> list[dict[str, Any]]:
        """Get available versions for a model.

        Args:
            model: Model identifier in format 'owner/model'

        Returns:
            List of model versions with their metadata

        Raises:
            ValueError: If the model is not found
            Exception: If the API request fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        try:
            # Get model
            model_obj = self.client.models.get(model)
            if not model_obj:
                raise ValueError(f"Model not found: {model}")

            # Get versions
            versions = model_obj.versions.list()

            # Return minimal version metadata
            return [
                {
                    "id": version.id,
                    "created_at": version.created_at.isoformat() if version.created_at else None,
                    "cog_version": version.cog_version,
                    "openapi_schema": version.openapi_schema,
                }
                for version in versions
            ]

        except ValueError as err:
            logger.error(f"Validation error: {str(err)}")
            raise
        except Exception as err:
            logger.error(f"Failed to get model versions: {str(err)}")
            raise Exception(f"Failed to get model versions: {str(err)}") from err

    async def predict(
        self,
        model: str,
        input_data: dict[str, Any],
        version: str | None = None,
        wait: bool = False,
        wait_timeout: int | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Run a prediction using a Replicate model.

        Args:
            model: Model identifier in format 'owner/model'
            input_data: Model-specific input parameters
            version: Optional model version hash
            wait: Whether to wait for prediction completion
            wait_timeout: Max seconds to wait if wait=True (1-60)
            stream: Whether to request streaming output

        Returns:
            Dict containing prediction details and optional stream URL

        Raises:
            ValueError: If the model or version is not found
            Exception: If the prediction fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        try:
            # Validate wait_timeout
            if wait and wait_timeout:
                if not 1 <= wait_timeout <= 60:
                    raise ValueError("wait_timeout must be between 1 and 60 seconds")

            # Get model
            model_obj = self.client.models.get(model)
            if not model_obj:
                raise ValueError(f"Model not found: {model}")

            # Get specific version or latest
            if version:
                model_version = model_obj.versions.get(version)
                if not model_version:
                    raise ValueError(f"Version not found: {version}")
            else:
                model_version = model_obj.latest_version

            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            if wait:
                if wait_timeout:
                    headers["Prefer"] = f"wait={wait_timeout}"
                else:
                    headers["Prefer"] = "wait"

            # Prepare request body
            body = {
                "input": input_data,
                "stream": stream,
            }
            if version:
                body["version"] = version

            # Create prediction using rate-limited request
            response = await self._make_request(
                "POST",
                "/predictions",
                headers=headers,
                json=body
            )
            data = response.json()

            # Format response
            result = {
                "id": data["id"],
                "status": data["status"],
                "input": data["input"],
                "output": data.get("output"),
                "error": data.get("error"),
                "logs": data.get("logs"),
                "created_at": data.get("created_at"),
                "started_at": data.get("started_at"),
                "completed_at": data.get("completed_at"),
                "urls": data.get("urls", {}),
            }

            # Add metrics if available
            if "metrics" in data:
                result["metrics"] = data["metrics"]

            # Add stream URL if requested and available
            if stream and "urls" in data and "stream" in data["urls"]:
                result["stream_url"] = data["urls"]["stream"]

            return result

        except ValueError as err:
            logger.error(f"Validation error: {str(err)}")
            raise
        except httpx.HTTPError as err:
            logger.error(f"HTTP error during prediction: {str(err)}")
            raise Exception(f"Prediction failed: {str(err)}") from err
        except Exception as err:
            logger.error(f"Prediction failed: {str(err)}")
            raise Exception(f"Prediction failed: {str(err)}") from err

    def get_prediction_status(self, prediction_id: str) -> dict[str, Any]:
        """Get the status of a prediction.

        Args:
            prediction_id: ID of the prediction to check

        Returns:
            Dict containing current status and output of the prediction

        Raises:
            ValueError: If the prediction is not found
            Exception: If the API request fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        try:
            # Get prediction
            prediction = self.client.predictions.get(prediction_id)
            if not prediction:
                raise ValueError(f"Prediction not found: {prediction_id}")

            # Return prediction status and output
            return {
                "id": prediction.id,
                "status": prediction.status,
                "output": prediction.output,
                "error": prediction.error,
                "created_at": prediction.created_at.isoformat() if prediction.created_at else None,
                "started_at": prediction.started_at.isoformat() if prediction.started_at else None,
                "completed_at": prediction.completed_at.isoformat() if prediction.completed_at else None,
                "urls": prediction.urls,
                "metrics": prediction.metrics,
            }

        except ValueError as err:
            logger.error(f"Validation error: {str(err)}")
            raise
        except Exception as err:
            logger.error(f"Failed to get prediction status: {str(err)}")
            raise Exception(f"Failed to get prediction status: {str(err)}") from err

    async def search_models(
        self, 
        query: str,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """Search for models using the QUERY endpoint.
        
        Args:
            query: Search query string
            cursor: Optional pagination cursor
            
        Returns:
            Dict containing search results with pagination info
            
        Raises:
            Exception: If the API request fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        try:
            # Build URL with cursor if provided
            url = "/models"
            if cursor:
                url = f"{url}?cursor={cursor}"
                
            # Make QUERY request
            response = await self.http_client.request(
                "QUERY",
                url,
                content=query,
                headers={"Content-Type": "text/plain"}
            )
            response.raise_for_status()
            data = response.json()
            
            # Format response with complete model structure
            return {
                "models": [
                    {
                        "id": f"{model['owner']}/{model['name']}",
                        "owner": model["owner"],
                        "name": model["name"],
                        "description": model.get("description"),
                        "visibility": model.get("visibility", "public"),
                        "github_url": model.get("github_url"),
                        "paper_url": model.get("paper_url"),
                        "license_url": model.get("license_url"),
                        "run_count": model.get("run_count"),
                        "cover_image_url": model.get("cover_image_url"),
                        "default_example": model.get("default_example"),
                        "featured": model.get("featured", False),
                        "tags": model.get("tags", []),
                        "latest_version": model.get("latest_version", {
                            "id": model.get("latest_version", {}).get("id"),
                            "created_at": model.get("latest_version", {}).get("created_at"),
                            "cog_version": model.get("latest_version", {}).get("cog_version"),
                            "openapi_schema": model.get("latest_version", {}).get("openapi_schema"),
                            "model": f"{model['owner']}/{model['name']}",
                            "replicate_version": model.get("latest_version", {}).get("replicate_version"),
                            "hardware": model.get("latest_version", {}).get("hardware"),
                        } if model.get("latest_version") else None),
                    }
                    for model in data.get("results", [])
                ],
                "next_cursor": data.get("next"),
                "total_count": data.get("total"),
            }

        except httpx.HTTPError as err:
            logger.error(f"HTTP error during model search: {str(err)}")
            raise Exception(f"Failed to search models: {str(err)}") from err
        except Exception as err:
            logger.error(f"Failed to search models: {str(err)}")
            raise Exception(f"Failed to search models: {str(err)}") from err

    async def list_hardware(self) -> list[dict[str, str]]:
        """Get list of available hardware options for running models.
        
        Returns:
            List of hardware options with name and SKU
            
        Raises:
            Exception: If the API request fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        try:
            response = await self.http_client.get("/hardware")
            response.raise_for_status()
            
            return [
                {
                    "name": hw["name"],
                    "sku": hw["sku"],
                }
                for hw in response.json()
            ]

        except httpx.HTTPError as err:
            logger.error(f"HTTP error getting hardware options: {str(err)}")
            raise Exception(f"Failed to get hardware options: {str(err)}") from err
        except Exception as err:
            logger.error(f"Failed to get hardware options: {str(err)}")
            raise Exception(f"Failed to get hardware options: {str(err)}") from err

    async def list_collections(self) -> list[dict[str, Any]]:
        """Get list of available model collections.
        
        Returns:
            List of collections with their metadata
            
        Raises:
            Exception: If the API request fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        try:
            response = await self.http_client.get("/collections")
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "name": collection["name"],
                    "slug": collection["slug"],
                    "description": collection.get("description"),
                }
                for collection in data.get("results", [])
            ]

        except httpx.HTTPError as err:
            logger.error(f"HTTP error listing collections: {str(err)}")
            raise Exception(f"Failed to list collections: {str(err)}") from err
        except Exception as err:
            logger.error(f"Failed to list collections: {str(err)}")
            raise Exception(f"Failed to list collections: {str(err)}") from err

    async def get_collection(self, collection_slug: str) -> dict[str, Any]:
        """Get details of a specific collection including its models.
        
        Args:
            collection_slug: The slug identifier of the collection
            
        Returns:
            Collection details including contained models
            
        Raises:
            ValueError: If the collection is not found
            Exception: If the API request fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        try:
            response = await self.http_client.get(f"/collections/{collection_slug}")
            response.raise_for_status()
            data = response.json()
            
            return {
                "name": data["name"],
                "slug": data["slug"],
                "description": data.get("description"),
                "models": [
                    {
                        "id": f"{model['owner']}/{model['name']}",
                        "owner": model["owner"],
                        "name": model["name"],
                        "description": model.get("description"),
                        "visibility": model.get("visibility", "public"),
                        "latest_version": model.get("latest_version"),
                    }
                    for model in data.get("models", [])
                ]
            }

        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                raise ValueError(f"Collection not found: {collection_slug}")
            logger.error(f"HTTP error getting collection: {str(err)}")
            raise Exception(f"Failed to get collection: {str(err)}") from err
        except Exception as err:
            logger.error(f"Failed to get collection: {str(err)}")
            raise Exception(f"Failed to get collection: {str(err)}") from err

    async def get_webhook_secret(self) -> str:
        """Get the signing secret for the default webhook endpoint.
        
        This secret is used to verify that webhook requests are coming from Replicate.
        
        Returns:
            The webhook signing secret
            
        Raises:
            Exception: If the API request fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        try:
            response = await self.http_client.get("/webhooks/default/secret")
            response.raise_for_status()
            data = response.json()
            
            return data["key"]

        except httpx.HTTPError as err:
            logger.error(f"HTTP error getting webhook secret: {str(err)}")
            raise Exception(f"Failed to get webhook secret: {str(err)}") from err
        except Exception as err:
            logger.error(f"Failed to get webhook secret: {str(err)}")
            raise Exception(f"Failed to get webhook secret: {str(err)}") from err

    async def cancel_prediction(self, prediction_id: str) -> dict[str, Any]:
        """Cancel a running prediction.
        
        Args:
            prediction_id: The ID of the prediction to cancel
            
        Returns:
            Dict containing the updated prediction status
            
        Raises:
            ValueError: If the prediction is not found
            Exception: If the cancellation fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        try:
            response = await self.http_client.post(
                f"/predictions/{prediction_id}/cancel",
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                }
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                raise ValueError(f"Prediction not found: {prediction_id}")
            logger.error(f"Failed to cancel prediction: {str(err)}")
            raise Exception(f"Failed to cancel prediction: {str(err)}") from err
        except Exception as err:
            logger.error(f"Failed to cancel prediction: {str(err)}")
            raise Exception(f"Failed to cancel prediction: {str(err)}") from err

    async def list_predictions(
        self,
        status: str | None = None,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """List recent predictions with optional filtering.
        
        Args:
            status: Optional status to filter by (starting|processing|succeeded|failed|canceled)
            limit: Maximum number of predictions to return (1-100)
            
        Returns:
            List of prediction objects
            
        Raises:
            ValueError: If limit is out of range
            Exception: If the API request fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")

        try:
            params = {"limit": limit}
            if status:
                params["status"] = status

            response = await self.http_client.get(
                "/predictions",
                params=params,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                }
            )
            response.raise_for_status()
            return response.json()

        except Exception as err:
            logger.error(f"Failed to list predictions: {str(err)}")
            raise Exception(f"Failed to list predictions: {str(err)}") from err

    async def create_prediction(
        self,
        version: str,
        input: Dict[str, Any],
        webhook: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new prediction using a model version.

        Args:
            version: Model version ID
            input: Model input parameters
            webhook: Optional webhook URL for prediction updates

        Returns:
            Dict containing prediction details

        Raises:
            Exception: If the prediction creation fails
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Check error property for details.")

        try:
            await self._ensure_http_client()
            
            # Prepare request body
            body = {
                "version": version,
                "input": input,
            }
            if webhook:
                body["webhook"] = webhook

            # Create prediction using rate-limited request
            response = await self._make_request(
                "POST",
                "/predictions",
                json=body
            )
            data = response.json()

            # Format response
            result = {
                "id": data["id"],
                "status": data["status"],
                "input": data["input"],
                "output": data.get("output"),
                "error": data.get("error"),
                "logs": data.get("logs"),
                "created_at": data.get("created_at"),
                "started_at": data.get("started_at"),
                "completed_at": data.get("completed_at"),
                "urls": data.get("urls", {}),
            }

            # Add metrics if available
            if "metrics" in data:
                result["metrics"] = data["metrics"]

            return result

        except Exception as err:
            logger.error(f"Failed to create prediction: {str(err)}")
            raise Exception(f"Failed to create prediction: {str(err)}") from err
