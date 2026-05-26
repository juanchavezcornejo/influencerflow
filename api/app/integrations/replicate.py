"""Replicate API wrapper for model inference with caching."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any

import httpx

from app.config import settings


class ReplicateClient:
    """Wrapper around Replicate API with caching and concurrency control."""

    _semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests

    def __init__(self, cache_repo=None):
        self.api_token = settings.replicate_api_key
        self.cache_repo = cache_repo
        self.base_url = "https://api.replicate.com/v1"

    async def run(
        self,
        model: str,
        inputs: dict[str, Any],
        webhook_events_filter: list[str] | None = None,
    ) -> dict:
        """
        Run a model on Replicate with caching and polling.

        Args:
            model: Model version ID (e.g., "stability-ai/sdxl:...")
            inputs: Input dict for the model
            webhook_events_filter: Optional webhook events to track

        Returns:
            Result dict with output, cost, etc.
        """
        # Generate cache key
        cache_key = self._generate_cache_key(model, inputs)

        # Check cache
        if self.cache_repo:
            cached_result = await self.cache_repo.get(cache_key)
            if cached_result:
                return cached_result

        # Use semaphore to limit concurrency
        async with self._semaphore:
            result = await self._create_and_poll_prediction(model, inputs)

        # Cache result
        if self.cache_repo and "error" not in result:
            await self.cache_repo.set(cache_key, result)

        return result

    async def _create_and_poll_prediction(self, model: str, inputs: dict) -> dict:
        """Create prediction and poll until complete."""
        try:
            # Create prediction
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/predictions",
                    json={"version": model, "input": inputs},
                    headers={"Authorization": f"Token {self.api_token}"},
                    timeout=30.0,
                )
                response.raise_for_status()
                prediction = response.json()

            prediction_id = prediction["id"]

            # Poll until complete
            max_wait = 600  # 10 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/predictions/{prediction_id}",
                        headers={"Authorization": f"Token {self.api_token}"},
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    prediction = response.json()

                status = prediction.get("status")

                if status == "succeeded":
                    return {
                        "output": prediction.get("output"),
                        "status": "success",
                        "model": model,
                        "prediction_id": prediction_id,
                    }
                elif status == "failed":
                    return {
                        "error": prediction.get("error", "Prediction failed"),
                        "status": "failed",
                        "model": model,
                        "prediction_id": prediction_id,
                    }
                elif status == "canceled":
                    return {
                        "error": "Prediction canceled",
                        "status": "canceled",
                        "model": model,
                        "prediction_id": prediction_id,
                    }

                # Wait before polling again
                await asyncio.sleep(2)

            return {
                "error": "Prediction timeout",
                "status": "timeout",
                "model": model,
                "prediction_id": prediction_id,
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "error",
                "model": model,
            }

    def _generate_cache_key(self, model: str, inputs: dict) -> str:
        """Generate SHA256 cache key from model and inputs."""
        cache_input = json.dumps(
            {
                "model": model,
                "inputs": inputs,
            },
            sort_keys=True,
        )
        return hashlib.sha256(cache_input.encode()).hexdigest()
