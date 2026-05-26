"""Google Drive API integration."""

from __future__ import annotations

import asyncio
from typing import Any

import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.config import settings


class GoogleDriveOAuth:
    """Handle Google Drive OAuth flow."""

    @staticmethod
    def get_auth_flow() -> Flow:
        """Create OAuth flow for Google Drive."""
        return Flow.from_client_secrets_file(
            "secrets/google_oauth.json",  # Must be created by user
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
            redirect_uri=settings.google_oauth_redirect_uri,
        )

    @staticmethod
    def get_auth_url() -> str:
        """Get the OAuth consent URL."""
        flow = GoogleDriveOAuth.get_auth_flow()
        auth_url, _state = flow.authorization_url(access_type="offline", prompt="consent")
        return auth_url

    @staticmethod
    def exchange_code_for_tokens(code: str) -> dict[str, Any]:
        """Exchange auth code for tokens."""
        flow = GoogleDriveOAuth.get_auth_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials
        return {
            "refresh_token": creds.refresh_token,
            "access_token": creds.token,
            "token_expiry": creds.expiry.isoformat() if creds.expiry else None,
        }


class GoogleDriveClient:
    """Google Drive API client."""

    def __init__(self, access_token: str, refresh_token: str | None = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._service = None
        self._request_count = 0
        self._request_semaphore = asyncio.Semaphore(1)  # Rate limit: 1 req at a time

    def _get_service(self) -> googleapiclient.discovery.Resource:
        """Get or create Drive service."""
        if not self._service:
            creds = Credentials(token=self.access_token)
            self._service = googleapiclient.discovery.build("drive", "v3", credentials=creds)
        return self._service

    async def list_folder_recursive(
        self, folder_id: str, page_size: int = 100
    ) -> list[dict[str, Any]]:
        """List all files in a folder recursively."""
        items = []
        service = self._get_service()

        async def _list_page(folder_id: str, page_token: str | None = None) -> None:
            async with self._request_semaphore:
                try:
                    results = (
                        service.files()
                        .list(
                            q=f"'{folder_id}' in parents and trashed=false",
                            spaces="drive",
                            pageSize=page_size,
                            pageToken=page_token,
                            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, fileSize)",
                        )
                        .execute()
                    )
                except googleapiclient.errors.HttpError as e:
                    if e.resp.status == 401:
                        # Token expired, refresh needed
                        pass
                    raise

                for item in results.get("files", []):
                    items.append(item)
                    if item["mimeType"] == "application/vnd.google-apps.folder":
                        await _list_page(item["id"], None)

                next_token = results.get("nextPageToken")
                if next_token:
                    await _list_page(folder_id, next_token)

        await _list_page(folder_id)
        return items

    async def download_file(self, file_id: str, dest_path: str) -> None:
        """Download a file from Drive."""
        async with self._request_semaphore:
            service = self._get_service()
            try:
                request = service.files().get_media(fileId=file_id)
                with open(dest_path, "wb") as f:
                    downloader = googleapiclient.http.MediaIoBaseDownload(f, request)
                    done = False
                    while not done:
                        _status, done = downloader.next_chunk()
            except googleapiclient.errors.HttpError as e:
                if e.resp.status == 401:
                    # Token expired
                    pass
                raise

    async def get_folder_metadata(self, folder_id: str) -> dict[str, Any]:
        """Get folder metadata (name, file count, etc.)."""
        async with self._request_semaphore:
            service = self._get_service()
            folder = service.files().get(fileId=folder_id, fields="name, id").execute()

            # Count files in folder
            results = (
                service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    spaces="drive",
                    pageSize=1,
                    fields="nextPageToken",
                )
                .execute()
            )

            return {
                "id": folder["id"],
                "name": folder["name"],
                "file_count": results.get("nextPageToken") is not None,  # Approximation for MVP
            }
