from fastapi import APIRouter, HTTPException

from mosaygent.command_runner import run_command
from mosaygent.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    tags=['Supabase Routes'],
)


@router.get("/supabase/check-installation")
async def check_supabase_installation() -> dict:
    """Check if Docker and Supabase CLI are installed."""
    logger.info("Checking Docker and Supabase CLI installation")

    docker_result = await run_command(['docker', '--version'], timeout=10, raise_on_error=False)

    if not docker_result.success:
        logger.warning("Docker is not installed")
        return {
            "docker_installed": False,
            "message": "Docker is not installed. Please install Docker to use Supabase."
        }

    logger.info("Docker is installed")
    docker_version = docker_result.stdout.strip()
    logger.debug(f"Docker version: {docker_version}")

    supabase_result = await run_command(['supabase', '--version'], timeout=10, raise_on_error=False)

    if not supabase_result.success:
        logger.warning("Supabase CLI is not installed")
        return {
            "docker_installed": True,
            "docker_version": docker_version,
            "supabase_installed": False,
            "message": "Supabase CLI is not installed. Please install the Supabase CLI."
        }

    logger.info("Supabase CLI is installed")
    supabase_version = supabase_result.stdout.strip()
    logger.debug(f"Supabase CLI version: {supabase_version}")

    return {
        "docker_installed": True,
        "docker_version": docker_version,
        "supabase_installed": True,
        "supabase_version": supabase_version
    }
