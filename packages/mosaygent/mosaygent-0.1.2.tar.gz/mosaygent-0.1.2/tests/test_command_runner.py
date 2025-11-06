import pytest
from fastapi import HTTPException

from mosaygent.command_runner import run_command
from mosaygent.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_run_command_success():
    """Test successful command execution."""
    result = await run_command(["echo", "hello"])

    assert result.success is True
    assert "hello" in result.stdout
    assert result.return_code == 0


@pytest.mark.asyncio
async def test_run_command_not_found():
    """Test that nonexistent command raises 404."""
    with pytest.raises(HTTPException) as exc_info:
        await run_command(["this_command_definitely_does_not_exist_12345"])

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_run_command_timeout():
    """Test that timeout raises 408."""
    with pytest.raises(HTTPException) as exc_info:
        await run_command(["sleep", "10"], timeout=1)

    assert exc_info.value.status_code == 408
