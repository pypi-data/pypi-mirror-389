from pathlib import Path

from fastapi import status
from mosayic import app

from mosaygent.logger import get_logger
from mosaygent.routes import router
from mosaygent.services.environment import EnvironmentService
from mosaygent.services.flutter import FlutterService

logger = get_logger(__name__)

__all__ = ['app']

# Configuration
FLUTTER_PORT = 36413


# Initialize environment service
logger.info("Initializing environment service")
app.state.environment_service = EnvironmentService()

# Initialize Flutter service if Flutter directory is available
flutter_dir = None
if app.state.environment_service.project_dir:
    flutter_dir = app.state.environment_service.project_dir / "flutterapp"
    if flutter_dir.exists():
        logger.info(f"Initializing Flutter service: {flutter_dir}")
        app.state.flutter_service = FlutterService(
            app_dir=flutter_dir,
            web_port=FLUTTER_PORT
        )
    else:
        logger.info(f"Flutter directory not found at {flutter_dir}, service not initialized")
else:
    logger.info("Project directory not set, Flutter service not initialized")


# Add health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK, include_in_schema=False)
async def health() -> dict:
    """Health check endpoint."""
    return {"healthy": True}


# Add dev routes to the mosayic app
app.include_router(router)
logger.info("Mosaygent development routes registered")


@app.on_event("shutdown")
async def shutdown_flutter_service():
    """Clean up Flutter service on shutdown."""
    if hasattr(app.state, 'flutter_service'):
        flutter_service = app.state.flutter_service
        if flutter_service.process and flutter_service.process.poll() is None:
            logger.info("Stopping Flutter service")
            flutter_service.stop()
