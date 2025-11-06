import re

from fastapi import APIRouter, HTTPException, Request, status

from mosaygent.command_runner import run_command
from mosaygent.logger import get_logger
from mosaygent.services.flutter import FlutterService

logger = get_logger(__name__)

router = APIRouter(
    tags=['Flutter Routes'],
)


def get_flutter_service(request: Request) -> FlutterService:
    """Get the Flutter service from app state."""
    if not hasattr(request.app.state, 'flutter_service'):
        logger.error("Flutter service not initialized - project directory may not be set")
        raise HTTPException(
            status_code=400,
            detail="Flutter service not initialized. Please set the project directory first using /environment/set-directory"
        )
    return request.app.state.flutter_service


@router.get("/flutter-version")
async def flutter_version() -> dict:
    """Get locally installed Flutter version information."""
    logger.info("Fetching Flutter version")

    result = await run_command(['flutter', '--version'], timeout=10)
    logger.debug(f"Flutter command output: {result.stdout[:100]}")

    path_result = await run_command(['which', 'flutter'], timeout=5)
    flutter_path = path_result.stdout.strip()
    logger.debug(f"Flutter installation path: {flutter_path}")

    version_match = re.search(r'Flutter\s+(\d+\.\d+\.\d+)', result.stdout)
    if version_match:
        version = version_match.group(1)
        logger.info(f"Successfully parsed Flutter version: {version}")
        return {
            "version": version,
            "path": flutter_path,
            "full_output": result.stdout.strip()
        }

    logger.warning("Primary pattern failed, trying fallback version pattern")
    version_match = re.search(r'(\d+\.\d+\.\d+)', result.stdout)
    if version_match:
        version = version_match.group(1)
        logger.info(f"Parsed Flutter version with fallback pattern: {version}")
        return {
            "version": version,
            "path": flutter_path,
            "full_output": result.stdout.strip()
        }

    logger.error(f"Failed to parse Flutter version from output: {result.stdout}")
    raise HTTPException(
        status_code=500,
        detail="Could not parse Flutter version from output"
    )


@router.post("/flutter/start", status_code=status.HTTP_200_OK)
async def start_flutter_server(request: Request) -> dict:
    """Start the Flutter development server."""
    logger.info("Starting Flutter development server")
    service = get_flutter_service(request)

    try:
        result = service.start()
        await service.wait_for_ready()
        return result
    except FileNotFoundError as e:
        logger.error(f"App directory not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to start Flutter server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start Flutter: {e}")


@router.post("/flutter/stop", status_code=status.HTTP_200_OK)
async def stop_flutter_server(request: Request) -> dict:
    """Stop the Flutter development server."""
    logger.info("Stopping Flutter development server")
    service = get_flutter_service(request)

    try:
        return service.stop()
    except Exception as e:
        logger.exception(f"Failed to stop Flutter server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop Flutter: {e}")


@router.get("/flutter/status", status_code=status.HTTP_200_OK)
async def get_flutter_status(request: Request) -> dict:
    """Get the status of the Flutter development server."""
    logger.info("Getting Flutter development server status")
    service = get_flutter_service(request)
    return service.get_status()


@router.post("/flutter/reload", status_code=status.HTTP_200_OK)
async def trigger_hot_reload(request: Request) -> dict:
    """Manually trigger a Flutter hot reload."""
    logger.info("Triggering manual hot reload")
    service = get_flutter_service(request)
    service.trigger_hot_reload()
    return {"message": "Hot reload triggered"}


@router.post("/flutter/restart", status_code=status.HTTP_200_OK)
async def trigger_hot_restart(request: Request) -> dict:
    """Manually trigger a Flutter hot restart."""
    logger.info("Triggering manual hot restart")
    service = get_flutter_service(request)
    service.trigger_hot_restart()
    return {"message": "Hot restart triggered"}


@router.get("/flutter/errors")
async def get_flutter_errors(request: Request) -> dict:
    """Get Flutter error messages from stderr."""
    logger.info("Fetching Flutter errors")
    service = get_flutter_service(request)
    errors = service.get_errors()
    return {
        "errors": errors,
        "count": len(errors),
        "has_errors": len(errors) > 0
    }
