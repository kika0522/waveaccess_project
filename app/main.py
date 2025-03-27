import asyncio
import json
from fastapi import FastAPI, HTTPException, UploadFile, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
from app.config import settings
from app.database import get_db
from app.files.github_client import GitHubClient
from app.reports.models import Report
from app.files.minio_client import MinioClient
from app.reports.reports_service import reports_service
from app.logger_config import setup_logging

logger = setup_logging()

MAX_FILE_SIZE = 1024 * 1024 * 1024 * 4  # = 4GB

app = FastAPI()


@app.post('/upload/',
          summary="Загрузка ZIP-файла",
          description="Загрузить ZIP-файл для анализа",
          response_description="ID задачи для отслеживания")
async def upload_file(file: UploadFile, db: AsyncSession = Depends(get_db)):
    """
    Загрузка ZIP-архива с кодом для анализа

    :param file: ZIP-архив с кодом для анализа
    :param db: Сессия БД
    :return: ID задачи для отслеживания статуса
    """
    logger.info(f"РАЗМЕР ФАЙЛА: {file.size}, МАКСИМАЛЬНЫЙ РАЗМЕР ФАЙЛА: {MAX_FILE_SIZE}")
    if file.size > MAX_FILE_SIZE:
        error_msg = "Максимальный размер ZIP-архива для загрузки: 4GB"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)


    if not file.filename.endswith('.zip'):
        error_msg = "Возможна загрузка только ZIP-архивов"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        task_id = str(uuid4())
        logger.info(f"Начало загрузки для задачи {task_id}")

        minio_client = MinioClient(bucket_name=settings.MINIO_BUCKET_NAME)
        await minio_client.create_bucket()
        await minio_client.upload_file(
            file=file.file,
            file_name=str(f"{task_id}.zip"),
            metadata={"original_filename": file.filename}
        )


        await reports_service.create_new_report(task_id, db)
        asyncio.create_task(reports_service.run_report_generation(task_id))

        logger.info(f"Загрузка задачи {task_id} завершена")
        return {"task_id": task_id}

    except Exception as e:
        error_msg = f"Ошибка при загрузке файла: {e}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@app.post('/upload-from-github/',
          summary="Загрузка репозитория из GitHub",
          description="Загрузка репозитория GitHub для анализа кода",
          response_description="Статус загрузки и ID задачи для отслеживания")
async def upload_from_github(repo_url: str, branch: str = "main", db:AsyncSession = Depends(get_db)):
    """
    Загрузка и анализ репозиторий GitHub

    :param repo_url: URL репозитория GitHub
    :param branch: Имя ветки (по умолчанию "main")
    :param db: Сессия БД
    :return: Статус загрузки и ID задачи
    """
    try:
        logger.info(f"Начало загрузки из GitHub: {repo_url} (ветка: {branch})")

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
            metadata={"original_filename": zip_name}
        )

        await reports_service.create_new_report(task_id, db)
        asyncio.create_task(reports_service.run_report_generation(task_id))

        logger.info(f"Загрузка из GitHub завершена, ID задачи: {task_id}")
        return {
            "message": f"Файлы из репозитория '{repo_url}' (ветка '{branch}') успешно загружены в MinIO.",
            "object_name": zip_name,
            "bucket": settings.MINIO_BUCKET_NAME,
            "task_id": task_id,
        }
    except Exception as e:
        error_msg = f"Ошибка при загрузке из GitHub: {e}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@app.get('/reports/{report_id}',
         summary="Получить отчёт",
         description="Получить отчёт анализа кода по ID задачи",
         response_description="Отчёт анализа кода")
async def get_report(
        report_id: str = Path(..., regex=r'^[0-9a-f-]+$', description="UUID отчёта", example="5f8a3b7e-1234-11ec-b909-0242ac130002"),
        db: AsyncSession = Depends(get_db)
):
    """
    Получить отчёт анализа кода по ID задачи.

    :param report_id: UUID отчёта
    :param db: Сессия БД
    :return: Статус и результаты анализа кода (если готовы)
    """
    try:
        logger.info(f"Запрос отчета {report_id}")
        query = select(Report).where(Report.id == report_id)
        result = await db.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            error_msg = f"Отчет {report_id} не найден"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        results_data = json.loads(report.results) if report.results else None

        if report.status == "IN_PROGRESS":
            return {
                "task_id": report.id,
                "status": "IN_PROGRESS",
                "message": "Отчет в процессе генерации"
            }
        logger.info(f"Отчет {report_id} успешно получен")
        return {
            "task_id": report.id,
            "status": report.status,
            "results": results_data,
        }
    except Exception as e:
        error_msg = f"Ошибка при получении отчета: {e}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)