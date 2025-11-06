from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from mosaygent.logger import get_logger
from mosaygent.services.environment import EnvironmentService
from mosaygent.services.flutter import FlutterService

logger = get_logger(__name__)

FLUTTER_PORT = 36413

router = APIRouter(
    tags=['Environment Routes'],
)


def get_environment_service(request: Request) -> EnvironmentService:
    """Get the Environment service from app state."""
    if not hasattr(request.app.state, 'environment_service'):
        logger.info("Initializing environment service")
        request.app.state.environment_service = EnvironmentService()
    return request.app.state.environment_service


class SetDirectoryRequest(BaseModel):
    path: str


@router.post("/environment/set-directory", status_code=status.HTTP_200_OK)
async def set_directory(request: Request, body: SetDirectoryRequest) -> dict:
    """Set the project directory and initialize Flutter service if available."""
    service = get_environment_service(request)

    try:
        service.set_project_dir(body.path)

        flutter_dir = Path(body.path) / "flutterapp"
        if flutter_dir.exists():
            logger.info(f"Initializing Flutter service for directory: {flutter_dir}")

            if hasattr(request.app.state, 'flutter_service'):
                old_service = request.app.state.flutter_service
                if old_service.process and old_service.process.poll() is None:
                    logger.info("Stopping existing Flutter service")
                    old_service.stop()

            request.app.state.flutter_service = FlutterService(
                app_dir=flutter_dir,
                web_port=FLUTTER_PORT
            )
            logger.info("Flutter service initialized successfully")
        else:
            logger.info(f"Flutter directory not found at {flutter_dir}")

        return {"success": True, "path": body.path}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to set directory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set directory: {str(e)}")


@router.get("/environment/directory", status_code=status.HTTP_200_OK)
async def get_directory(request: Request) -> dict:
    """Get the current project directory."""
    service = get_environment_service(request)
    path = service.get_project_dir()
    return {"path": path}


@router.get("/environment/status", status_code=status.HTTP_200_OK)
async def get_status(request: Request) -> dict:
    """Get comprehensive status of both codebases."""
    service = get_environment_service(request)

    api_status = service.check_codebase_status("api")
    flutter_status = service.check_codebase_status("flutter")

    return {
        "project_dir": service.get_project_dir(),
        "api": api_status,
        "flutter": flutter_status,
    }


@router.post("/environment/clone-api", status_code=status.HTTP_200_OK)
async def clone_api(request: Request) -> dict:
    """Clone the API repository."""
    service = get_environment_service(request)

    try:
        result = await service.clone_repository("api")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to clone API repository: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clone API repository: {str(e)}")


@router.post("/environment/clone-flutter", status_code=status.HTTP_200_OK)
async def clone_flutter(request: Request) -> dict:
    """Clone the Flutter repository."""
    service = get_environment_service(request)

    try:
        result = await service.clone_repository("flutter")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to clone Flutter repository: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clone Flutter repository: {str(e)}")


@router.get("/environment/analyze-python", status_code=status.HTTP_200_OK)
async def analyze_python_directory(request: Request, path: str) -> dict:
    """Analyze if a directory contains a Python codebase."""
    logger.info(f"Received request to analyze Python codebase at: {path}")
    service = get_environment_service(request)

    try:
        result = service.analyze_python_codebase(path)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to analyze Python codebase: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze directory: {str(e)}")


@router.get("/environment/analyze-flutter", status_code=status.HTTP_200_OK)
async def analyze_flutter_directory(request: Request, path: str) -> dict:
    """Analyze if a directory contains a Flutter codebase."""
    logger.info(f"Received request to analyze Flutter codebase at: {path}")
    service = get_environment_service(request)

    try:
        result = service.analyze_flutter_codebase(path)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to analyze Flutter codebase: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze directory: {str(e)}")
