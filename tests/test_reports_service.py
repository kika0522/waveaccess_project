import pytest
from unittest.mock import AsyncMock
from app.reports.reports_service import ReportsService


@pytest.mark.asyncio
async def test_generate_report_success():
    mock_db = AsyncMock()
    mock_db.execute.return_value = None
    mock_db.commit.return_value = None

    service = ReportsService()
    service._generate_all_reports = AsyncMock(return_value={"results": {}})

    await service.generate_report("test-id", mock_db)

    # Проверяем, что статус обновлялся дважды (IN_PROGRESS и SUCCESS)
    assert mock_db.execute.call_count == 2
    assert mock_db.commit.call_count == 2


@pytest.mark.asyncio
async def test_generate_report_error():
    mock_db = AsyncMock()
    mock_db.execute.return_value = None
    mock_db.commit.return_value = None

    service = ReportsService()
    service._generate_all_reports = AsyncMock(side_effect=Exception("Test error"))

    with pytest.raises(Exception):
        await service.generate_report("test-id", mock_db)

    # Проверяем, что был выполнен rollback
    mock_db.rollback.assert_called_once()