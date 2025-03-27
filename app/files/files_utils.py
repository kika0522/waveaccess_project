import zipfile
from fastapi import FastAPI, UploadFile, HTTPException
from io import BytesIO


async def is_valid_zip(file: UploadFile) -> bool:
    # Проверка расширения
    if not file.filename.lower().endswith('.zip'):
        return False

    # Проверка сигнатуры
    header = await file.read(4)
    await file.seek(0)
    if header != b'PK\x03\x04':
        return False

    # Проверка структуры
    try:
        content = await file.read()
        with zipfile.ZipFile(BytesIO(content)) as z:
            if not z.namelist():
                return False
        await file.seek(0)
        return True
    except zipfile.BadZipFile:
        return False