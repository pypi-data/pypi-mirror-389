from pathlib import Path

from fastapi import HTTPException

from mosaygent.command_runner import run_command, run_command_streaming
from mosaygent.logger import get_logger
from mosaygent.services.environment import EnvironmentService

logger = get_logger(__name__)


class FirebaseDeployService:
    """Manages Firebase deployment operations."""

    def __init__(self):
        self.env_service = EnvironmentService()

    async def _run_npm_install(self, functions_dir: Path) -> None:
        """Run npm install in the functions directory if package.json exists."""
        if functions_dir.exists() and (functions_dir / "package.json").exists():
            logger.info(f"Running npm install in {functions_dir}")
            try:
                npm_result = await run_command(
                    ["npm", "install"],
                    timeout=300,
                    cwd=str(functions_dir),
                    raise_on_error=False
                )
                if npm_result.success:
                    logger.info("npm install completed successfully")
                else:
                    logger.warning(f"npm install failed: {npm_result.stderr}")
            except Exception as e:
                logger.warning(f"npm install failed: {e}")

    async def deploy_firebase(self, project_id: str, repo_path: str | None = None) -> dict:
        """Deploy Firebase project (assumes firebase.json exists in repo_path/firebase/)."""
        logger.info(f"Starting Firebase deployment for project: {project_id}")

        if repo_path:
            repo_path_obj = Path(repo_path)
            logger.info(f"Using provided repo path: {repo_path_obj}")
        elif self.env_service.project_dir:
            repo_path_obj = self.env_service.project_dir
            logger.info(f"Using configured project directory: {repo_path_obj}")
        else:
            logger.error("No repository path provided and project directory not configured")
            raise HTTPException(
                status_code=500,
                detail="No repo_path provided and project directory not configured"
            )

        firebase_dir = repo_path_obj / "firebase"

        if not firebase_dir.exists():
            logger.error(f"Firebase directory not found: {firebase_dir}")
            raise HTTPException(
                status_code=404,
                detail=f"Firebase directory not found at {firebase_dir}."
            )

        firebase_json = firebase_dir / "firebase.json"
        if not firebase_json.exists():
            logger.error(f"firebase.json not found: {firebase_json}")
            raise HTTPException(
                status_code=404,
                detail=f"firebase.json not found at {firebase_json}"
            )

        logger.info(f"Found firebase.json at {firebase_json}")

        functions_dir = firebase_dir / "functions"
        await self._run_npm_install(functions_dir)

        try:
            logger.info(f"Running firebase deploy --project {project_id}")
            result = run_command_streaming(
                ["firebase", "deploy", "--project", project_id],
                timeout=300,
                cwd=str(firebase_dir)
            )

            logger.info("Firebase deployment completed successfully")
            return {
                "success": True,
                "project_id": project_id,
                "firebase_dir": str(firebase_dir),
                "output": result.stdout.strip(),
            }
        except Exception as e:
            logger.exception(f"Firebase deployment failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Deployment failed: {str(e)}"
            )

    async def deploy_project(
        self,
        project_id: str,
        working_directory: str | None = None,
        targets: str | None = None,
        force: bool = False
    ) -> dict:
        """Deploy Firebase project with flexible options for targets and working directory."""
        logger.info(f"Starting Firebase deployment for project: {project_id}")

        if working_directory:
            repo_path = Path(working_directory)
            logger.info(f"Using provided working directory: {repo_path}")
        elif self.env_service.project_dir:
            repo_path = self.env_service.project_dir
            logger.info(f"Using configured project directory: {repo_path}")
        else:
            logger.error("No working directory provided and project directory not configured")
            raise HTTPException(
                status_code=400,
                detail="No working_directory provided and project directory not configured"
            )

        firebase_dir = repo_path / "firebase"

        if not firebase_dir.exists():
            logger.error(f"Firebase directory not found: {firebase_dir}")
            raise HTTPException(
                status_code=404,
                detail=f"Firebase directory not found at {firebase_dir}"
            )

        firebase_json = firebase_dir / "firebase.json"
        if not firebase_json.exists():
            logger.error(f"firebase.json not found: {firebase_json}")
            raise HTTPException(
                status_code=404,
                detail=f"firebase.json not found at {firebase_json}"
            )

        logger.info(f"Found firebase.json at {firebase_json}")

        functions_dir = firebase_dir / "functions"
        await self._run_npm_install(functions_dir)

        command = ["firebase", "deploy", "--project", project_id]

        if targets:
            command.extend(["--only", targets])
            logger.info(f"Deploying targets: {targets}")
        else:
            logger.info("Deploying all targets")

        if force:
            command.append("--force")
            logger.info("Force deployment enabled")

        try:
            logger.info(f"Running command: {' '.join(command)} from {firebase_dir}")
            result = run_command_streaming(
                command,
                timeout=300,
                cwd=str(firebase_dir)
            )

            logger.info("Firebase deployment completed successfully")
            return {
                "project_id": project_id,
                "firebase_directory": str(firebase_dir),
                "targets": targets or "all",
                "output": result.stdout.strip(),
            }
        except Exception as e:
            logger.exception(f"Firebase deployment failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Deployment failed: {str(e)}"
            )
