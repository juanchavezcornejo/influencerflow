"""Claude API wrapper for calling Anthropic models with caching."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from anthropic import Anthropic

from app.config import settings


class ClaudeClient:
    """Wrapper around Anthropic SDK with caching support."""

    def __init__(self, api_key: str | None = None, cache_repo=None):
        self.client = Anthropic(api_key=api_key or settings.anthropic_api_key)
        self.cache_repo = cache_repo

    async def call(
        self,
        prompt_name: str,
        prompt_version: str,
        variables: dict[str, Any],
        model: str = "claude-opus-4-7",
        vision_content: list | None = None,
    ) -> dict:
        """
        Call Claude API with optional caching.

        Args:
            prompt_name: Name of the prompt (e.g., "OBJECT_REMOVAL_V1")
            prompt_version: Version string
            variables: Variables to interpolate in prompt
            model: Model to use
            vision_content: Optional list of image content objects

        Returns:
            Response dict with text and usage info
        """
        # Generate cache key from inputs
        cache_key = self._generate_cache_key(prompt_name, prompt_version, variables, vision_content)

        # Check cache
        if self.cache_repo:
            cached_response = await self.cache_repo.get(cache_key)
            if cached_response:
                return cached_response

        # Build messages
        messages = self._build_messages(variables, vision_content)

        try:
            # Call Claude
            response = self.client.messages.create(
                model=model,
                max_tokens=2048,
                messages=messages,
            )

            # Extract response
            result = {
                "text": response.content[0].text if response.content else "",
                "model": model,
                "tokens_in": response.usage.input_tokens,
                "tokens_out": response.usage.output_tokens,
                "cache_key": cache_key,
            }

            # Cache result
            if self.cache_repo:
                await self.cache_repo.set(
                    cache_key,
                    result,
                    model_used=model,
                    tokens_in=response.usage.input_tokens,
                    tokens_out=response.usage.output_tokens,
                )

            return result

        except Exception as e:
            return {
                "error": str(e),
                "model": model,
                "cache_key": cache_key,
            }

    def _generate_cache_key(
        self,
        prompt_name: str,
        prompt_version: str,
        variables: dict,
        vision_content: list | None,
    ) -> str:
        """Generate SHA256 cache key from inputs."""
        cache_input = json.dumps(
            {
                "prompt_name": prompt_name,
                "prompt_version": prompt_version,
                "variables": variables,
                "vision_content_count": len(vision_content) if vision_content else 0,
            },
            sort_keys=True,
        )
        return hashlib.sha256(cache_input.encode()).hexdigest()

    def _build_messages(self, variables: dict, vision_content: list | None = None) -> list:
        """Build message list for Claude API."""
        user_content = []

        # Add text from variables
        if "prompt_text" in variables:
            user_content.append(
                {
                    "type": "text",
                    "text": variables["prompt_text"],
                }
            )

        # Add vision content if provided
        if vision_content:
            user_content.extend(vision_content)

        return [
            {
                "role": "user",
                "content": user_content
                if user_content
                else [{"type": "text", "text": "Process this request."}],
            }
        ]
