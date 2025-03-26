import asyncio
import logging
import json
from fastapi import FastAPI, HTTPException, UploadFile, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4, UUID
from app.config import settings
from app.database import get_db, async_session_maker
from app.files.github_client import GitHubClient
from app.reports.models import Report
from app.files.minio_client import MinioClient
from app.reports.reports_service import reports_service

logger = logging.getLogger(__name__)

app = FastAPI()


@app.post('/upload/')
async def upload_file(file: UploadFile, db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Возможна загрузка только ZIP-архивов")

    try:
        task_id = str(uuid4())

        minio_client = MinioClient(bucket_name=settings.MINIO_BUCKET_NAME)
        await minio_client.create_bucket()
        await minio_client.upload_file(
            file=file.file,
            file_name=str(f"{task_id}.zip"),
            metadata={
                "original_filename": file.filename
            }
        )

        await reports_service.create_new_report(task_id, db)

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
        db: AsyncSession = Depends(get_db)
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

        results_data = json.loads(report.results) if report.results else None

        if report.status == "IN_PROGRESS":
            return {
                "task_id": report.id,
                "status": "IN_PROGRESS",
                "message": "Отчет в процессе генерации"
            }
        return {
            "task_id": report.status,
            "status": report.status,
            "results": results_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении отчёта11: {e}")