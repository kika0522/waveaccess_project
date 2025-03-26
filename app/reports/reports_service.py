import asyncio
import logging
import json
from uuid import UUID
from typing import Dict

from sqlalchemy import update, values, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_maker
from app.ext_services.sonarqube_mock import generate_sonarqube_report
from app.ext_services.second_service_mock import generate_second_service_report
from app.ext_services.third_service_mock import generate_third_service_report
from app.files.minio_client import MinioClient
from app.reports.models import Report

logger = logging.getLogger(__name__)


class ReportsService:
    def __init__(self):
        self.minio_client = MinioClient(bucket_name=settings.MINIO_BUCKET_NAME)

    async def _generate_all_reports(self, task_id: str) -> Dict:
        # Запускаем все генераторы параллельно
        sonarqube, second, third = await asyncio.gather(
            generate_sonarqube_report(task_id),
            generate_second_service_report(task_id),
            generate_third_service_report(task_id),
        )

        return {
            "results": {
                "sonarqube": sonarqube,
                "second_service": second,
                "third_service": third,
            }
        }

    async def generate_report(self, task_id: str, db: AsyncSession):
        try:
            logger.info(f"Setting status to IN_PROGRESS for task {task_id}")
            await db.execute(
                update(Report)
                .where(Report.id == task_id)
                .values(status="IN_PROGRESS")
            )
            await db.commit()  # 💡 Этот коммит может не выполняться из-за ошибки
            logger.info(f"Status set to IN_PROGRESS for task {task_id}")

            report_data = await self._generate_all_reports(task_id)
            report_json = json.dumps(report_data)

            await db.execute(
                update(Report)
                .where(Report.id == task_id)
                .values(status="SUCCESS", results=report_json)
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Error generating report {task_id}: {e}")
            await db.rollback()
            await db.execute(
                update(Report)
                .where(Report.id == task_id)
                .values(status="ERROR", results=None)
            )
            await db.commit()
            raise

    async def run_report_generation(self, task_id: str):
        async with async_session_maker() as new_db:
            await self.generate_report(task_id, new_db)

    async def create_new_report(self, task_id: str, db: AsyncSession):
        async with db.begin():
            await db.execute(
                insert(Report)
                .values(id=task_id, status="PENDING")
            )
            await db.commit()
# Синглтон экземпляр сервиса
reports_service = ReportsService()