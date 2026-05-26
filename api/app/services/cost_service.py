"""Cost estimation service."""

from __future__ import annotations

from typing import Any


class CostEstimator:
    """Service for estimating API costs."""

    # Pricing (in dollars)
    CLAUDE_OPUS_INPUT_1M = 0.015  # $0.015 per 1M input tokens
    CLAUDE_OPUS_OUTPUT_1M = 0.045  # $0.045 per 1M output tokens
    CLAUDE_HAIKU_INPUT_1M = 0.0008  # $0.0008 per 1M input tokens
    CLAUDE_HAIKU_OUTPUT_1M = 0.0024  # $0.0024 per 1M output tokens

    REPLICATE_LAMA = 0.01  # LaMa inpainting per call
    REPLICATE_GFPGAN = 0.005  # GFPGAN per call

    @staticmethod
    def estimate(operation: str, inputs: dict[str, Any]) -> dict:
        """
        Estimate cost for an operation.

        Returns:
            {tokens_in, tokens_out, dollars}
        """
        if operation == "object_removal":
            # LaMa inpainting
            return {
                "tokens_in": 0,
                "tokens_out": 0,
                "dollars": CostEstimator.REPLICATE_LAMA,
                "model": "lama",
            }

        elif operation == "color_ai":
            # Claude vision analysis of one image
            estimated_tokens_in = 2000  # ~2K tokens for image + prompt
            estimated_tokens_out = 500  # ~500 tokens for suggestion
            dollars = (estimated_tokens_in / 1_000_000) * CostEstimator.CLAUDE_OPUS_INPUT_1M + (
                estimated_tokens_out / 1_000_000
            ) * CostEstimator.CLAUDE_OPUS_OUTPUT_1M
            return {
                "tokens_in": estimated_tokens_in,
                "tokens_out": estimated_tokens_out,
                "dollars": dollars,
                "model": "claude-opus-4-7",
            }

        elif operation == "crop_ai":
            # Claude composition analysis
            estimated_tokens_in = 1500
            estimated_tokens_out = 300
            dollars = (estimated_tokens_in / 1_000_000) * CostEstimator.CLAUDE_OPUS_INPUT_1M + (
                estimated_tokens_out / 1_000_000
            ) * CostEstimator.CLAUDE_OPUS_OUTPUT_1M
            return {
                "tokens_in": estimated_tokens_in,
                "tokens_out": estimated_tokens_out,
                "dollars": dollars,
                "model": "claude-opus-4-7",
            }

        elif operation == "description":
            # Claude caption generation with tile-packed images
            # Assume 4-9 images + text
            estimated_tokens_in = 4000
            estimated_tokens_out = 200
            dollars = (estimated_tokens_in / 1_000_000) * CostEstimator.CLAUDE_OPUS_INPUT_1M + (
                estimated_tokens_out / 1_000_000
            ) * CostEstimator.CLAUDE_OPUS_OUTPUT_1M
            return {
                "tokens_in": estimated_tokens_in,
                "tokens_out": estimated_tokens_out,
                "dollars": dollars,
                "model": "claude-opus-4-7",
            }

        elif operation == "nima":
            # NIMA aesthetic scoring via Replicate
            num_images = inputs.get("num_images", 1)
            return {
                "tokens_in": 0,
                "tokens_out": 0,
                "dollars": 0.001 * num_images,  # ~$0.001 per image
                "model": "nima",
            }

        else:
            # Unknown operation
            return {
                "tokens_in": 0,
                "tokens_out": 0,
                "dollars": 0.0,
                "model": "unknown",
            }
