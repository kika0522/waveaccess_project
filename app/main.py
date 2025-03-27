import asyncio
import logging
import json
from fastapi import FastAPI, HTTPException, UploadFile, Depends, Path
from fastapi_keycloak import FastAPIKeycloak
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
from app.config import settings
from app.database import get_db
from app.files.github_client import GitHubClient
from app.reports.models import Report
from app.files.minio_client import MinioClient
from app.reports.reports_service import reports_service

logger = logging.getLogger(__name__)

app = FastAPI()

keycloak = FastAPIKeycloak(
    server_url="http://keycloak:8080/",
    client_id="myclient",
    client_secret="sIkCWeFx6aK8va01f891jC77WxJtXLZR",
    admin_client_id="admin-cli",
    admin_client_secret="C3LwdeYaQdyzzSVbjmwsHdKUMBP58Ukn",
    realm="myrealm",
    callback_uri="http://fastapi:8000/callback",
)


@app.post('/upload/')
async def upload_file(file: UploadFile, db: AsyncSession = Depends(get_db), user=Depends(keycloak.get_current_user)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Возможна загрузка только ZIP-архивов")

    try:
        task_id = str(uuid4())
        user_id = user["sub"]

        minio_client = MinioClient(bucket_name=settings.MINIO_BUCKET_NAME)
        await minio_client.create_bucket()
        await minio_client.upload_file(
            file=file.file,
            file_name=str(f"{task_id}.zip"),
            metadata={
                "original_filename": file.filename
            }
        )

        await reports_service.create_new_report(task_id, db, user_id)

        asyncio.create_task(reports_service.run_report_generation(task_id))

        return {"task_id": task_id}

    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке файла: {e}")


@app.post('/upload-from-github/')
async def upload_from_github(repo_url: str, branch: str = "main", db:AsyncSession = Depends(get_db)):
    try:
        minio_client = MinioClient(bucket_name=settings.MINIO_BUCKET_NAME)
        github_client = GitHubClient()

        zip_file = await github_client.download_repo_zip(repo_url, branch)

        repo_path = repo_url.strip("/").split("github.com/")[-1]
        user, repo = repo_path.split("/")[:2]
        repo = repo.replace(".git", "")
        zip_name = f"{user}-{repo}-{branch}.zip"

        task_id = str(uuid4())

        await minio_client.create_bucket()
        await minio_client.upload_file(
            file=zip_file,
            file_name=str(f"{task_id}.zip"),
            metadata={
                "original_filename": zip_name
            }
        )

        await reports_service.create_new_report(task_id, db)

        asyncio.create_task(reports_service.run_report_generation(task_id))

        return {
            "message": f"Файлы из репозитория '{repo_url}' (ветка '{branch}') успешно загружены в MinIO.",
            "object_name": zip_name,
            "bucket": settings.MINIO_BUCKET_NAME,
            "task_id": task_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке файлов из GitHub: {e}")


@app.get('/reports/{report_id}')
async def get_report(
        report_id: str = Path(..., regex=r'^[0-9a-f-]+$', description="UUID отчёта"),
        db: AsyncSession = Depends(get_db),
        user: dict = Depends(keycloak.get_current_user)
):
    """
    Возвращает отчёт по его UUID.
    """
    try:
        query = select(Report).where(Report.id == report_id)
        result = await db.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="Отчёт не найден")

        user_id = user["sub"]
        # is_admin = keycloak.has_role(user, settings.KEYCLOAK_ADMIN_ROLE)

        if report.user_id != user_id: # and not is_admin:
            raise HTTPException(status_code=403, detail="У вас нет доступа к этому отчёту")

        if report.status == "IN_PROGRESS":
            return {
                "task_id": report.id,
                "status": "IN_PROGRESS",
                "message": "Отчёт в процессе генерации"
            }
        return {
            "task_id": report.id,
            "status": report.status,
            "results": json.loads(report.results) if report.results else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении отчёта11: {e}")