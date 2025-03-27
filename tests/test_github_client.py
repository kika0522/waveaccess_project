import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from app.files.github_client import GitHubClient


@pytest.mark.asyncio
async def test_download_repo_zip_success():
    mock_response = AsyncMock()
    mock_response.content = b"zip content"
    mock_response.raise_for_status = AsyncMock()

    with patch('httpx.AsyncClient.get', return_value=mock_response):
        client = GitHubClient()
        result = await client.download_repo_zip("https://github.com/user/repo")

        assert result.getvalue() == b"zip content"


@pytest.mark.asyncio
async def test_download_repo_zip_http_error():
    mock_response = AsyncMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP Error")

    with patch('httpx.AsyncClient.get', return_value=mock_response):
        client = GitHubClient()
        with pytest.raises(HTTPException):
            await client.download_repo_zip("https://github.com/user/repo")