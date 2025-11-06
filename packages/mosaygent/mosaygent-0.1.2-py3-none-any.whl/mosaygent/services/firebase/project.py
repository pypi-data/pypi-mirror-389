import re

from fastapi import HTTPException

from mosaygent.command_runner import run_command
from mosaygent.logger import get_logger
from mosaygent.services.environment import EnvironmentService

logger = get_logger(__name__)


class FirebaseProjectService:
    """Manages Firebase CLI, authentication, and project configuration."""

    def __init__(self):
        self.env_service = EnvironmentService()

    async def check_cli_installed(self) -> dict:
        """Check if Firebase CLI and Google Cloud CLI are installed."""
        logger.info("Checking if Firebase CLI and gcloud CLI are installed")

        firebase_result = await run_command(
            ["firebase", "--version"],
            timeout=5,
            raise_on_error=False
        )

        firebase_installed = firebase_result.success
        firebase_version = firebase_result.stdout.strip() if firebase_installed else None

        if firebase_installed:
            logger.info(f"Firebase CLI is installed: {firebase_version}")
        else:
            logger.warning("Firebase CLI is not installed")

        gcloud_result = await run_command(
            ["gcloud", "version"],
            timeout=5,
            raise_on_error=False
        )

        gcloud_installed = gcloud_result.success
        gcloud_version = None
        if gcloud_installed:
            version_output = gcloud_result.stdout.strip()
            version_match = re.search(r'Google Cloud SDK (\S+)', version_output)
            gcloud_version = version_match.group(1) if version_match else version_output.split('\n')[0]
            logger.info(f"gcloud CLI is installed: {gcloud_version}")
        else:
            logger.warning("gcloud CLI is not installed")

        return {
            "firebase": {
                "installed": firebase_installed,
                "version": firebase_version,
            },
            "gcloud": {
                "installed": gcloud_installed,
                "version": gcloud_version,
            }
        }

    async def check_auth_status(self) -> dict:
        """Check Firebase CLI authentication status."""
        logger.info("Checking Firebase auth status")

        result = await run_command(
            ["firebase", "login:list"],
            timeout=10,
            raise_on_error=False
        )

        if result.success:
            output = result.stdout.strip()

            if "no authorized accounts" in output.lower() or not output:
                logger.warning("No Firebase accounts are logged in")
                return {
                    "logged_in": False,
                    "message": "Run 'firebase login' to authenticate",
                }

            logger.info("User is logged in to Firebase CLI")
            return {
                "logged_in": True,
                "output": output,
            }

        logger.warning("Failed to check Firebase auth status")
        return {
            "logged_in": False,
            "message": "Run 'firebase login' to authenticate",
        }

    async def install_cli(self) -> dict:
        """Attempt to install Firebase CLI using npm."""
        logger.info("Attempting to install Firebase CLI via npm")

        npm_check = await run_command(
            ["npm", "--version"],
            timeout=5,
            raise_on_error=False
        )

        if not npm_check.success:
            logger.error("npm is not installed")
            raise HTTPException(
                status_code=500,
                detail="npm is required to install Firebase CLI. Please install Node.js and npm first."
            )

        logger.info(f"npm is available: {npm_check.stdout.strip()}")

        try:
            logger.info("Installing firebase-tools globally via npm")
            from mosaygent.command_runner import run_command_streaming
            result = run_command_streaming(
                ["npm", "install", "-g", "firebase-tools"],
                timeout=300,
            )

            logger.info("Successfully installed Firebase CLI via npm")
            return {
                "installed": True,
                "method": "npm",
                "output": result.stdout.strip(),
            }
        except Exception as e:
            logger.error(f"npm install failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Installation failed: {str(e)}"
            )

    async def get_login_instructions(self) -> dict:
        """Get instructions for logging into Firebase CLI."""
        logger.info("Returning Firebase login instructions")

        return {
            "instructions": [
                "Open a terminal window",
                "Run the command: firebase login",
                "Follow the prompts to authenticate with your Google account",
                "Once logged in, return here to continue"
            ],
            "command": "firebase login",
            "note": "Make sure Firebase CLI is installed before running this command"
        }

    async def get_project(self) -> dict:
        """Get the currently configured GCloud project."""
        logger.info("Fetching current GCloud project")

        result = await run_command(
            ["gcloud", "config", "get-value", "project"],
            timeout=5
        )

        project_id = result.stdout.strip()

        if not project_id:
            logger.warning("No GCloud project is currently set")
            return {"project_id": None}

        logger.info(f"Current project: {project_id}")
        return {"project_id": project_id}

    async def set_project(self, project_id: str) -> dict:
        """Set the local GCloud project configuration."""
        logger.info(f"Setting GCloud project to: {project_id}")

        config_result = await run_command(
            ["gcloud", "config", "set", "project", project_id],
            timeout=10
        )
        logger.debug(f"gcloud config set project output: {config_result.stdout}")

        quota_result = await run_command(
            ["gcloud", "auth", "application-default", "set-quota-project", project_id],
            timeout=10
        )
        logger.debug(f"gcloud set-quota-project output: {quota_result.stdout}")

        logger.info(f"Successfully set project to: {project_id}")

        return {
            "project_id": project_id,
            "config_output": config_result.stdout.strip(),
            "quota_output": quota_result.stdout.strip(),
        }

    async def disconnect_project(self, repo_path: str | None = None) -> dict:
        """Disconnect from the currently selected Firebase and gcloud project."""
        logger.info("Disconnecting from current Firebase and gcloud project")

        if repo_path:
            firebase_cwd = repo_path
            logger.info(f"Using provided repo path for Firebase: {firebase_cwd}")
        elif self.env_service.project_dir:
            firebase_cwd = str(self.env_service.project_dir)
            logger.info(f"Using configured project directory for Firebase: {firebase_cwd}")
        else:
            firebase_cwd = None
            logger.info("No Firebase project directory specified")

        current_gcloud_result = await run_command(
            ["gcloud", "config", "get-value", "project"],
            timeout=5,
            raise_on_error=False
        )

        previous_gcloud_project = current_gcloud_result.stdout.strip() if current_gcloud_result.success else None

        previous_firebase_project = None
        if firebase_cwd:
            firebase_use_result = await run_command(
                ["firebase", "use"],
                timeout=5,
                cwd=firebase_cwd,
                raise_on_error=False
            )

            if firebase_use_result.success:
                firebase_output = firebase_use_result.stdout.strip()
                if "project" in firebase_output.lower():
                    project_match = re.search(r'project\s+([^\s\)]+)', firebase_output)
                    if project_match:
                        previous_firebase_project = project_match.group(1)

        if previous_gcloud_project:
            logger.info(f"Disconnecting from gcloud project: {previous_gcloud_project}")
        if previous_firebase_project:
            logger.info(f"Disconnecting from Firebase project: {previous_firebase_project}")

        firebase_disconnected = False
        firebase_output = ""
        if firebase_cwd:
            firebase_clear_result = await run_command(
                ["firebase", "use", "--clear"],
                timeout=10,
                cwd=firebase_cwd,
                raise_on_error=False
            )

            if firebase_clear_result.success:
                firebase_disconnected = True
                firebase_output = firebase_clear_result.stdout.strip()
                logger.info("Successfully cleared Firebase project selection")
            else:
                logger.warning(f"Could not clear Firebase project: {firebase_clear_result.stderr}")
                firebase_output = firebase_clear_result.stderr

        gcloud_unset_result = await run_command(
            ["gcloud", "config", "unset", "project"],
            timeout=10,
            raise_on_error=False
        )

        if not gcloud_unset_result.success:
            logger.error(f"Failed to unset gcloud project: {gcloud_unset_result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to unset gcloud project: {gcloud_unset_result.stderr}"
            )

        logger.info("Successfully unset gcloud project")

        quota_unset_result = await run_command(
            ["gcloud", "config", "unset", "billing/quota_project"],
            timeout=10,
            raise_on_error=False
        )

        if quota_unset_result.success:
            logger.info("Successfully unset quota project")
        else:
            logger.debug(f"Could not unset quota project: {quota_unset_result.stderr}")

        logger.info("Successfully disconnected from Firebase and gcloud projects")

        return {
            "disconnected": True,
            "previous_gcloud_project": previous_gcloud_project,
            "previous_firebase_project": previous_firebase_project,
            "firebase_disconnected": firebase_disconnected,
            "gcloud_output": gcloud_unset_result.stdout.strip(),
            "firebase_output": firebase_output,
        }
