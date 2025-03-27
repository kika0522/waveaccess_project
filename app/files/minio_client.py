import io
from typing import BinaryIO
from fastapi import HTTPException, status
from minio import Minio
from app.config import settings

from app.logger_config import app_logger

logger = app_logger.getChild(__name__)

class MinioClient:
    def __init__(self, bucket_name: str):
        """Инициализация MinIO клиента"""
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
        )
        self.bucket_name = bucket_name
        logger.info(f"Инициализирован клиент MinIO для бакета: {self.bucket_name}")

    async def create_bucket(self):
        """Создать бакет, если не существует"""
        bucket_name = self.bucket_name
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            logger.info(f"Бакет {self.bucket_name} создан")
        else:
            logger.info(f"Бакет {self.bucket_name} уже существует.")

    async def upload_file(self, file: io.IOBase | BinaryIO, file_name: str, metadata: dict = None):
        """
        Загружает файл в хранилище MinIO
        """
        file.seek(0)
        logger.info(f"Загрузка файла {file_name} в бакет {self.bucket_name}")
        self.client.put_object(
            self.bucket_name,
            file_name,
            file,
            length=-1,
            part_size=10*1024*1024,
            metadata=metadata
        )
        logger.info(f"Файл {file_name} успешно загружен")

    async def file_exists(self, file_name: str) -> bool:
        """
        Проверяем существование файла в бакете

        :param file_name: Имя файла для проверки

        :return: bool: True, если файл существует, иначе False
        """
        try:
            await self.client.stat_object(self.bucket_name, file_name)
            return True
        except Exception as e:
            logger.warning(f"Файл {file_name} не найден: {e}")
            return False

    def _exception(self, detail: str):
        logger.error(detail)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )