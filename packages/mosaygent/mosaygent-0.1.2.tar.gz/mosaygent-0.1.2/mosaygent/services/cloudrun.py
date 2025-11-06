import subprocess
from pathlib import Path

from fastapi import HTTPException

from mosaygent.command_runner import run_command
from mosaygent.logger import get_logger

logger = get_logger(__name__)


class CloudRunService:
    """Manages Google Cloud Run deployment operations."""

    async def _get_current_branch(self, project_directory: str) -> str:
        """Get the current git branch in the project directory."""
        logger.info(f"Getting current git branch in {project_directory}")

        result = await run_command(
            ["git", "branch", "--show-current"],
            timeout=5,
            cwd=project_directory,
            raise_on_error=False
        )

        if not result.success:
            logger.error(f"Failed to get current git branch: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get current git branch: {result.stderr}"
            )

        branch = result.stdout.strip()
        logger.info(f"Current branch: {branch}")
        return branch

    async def _get_project_number(self, project_id: str) -> str:
        """Get the project number from project ID."""
        logger.info(f"Getting project number for project: {project_id}")

        result = await run_command(
            ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
            timeout=10,
            raise_on_error=False
        )

        if not result.success:
            logger.error(f"Failed to get project number: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get project number for project '{project_id}': {result.stderr}"
            )

        project_number = result.stdout.strip()
        if not project_number:
            logger.error(f"Project number is empty for project: {project_id}")
            raise HTTPException(
                status_code=500,
                detail=f"Could not retrieve project number for project '{project_id}'"
            )

        logger.info(f"Project number: {project_number}")
        return project_number

    async def _verify_secret_exists(self, secret_name: str, project_id: str) -> bool:
        """Verify that a secret exists in Google Secret Manager."""
        logger.info(f"Verifying secret '{secret_name}' exists in project {project_id}")

        result = await run_command(
            ["gcloud", "secrets", "describe", secret_name, "--project", project_id],
            timeout=10,
            raise_on_error=False
        )

        exists = result.success
        if exists:
            logger.info(f"Secret '{secret_name}' exists")
        else:
            logger.warning(f"Secret '{secret_name}' does not exist")

        return exists

    async def _grant_secret_access(
        self,
        service_account: str,
        secret_names: list[str],
        project_id: str
    ) -> bool:
        """
        Attempt to grant Secret Manager Secret Accessor role to service account.

        Returns:
            True if all secrets were granted successfully, False otherwise
        """
        logger.info(f"Attempting to grant Secret Accessor role to {service_account}")

        member = f"serviceAccount:{service_account}"

        for secret_name in secret_names:
            result = await run_command(
                [
                    "gcloud", "secrets", "add-iam-policy-binding", secret_name,
                    "--member", member,
                    "--role", "roles/secretmanager.secretAccessor",
                    "--project", project_id
                ],
                timeout=15,
                raise_on_error=False
            )

            if not result.success:
                logger.error(f"Failed to grant access to '{secret_name}': {result.stderr}")
                return False

            logger.info(f"Successfully granted access to '{secret_name}'")

        logger.info("Successfully granted Secret Accessor role for all secrets")
        return True

    async def deploy(
        self,
        project_id: str,
        project_directory: str,
        environment: str,
        region: str = "us-east1",
        service_name: str | None = None
    ) -> dict:
        """
        Deploy a Cloud Run service from source.

        Args:
            project_id: Google Cloud project ID
            project_directory: Path to the project directory containing source code
            environment: Target environment ("development" or "production")
            region: Google Cloud region (default: "us-east1")
            service_name: Optional service name (defaults to directory name with environment suffix)

        Returns:
            Dictionary with deployment results
        """
        logger.info(f"Starting Cloud Run deployment for project: {project_id}")
        logger.info(f"Environment: {environment}, Region: {region}")

        project_path = Path(project_directory).resolve()
        if not project_path.exists():
            logger.error(f"Project directory does not exist: {project_path}")
            raise HTTPException(
                status_code=400,
                detail=f"Project directory does not exist: {project_path}"
            )

        if not project_path.is_dir():
            logger.error(f"Project path is not a directory: {project_path}")
            raise HTTPException(
                status_code=400,
                detail=f"Project path is not a directory: {project_path}"
            )

        if environment not in ["development", "production"]:
            logger.error(f"Invalid environment: {environment}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid environment '{environment}'. Must be 'development' or 'production'"
            )

        expected_branch = "develop" if environment == "development" else "main"
        current_branch = await self._get_current_branch(str(project_path))

        if current_branch != expected_branch:
            logger.error(f"Branch mismatch: expected '{expected_branch}', but on '{current_branch}'")
            raise HTTPException(
                status_code=400,
                detail=f"Cannot deploy {environment} environment from branch '{current_branch}'. Must be on '{expected_branch}' branch."
            )

        if not service_name:
            service_name = f"{project_path.name}-{environment}"
            logger.info(f"Service name not provided, using default: {service_name}")

        env_file = ".env.dev.yaml" if environment == "development" else ".env.prod.yaml"
        env_file_path = project_path / env_file

        if not env_file_path.exists():
            logger.error(f"Environment file not found: {env_file_path}")
            raise HTTPException(
                status_code=400,
                detail=f"Environment file not found: {env_file_path}. Create it before deploying."
            )

        logger.info(f"Using environment file: {env_file_path}")

        project_number = await self._get_project_number(project_id)

        required_secrets = ["SUPABASE_SECRET_KEY", "RESEND_API_KEY"]
        missing_secrets = []

        for secret_name in required_secrets:
            exists = await self._verify_secret_exists(secret_name, project_id)
            if not exists:
                missing_secrets.append(secret_name)

        if missing_secrets:
            logger.error(f"Missing required secrets: {missing_secrets}")
            raise HTTPException(
                status_code=400,
                detail=f"Missing required secrets in Google Secret Manager: {', '.join(missing_secrets)}. Create these secrets before deploying."
            )

        logger.info("All required secrets verified")

        service_account = f"{project_number}-compute@developer.gserviceaccount.com"
        secrets_flag = f"SUPABASE_SECRET_KEY=SUPABASE_SECRET_KEY:latest,RESEND_API_KEY=RESEND_API_KEY:latest"

        deploy_command = [
            "gcloud", "run", "deploy", service_name,
            "--source", str(project_path),
            "--region", region,
            "--platform", "managed",
            "--allow-unauthenticated",
            # "--service-account", service_account,
            "--env-vars-file", str(env_file_path),
            "--set-secrets", secrets_flag,
            "--project", project_id,
            "--quiet"
        ]

        logger.info(f"Executing deployment command: {' '.join(deploy_command)}")

        result = await run_command(
            deploy_command,
            timeout=600,
            cwd=str(project_path),
            raise_on_error=False
        )

        if not result.success:
            logger.error(f"Cloud Run deployment failed: {result.stderr}")

            if "Permission denied on secret" in result.stderr and "secretmanager.secretAccessor" in result.stderr:
                logger.warning("Deployment failed due to missing Secret Manager permissions")
                logger.info("Attempting to grant permissions and retry...")

                grant_success = await self._grant_secret_access(
                    service_account,
                    required_secrets,
                    project_id
                )

                if not grant_success:
                    logger.error("Failed to automatically grant permissions")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Deployment failed due to missing Secret Manager permissions. Please grant the 'Secret Manager Secret Accessor' role (roles/secretmanager.secretAccessor) to service account {service_account} using: gcloud projects add-iam-policy-binding {project_id} --member='serviceAccount:{service_account}' --role='roles/secretmanager.secretAccessor'"
                    )

                logger.info("Retrying deployment...")

                result = await run_command(
                    deploy_command,
                    timeout=600,
                    cwd=str(project_path),
                    raise_on_error=False
                )

                if not result.success:
                    logger.error(f"Deployment failed on retry: {result.stderr}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Cloud Run deployment failed: {result.stderr}"
                    )

            elif "secret" in result.stderr.lower() or "Secret" in result.stderr:
                raise HTTPException(
                    status_code=400,
                    detail=f"Deployment failed due to secret configuration error: {result.stderr}"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Cloud Run deployment failed: {result.stderr}"
                )

        logger.info("Cloud Run deployment completed successfully")
        logger.debug(f"Deployment output: {result.stdout}")

        service_url_line = [line for line in result.stdout.split('\n') if 'Service URL:' in line or 'https://' in line]
        service_url = service_url_line[0].split()[-1] if service_url_line else None

        return {
            "project_id": project_id,
            "service_name": service_name,
            "region": region,
            "environment": environment,
            "branch": current_branch,
            "service_url": service_url,
            "service_account": service_account,
            "output": result.stdout
        }
