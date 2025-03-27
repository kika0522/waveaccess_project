from fastapi import HTTPException
from urllib.parse import urlparse
from io import BytesIO
import httpx


from app.logger_config import app_logger

logger = app_logger.getChild(__name__)

class GitHubClient:
    async def download_repo_zip(self, repo_url: str, branch: str = "main") -> BytesIO:
        """
        Скачивает репозиторий GitHub в формате ZIP

        :param repo_url: URL репозитория GitHub
        :param branch: Имя ветки (по умолчанию "main")
        :return: BytesIO: ZIP-архив
        """
        try:
            logger.info(f"Скачивание репозитория {repo_url} (ветка: {branch})")
            parsed_url = urlparse(repo_url)
            if parsed_url.netloc != "github.com":
                error_msg = "Поддерживаются только репозитории с GitHub."
                logger.error(error_msg)
                raise ValueError(error_msg)

            path_parts = parsed_url.path.strip("/").split("/")
            if len(path_parts) < 2:
                error_msg = "Некорректный URL репозитория."
                logger.error(error_msg)
                raise ValueError(error_msg)

            user, repo = path_parts[0], path_parts[1]
            repo = repo.replace(".git", "")
            zip_url = f"https://github.com/{user}/{repo}/archive/refs/heads/{branch}.zip"

            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(zip_url)
                response.raise_for_status()
                logger.info(f"Репозиторий {repo_url} скачан")
                return BytesIO(response.content)
        except Exception as e:
            error_msg = f"Ошибка при скачивании репозитория: {e}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)