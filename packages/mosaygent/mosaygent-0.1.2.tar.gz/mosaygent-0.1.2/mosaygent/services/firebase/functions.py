import json
import subprocess
from pathlib import Path

import yaml
from fastapi import HTTPException

from mosaygent.command_runner import run_command
from mosaygent.logger import get_logger

logger = get_logger(__name__)


class FirebaseFunctionsService:
    """Manages Firebase Cloud Functions operations."""

    async def list_functions(self) -> dict:
        """List all Firebase functions in the currently configured project."""
        logger.info("Fetching list of Firebase functions")

        project_result = await run_command(
            ["gcloud", "config", "get-value", "project"],
            timeout=5,
            raise_on_error=False
        )

        if not project_result.success or not project_result.stdout.strip():
            logger.error("No GCloud project is currently configured")
            raise HTTPException(
                status_code=400,
                detail="No GCloud project configured. Set a project first using /set-project"
            )

        project_id = project_result.stdout.strip()
        logger.info(f"Listing Firebase functions for project: {project_id}")

        result = await run_command(
            ["firebase", "functions:list", "--project", project_id, "--json"],
            timeout=30,
            raise_on_error=False
        )

        if not result.success:
            logger.error(f"Failed to list Firebase functions: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list Firebase functions: {result.stderr}"
            )

        try:
            functions_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Firebase functions list: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to parse Firebase functions list"
            )

        logger.debug(f"Raw functions data type: {type(functions_data)}")
        logger.debug(f"Raw functions data: {functions_data}")

        if not functions_data:
            logger.info(f"No functions found in project {project_id}")
            return {
                "project_id": project_id,
                "functions": [],
                "count": 0
            }

        functions_list = []

        if isinstance(functions_data, dict):
            if "result" in functions_data:
                functions_array = functions_data["result"]
            else:
                functions_array = [functions_data]
        elif isinstance(functions_data, list):
            functions_array = functions_data
        else:
            logger.error(f"Unexpected functions data type: {type(functions_data)}")
            raise HTTPException(
                status_code=500,
                detail="Unexpected response format from Firebase CLI"
            )

        for func in functions_array:
            if isinstance(func, str):
                logger.warning(f"Function is a string, not a dict: {func}")
                functions_list.append({
                    "name": func,
                    "url": None,
                    "runtime": None,
                    "state": None,
                    "region": None,
                })
                continue

            if not isinstance(func, dict):
                logger.warning(f"Skipping non-dict function: {func}")
                continue

            trigger_type = None
            if "callableTrigger" in func:
                trigger_type = "callable"
            elif "httpsTrigger" in func:
                trigger_type = "https"
            elif "eventTrigger" in func:
                trigger_type = "event"

            function_name = func.get("id")
            function_region = func.get("region")
            function_platform = func.get("platform")

            logs_url = None
            if function_name and function_region:
                if function_platform == "gcfv2":
                    logs_url = f"https://console.cloud.google.com/run/detail/{function_region}/{function_name}/logs?project={project_id}"
                else:
                    logs_url = f"https://console.cloud.google.com/functions/details/{function_region}/{function_name}?project={project_id}&tab=logs"

            function_info = {
                "name": function_name,
                "url": func.get("uri"),
                "logs_url": logs_url,
                "entry_point": func.get("entryPoint"),
                "runtime": func.get("runtime"),
                "state": func.get("state"),
                "region": function_region,
                "platform": function_platform,
                "trigger_type": trigger_type,
                "security_level": func.get("securityLevel"),
                "ingress_settings": func.get("ingressSettings"),
                "memory_mb": func.get("availableMemoryMb"),
                "timeout_seconds": func.get("timeoutSeconds"),
                "codebase": func.get("codebase"),
                "deployment_hash": func.get("hash"),
                "service_account": func.get("serviceAccount"),
                "labels": func.get("labels", {}),
            }

            if trigger_type == "event" and "eventTrigger" in func:
                function_info["event_trigger"] = {
                    "event_type": func["eventTrigger"].get("eventType"),
                    "resource": func["eventTrigger"].get("resource"),
                    "service": func["eventTrigger"].get("service"),
                }

            functions_list.append(function_info)

        logger.info(f"Found {len(functions_list)} functions in project {project_id}")

        return {
            "project_id": project_id,
            "functions": functions_list,
            "count": len(functions_list)
        }

    async def set_secrets(
        self,
        secrets: dict[str, str],
        env_variables: dict[str, str],
        environment: str,
        working_directory: str,
        firebase_secret_name: str | None = None,
        firebase_secret_value: str | None = None,
        project_id: str | None = None
    ) -> dict:
        """
        Create or update environment files and optionally upload one secret to Firebase.

        Args:
            secrets: Dictionary of secret names to values (e.g., {"API_KEY": "xxx", "TOKEN": "yyy"})
            env_variables: Dictionary of environment variable names to values (e.g., {"NODE_ENV": "development"})
            environment: Target environment ("development" or "production")
            working_directory: Directory where env files will be created
            firebase_secret_name: Optional name of the secret to upload to Firebase
            firebase_secret_value: Optional value of the secret to upload to Firebase
            project_id: Optional Firebase project ID (uses current project if not specified)

        Returns:
            Dictionary with operation results
        """
        logger.info(f"Setting {len(secrets)} secrets and {len(env_variables)} env variables for {environment} environment")

        firebase_secret_uploaded = False
        firebase_secret_error = None

        if firebase_secret_name and firebase_secret_value:
            if not project_id:
                project_result = await run_command(
                    ["gcloud", "config", "get-value", "project"],
                    timeout=5,
                    raise_on_error=False
                )

                if not project_result.success or not project_result.stdout.strip():
                    logger.error("No GCloud project is currently configured")
                    raise HTTPException(
                        status_code=400,
                        detail="No GCloud project configured. Set a project first using /set-project"
                    )

                project_id = project_result.stdout.strip()

            logger.info(f"Uploading secret '{firebase_secret_name}' to Firebase project: {project_id}")

            try:
                process = subprocess.run(
                    ["firebase", "functions:secrets:set", firebase_secret_name, "--project", project_id, "--data-file", "-"],
                    input=firebase_secret_value,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if process.returncode != 0:
                    logger.error(f"Failed to upload secret '{firebase_secret_name}': {process.stderr}")
                    firebase_secret_error = process.stderr.strip()
                else:
                    logger.info(f"Successfully uploaded secret '{firebase_secret_name}' to Firebase")
                    logger.debug(f"Firebase CLI output: {process.stdout}")
                    firebase_secret_uploaded = True

            except FileNotFoundError:
                logger.error("Firebase CLI not found")
                raise HTTPException(
                    status_code=404,
                    detail="Firebase CLI not found. Is it installed and in PATH?"
                )
            except subprocess.TimeoutExpired:
                logger.error(f"Uploading secret '{firebase_secret_name}' timed out after 60 seconds")
                firebase_secret_error = "Timeout after 60 seconds"
            except Exception as e:
                logger.exception(f"Unexpected error uploading secret '{firebase_secret_name}': {e}")
                firebase_secret_error = str(e)
        else:
            logger.info("No firebase_secret provided, skipping Firebase upload")

        work_dir = Path(working_directory).resolve()
        logger.info(f"Creating environment file in directory: {work_dir}")

        if not work_dir.exists():
            logger.error(f"Working directory does not exist: {work_dir}")
            raise HTTPException(
                status_code=400,
                detail=f"Working directory does not exist: {work_dir}"
            )

        if environment == "development":
            env_local_path = work_dir / ".env.local"
            logger.info(f"Creating .env.local file at: {env_local_path}")

            combined_vars = {**secrets, **env_variables}
            env_local_content = "\n".join([f"{key}={value}" for key, value in combined_vars.items()])

            try:
                env_local_path.write_text(env_local_content)
                logger.info(f"Successfully created/updated .env.local with {len(combined_vars)} items (secrets + env variables)")
            except Exception as e:
                logger.exception(f"Failed to write .env.local file: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to write .env.local file: {str(e)}"
                )

            env_dev_yaml_path = work_dir / ".env.dev.yaml"
            logger.info(f"Creating .env.dev.yaml file at: {env_dev_yaml_path}")

            try:
                with open(env_dev_yaml_path, 'w') as f:
                    yaml.dump(env_variables, f, default_flow_style=False, sort_keys=False)
                logger.info(f"Successfully created/updated .env.dev.yaml with {len(env_variables)} env variables")
            except Exception as e:
                logger.exception(f"Failed to write .env.dev.yaml file: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to write .env.dev.yaml file: {str(e)}"
                )

        elif environment == "production":
            env_prod_yaml_path = work_dir / ".env.prod.yaml"
            logger.info(f"Creating .env.prod.yaml file at: {env_prod_yaml_path}")

            try:
                with open(env_prod_yaml_path, 'w') as f:
                    yaml.dump(env_variables, f, default_flow_style=False, sort_keys=False)
                logger.info(f"Successfully created/updated .env.prod.yaml with {len(env_variables)} env variables")
            except Exception as e:
                logger.exception(f"Failed to write .env.prod.yaml file: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to write .env.prod.yaml file: {str(e)}"
                )

        else:
            logger.error(f"Invalid environment: {environment}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid environment '{environment}'. Must be 'development' or 'production'"
            )

        logger.info(f"Operation completed. Secrets: {len(secrets)}, Env variables: {len(env_variables)}, Firebase upload: {firebase_secret_uploaded}")

        response = {
            "environment": environment,
            "secrets_count": len(secrets),
            "env_variables_count": len(env_variables),
            "firebase_secret_uploaded": firebase_secret_uploaded
        }

        if firebase_secret_name:
            response["firebase_secret_name"] = firebase_secret_name

        if firebase_secret_error:
            response["firebase_secret_error"] = firebase_secret_error

        if project_id:
            response["project_id"] = project_id

        return response

    async def get_secrets(self, working_directory: str, environment: str) -> dict:
        """
        Read secrets from environment files.

        Args:
            working_directory: Directory where env files are located
            environment: Target environment ("development" or "production")

        Returns:
            Dictionary with secrets and file information
        """
        logger.info(f"Reading secrets from {environment} environment file")

        work_dir = Path(working_directory).resolve()
        logger.info(f"Reading environment file from directory: {work_dir}")

        if not work_dir.exists():
            logger.error(f"Working directory does not exist: {work_dir}")
            raise HTTPException(
                status_code=400,
                detail=f"Working directory does not exist: {work_dir}"
            )

        if environment == "development":
            env_file_path = work_dir / ".env.local"
            logger.info(f"Reading .env.local file at: {env_file_path}")

            if not env_file_path.exists():
                logger.info(f".env.local file not found at: {env_file_path}, returning empty response")
                return {
                    "environment": environment,
                    "secrets": {},
                    "secrets_count": 0
                }

            try:
                content = env_file_path.read_text()
                secrets = {}

                for line in content.strip().split('\n'):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    if '=' in line:
                        key, value = line.split('=', 1)
                        secrets[key.strip()] = value.strip()

                logger.info(f"Successfully read {len(secrets)} secrets from .env.local")

                return {
                    "environment": environment,
                    "secrets": secrets,
                    "secrets_count": len(secrets)
                }

            except Exception as e:
                logger.exception(f"Failed to read .env.local file: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to read .env.local file: {str(e)}"
                )

        elif environment == "production":
            env_file_path = work_dir / ".env.prod.yaml"
            logger.info(f"Reading .env.prod.yaml file at: {env_file_path}")

            if not env_file_path.exists():
                logger.info(f".env.prod.yaml file not found at: {env_file_path}, returning empty response")
                return {
                    "environment": environment,
                    "secrets": {},
                    "secrets_count": 0
                }

            try:
                with open(env_file_path, 'r') as f:
                    secrets = yaml.safe_load(f)

                if not isinstance(secrets, dict):
                    logger.error(f"Invalid YAML format in .env.prod.yaml: expected dict, got {type(secrets)}")
                    raise HTTPException(
                        status_code=500,
                        detail="Invalid YAML format: expected dictionary of key-value pairs"
                    )

                logger.info(f"Successfully read {len(secrets)} secrets from .env.prod.yaml")

                return {
                    "environment": environment,
                    "secrets": secrets,
                    "secrets_count": len(secrets)
                }

            except yaml.YAMLError as e:
                logger.exception(f"Failed to parse .env.prod.yaml file: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse YAML file: {str(e)}"
                )
            except Exception as e:
                logger.exception(f"Failed to read .env.prod.yaml file: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to read .env.prod.yaml file: {str(e)}"
                )

        else:
            logger.error(f"Invalid environment: {environment}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid environment '{environment}'. Must be 'development' or 'production'"
            )
