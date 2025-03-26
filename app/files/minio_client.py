import io
from typing import BinaryIO

from fastapi import HTTPException, status
from minio import Minio

from app.config import settings


class MinioClient:
    def __init__(self, bucket_name: str):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
        )
        self.bucket_name = bucket_name
        # TODO - Добавить logger.info(init self.bucket_name)

    async def create_bucket(self):
        bucket_name = self.bucket_name
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            print(f"Бакет {self.bucket_name} создан.")
        else:
            print(f"Бакет {self.bucket_name} уже существует.")

    async def upload_file(self, file: io.IOBase | BinaryIO, file_name: str, metadata: dict = None):
        """Загружает файл в MinIO"""
        file.seek(0)
        self.client.put_object(
            self.bucket_name,
            file_name,
            file,
            length=-1,
            part_size=10*1024*1024,
            metadata=metadata
        )

    async def file_exists(self, file_name: str) -> bool:
        try:
            await self.client.stat_object(self.bucket_name, file_name)
            return True
        except Exception:
            return False

    def _exception(self, detail: str):
        #TODO - Добавить logger.error(detail)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )