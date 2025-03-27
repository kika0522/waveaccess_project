import asyncio
import json
from typing import Dict
from sqlalchemy import update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import async_session_maker
from app.ext_services.sonarqube_mock import generate_sonarqube_report
from app.ext_services.second_service_mock import generate_second_service_report
from app.ext_services.third_service_mock import generate_third_service_report
from app.files.minio_client import MinioClient
from app.reports.models import Report

from app.logger_config import app_logger

logger = app_logger.getChild(__name__)

class ReportsService:
    def __init__(self):
        """Инициализация сервиса отчётов с клиентом MinIO"""
        self.minio_client = MinioClient(bucket_name=settings.MINIO_BUCKET_NAME)
        logger.info("Сервис отчетов инициализирован")

    async def _generate_all_reports(self, task_id: str) -> Dict:
        """
        Параллельный запуск генерации всех отчётов

        :param task_id: ID задачи для генерации отчётов
        :return: Dict: Объединённые отчёты всех сервисов
        """

        logger.info(f"Начало генерации отчетов для задачи {task_id}")
        sonarqube, second, third = await asyncio.gather(
            generate_sonarqube_report(task_id),
            generate_second_service_report(task_id),
            generate_third_service_report(task_id),
        )

        logger.info(f"Генерация отчетов завершена для задачи {task_id}")
        return {
            "results": {
                "sonarqube": sonarqube,
                "second_service": second,
                "third_service": third,
            }
        }

    async def generate_report(self, task_id: str, db: AsyncSession):
        """
        Генерация и сохранение в БД отчёта по ID задачи

        :param task_id: ID задачи для генерации отчёта
        :param db: Сессия БД
        """
        try:
            logger.info(f"Устанавливаем статус IN_PROGRESS для задачи {task_id}")
            await db.execute(
                update(Report)
                .where(Report.id == task_id)
                .values(status="IN_PROGRESS")
            )
            await db.commit()  # 💡 Этот коммит может не выполняться из-за ошибки
            logger.info(f"Статус задачи {task_id} обновлён на IN_PROGRESS")


            report_data = await self._generate_all_reports(task_id)
            report_json = json.dumps(report_data)

            await db.execute(
                update(Report)
                .where(Report.id == task_id)
                .values(status="SUCCESS", results=report_json)
            )
            await db.commit()
            logger.info(f"Отчет для задачи {task_id} успешно сгенерирован")

        except Exception as e:
            logger.error(f"Ошибка генерации отчета {task_id}: {e}")
            await db.rollback()
            await db.execute(
                update(Report)
                .where(Report.id == task_id)
                .values(status="ERROR", results=None)
            )
            await db.commit()
            raise

    async def run_report_generation(self, task_id: str):
        """
        Запуск генерации отчётов в фоновом режиме

        :param task_id: ID задачи для генерации отчёта
        :return:
        """
        logger.info(f"Запуск фоновой генерации отчета для задачи {task_id}")
        async with async_session_maker() as new_db:
            await self.generate_report(task_id, new_db)

    async def create_new_report(self, task_id: str, db: AsyncSession):
        """
        Создание новой записи в БД
        :param task_id: ID новой задачи
        :param db: Сессия БД
        """
        logger.info(f"Создание новой записи отчета для задачи {task_id}")
        async with db.begin():
            await db.execute(
                insert(Report)
                .values(id=task_id, status="PENDING")
            )
            await db.commit()
            logger.info(f"Новая запись отчета создана для задачи {task_id}")


reports_service = ReportsService()