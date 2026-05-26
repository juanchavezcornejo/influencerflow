"""Mock implementations of external services for end-to-end testing.

These replace Google Drive, Claude, and Replicate with fake implementations
that return canned responses using fixture images and hardcoded data.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "images"

FIXTURE_FILES = [
    {
        "id": "fix-01",
        "name": "rome_colosseum_01.jpg",
        "local_path": str(FIXTURES_DIR / "rome_colosseum_01.jpg"),
        "mimeType": "image/jpeg",
    },
    {
        "id": "fix-02",
        "name": "rome_colosseum_02.jpg",
        "local_path": str(FIXTURES_DIR / "rome_colosseum_02.jpg"),
        "mimeType": "image/jpeg",
    },
    {
        "id": "fix-03",
        "name": "rome_colosseum_03.jpg",
        "local_path": str(FIXTURES_DIR / "rome_colosseum_03.jpg"),
        "mimeType": "image/jpeg",
    },
    {
        "id": "fix-04",
        "name": "rome_vatican_01.jpg",
        "local_path": str(FIXTURES_DIR / "rome_vatican_01.jpg"),
        "mimeType": "image/jpeg",
    },
    {
        "id": "fix-05",
        "name": "rome_vatican_02.jpg",
        "local_path": str(FIXTURES_DIR / "rome_vatican_02.jpg"),
        "mimeType": "image/jpeg",
    },
    {
        "id": "fix-06",
        "name": "florence_duomo_01.jpg",
        "local_path": str(FIXTURES_DIR / "florence_duomo_01.jpg"),
        "mimeType": "image/jpeg",
    },
]

TEST_FOLDER_ID = "e2e-test-folder-123"
TEST_FOLDER_NAME = "Italy Trip 2024"


class MockGoogleDriveClient:
    """Fake Google Drive client that returns fixture images."""

    def __init__(self, access_token: str = "", refresh_token: str | None = None):
        self.access_token = access_token
        self.refresh_token = refresh_token

    async def list_folder_recursive(
        self, folder_id: str, page_size: int = 100
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": f["id"],
                "name": f["name"],
                "mimeType": f["mimeType"],
            }
            for f in FIXTURE_FILES
        ]

    async def download_file(self, file_id: str, dest_path: str) -> None:
        for f in FIXTURE_FILES:
            if f["id"] == file_id:
                shutil.copy2(f["local_path"], dest_path)
                return
        raise FileNotFoundError(f"Fixture not found: {file_id}")

    async def get_folder_metadata(self, folder_id: str) -> dict[str, Any]:
        return {
            "id": TEST_FOLDER_ID,
            "name": TEST_FOLDER_NAME,
            "file_count": len(FIXTURE_FILES),
        }


class MockGoogleDriveOAuth:
    """Fake OAuth that skips real Google consent flow."""

    @staticmethod
    def get_auth_url() -> str:
        return "http://localhost:3000/dashboard?oauth=mocked"

    @staticmethod
    def get_auth_flow():
        """Return a mock flow object for callers that need it."""
        # The real router only calls get_auth_url() and get_auth_flow() via the
        # GoogleDriveOAuth methods on the class. We mock both so they work.
        return _MockFlow()

    @staticmethod
    def exchange_code_for_tokens(code: str) -> dict[str, Any]:
        return {
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_expiry": None,
        }


class _MockFlow:
    """Minimal mock to satisfy get_auth_flow().authorization_url()."""

    @staticmethod
    def authorization_url(access_type: str = "", prompt: str = "") -> tuple[str, str]:
        return ("http://localhost:3000/dashboard?oauth=mocked", "mock-state")


class MockClaudeClient:
    """Fake Claude API that returns canned responses."""

    def __init__(self, api_key: str | None = None, cache_repo=None):
        self.client = None
        self.cache_repo = cache_repo

    async def call(
        self,
        prompt_name: str,
        prompt_version: str,
        variables: dict[str, Any],
        model: str = "claude-opus-4-7",
        vision_content: list | None = None,
    ) -> dict:
        return {
            "text": _get_mock_claude_response(prompt_name, variables),
            "model": model,
            "tokens_in": 100,
            "tokens_out": 50,
            "cache_key": "mock-cache-key",
        }


def _get_mock_claude_response(prompt_name: str, variables: dict) -> str:
    """Return canned Claude responses based on prompt type."""
    if "description" in prompt_name.lower():
        location = variables.get("location", "Italy")
        return f"Exploring {location} never gets old. Each corner has a story to tell - from the ancient stones of Rome to the golden light of Florence. 🔆\n\n#Italy #TravelDiaries"

    if "grouping" in prompt_name.lower():
        return '{"groups": []}'

    if "color" in prompt_name.lower():
        return '{"proposals": []}'

    if "object_removal" in prompt_name.lower():
        return '{"candidates": []}'

    if "crop" in prompt_name.lower():
        return '{"crop": {"x": 0, "y": 0, "width": 1, "height": 1}, "aspect_ratio": "4:5"}'

    if "selection" in prompt_name.lower():
        return '{"winner_index": 0, "reason": "best exposure"}'

    return '{"result": "mock"}'


class MockReplicateClient:
    """Fake Replicate API that returns canned outputs."""

    def __init__(self, cache_repo=None):
        self.api_token = "mock-token"
        self.cache_repo = cache_repo

    async def run(
        self,
        model: str,
        inputs: dict[str, Any],
        webhook_events_filter: list[str] | None = None,
    ) -> dict:
        return {
            "output": "mock-output-url",
            "status": "success",
            "model": model,
            "prediction_id": f"mock-prediction-{hash(model)}",
        }
