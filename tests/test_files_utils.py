import zipfile

import pytest
from fastapi import UploadFile
from io import BytesIO
from app.files.files_utils import is_valid_zip


@pytest.mark.asyncio
async def test_is_valid_zip_with_valid_file():
    # Создаем валидный ZIP в памяти
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr('test.zip', 'test content')
    zip_buffer.seek(0)

    upload_file = UploadFile(filename='test.zip', file=zip_buffer)
    assert await is_valid_zip(upload_file) is True


@pytest.mark.asyncio
async def test_is_valid_zip_with_invalid_file():
    # Создаем невалидный файл (не ZIP)
    file_buffer = BytesIO(b'not a zip file')
    upload_file = UploadFile(filename='test.txt', file=file_buffer)
    assert await is_valid_zip(upload_file) is False


@pytest.mark.asyncio
async def test_is_valid_zip_with_empty_zip():
    # Создаем пустой ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w'):
        pass
    zip_buffer.seek(0)

    upload_file = UploadFile(filename='empty.zip', file=zip_buffer)
    assert await is_valid_zip(upload_file) is False