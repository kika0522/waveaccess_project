from fastapi import HTTPException
from urllib.parse import urlparse
from io import BytesIO

import httpx


class GitHubClient:
    async def download_repo_zip(self, repo_url: str, branch: str = "main") -> BytesIO:
        try:
            parsed_url = urlparse(repo_url)
            if parsed_url.netloc != "github.com":
                raise ValueError("Поддерживаются только репозитории с GitHub.")

            path_parts = parsed_url.path.strip("/").split("/")
            if len(path_parts) < 2:
                raise ValueError("Некорректная ссылка на репозиторий.")

            user, repo = path_parts[0], path_parts[1]
            repo = repo.replace(".git", "")
            zip_url = f"https://github.com/{user}/{repo}/archive/refs/heads/{branch}.zip"

            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(zip_url)
                response.raise_for_status()
                return BytesIO(response.content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при скачивании репозитория: {e}")