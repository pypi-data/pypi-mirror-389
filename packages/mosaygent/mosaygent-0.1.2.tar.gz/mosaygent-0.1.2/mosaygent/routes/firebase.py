from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from mosaygent.logger import get_logger
from mosaygent.services.cloudrun import CloudRunService
from mosaygent.services.firebase import (
    FirebaseAuthService,
    FirebaseConfigService,
    FirebaseDeployService,
    FirebaseFunctionsService,
    FirebaseProjectService,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix='/firebase',
    tags=['Firebase Routes'],
)

project_service = FirebaseProjectService()
deploy_service = FirebaseDeployService()
auth_service = FirebaseAuthService()
functions_service = FirebaseFunctionsService()
config_service = FirebaseConfigService()
cloudrun_service = CloudRunService()


@router.get("/cli-installed")
async def check_cli_installed() -> dict:
    """Check if Firebase CLI and Google Cloud CLI are installed."""
    return await project_service.check_cli_installed()


@router.get("/auth-status")
async def check_firebase_auth_status() -> dict:
    """Check Firebase CLI authentication status."""
    return await project_service.check_auth_status()


@router.post("/install-cli")
async def install_firebase_cli() -> dict:
    """Attempt to install Firebase CLI using npm."""
    return await project_service.install_cli()


@router.get("/login-instructions")
async def get_firebase_login_instructions() -> dict:
    """Get instructions for logging into Firebase CLI."""
    return await project_service.get_login_instructions()


class DeployRequest(BaseModel):
    """Request model for Firebase deployment."""
    project_id: str = Field(min_length=1, description="Firebase project ID")
    repo_path: str | None = Field(default=None, description="Optional repository path (defaults to configured project directory)")


class DeployProjectRequest(BaseModel):
    """Request model for flexible Firebase project deployment."""
    project_id: str = Field(min_length=1, description="Firebase project ID")
    working_directory: str | None = Field(default=None, description="Working directory to run deploy from (defaults to configured project directory)")
    targets: str | None = Field(default=None, description="Deployment targets (e.g., 'functions', 'hosting', 'functions,hosting'). Deploys all if not specified.")
    force: bool = Field(default=False, description="Force deploy without confirmation prompts")


@router.post("/deploy")
async def deploy_firebase(request: DeployRequest) -> dict:
    """Deploy Firebase project (assumes firebase.json exists in repo_path/firebase/)."""
    return await deploy_service.deploy_firebase(
        project_id=request.project_id,
        repo_path=request.repo_path
    )


class SetProjectRequest(BaseModel):
    """Request to set Firebase/GCloud project."""
    project_id: str = Field(min_length=1, description="GCloud project ID")


class FetchFirebaseConfigsRequest(BaseModel):
    """Request to fetch Firebase config files (Android, iOS, and Web)."""
    project_id: str = Field(min_length=1, description="Firebase project ID")
    flutter_app_path: str = Field(min_length=1, description="Path to Flutter app root")
    bundle_id: str = Field(min_length=1, description="Bundle ID used by all platforms (e.g., com.company.appname)")
    firebase_config_path: str | None = Field(
        default=None,
        description="Optional path to firebase_config.dart. Defaults to {flutter_app_path}/lib/backend/firebase/firebase_config.dart"
    )


@router.get("/project")
async def get_project() -> dict:
    """Get the currently configured GCloud project."""
    return await project_service.get_project()


@router.post("/set-project")
async def set_project(request: SetProjectRequest) -> dict:
    """Set the local GCloud project configuration."""
    return await project_service.set_project(request.project_id)


class DisconnectProjectRequest(BaseModel):
    """Request model for disconnecting from projects."""
    repo_path: str | None = Field(default=None, description="Optional repository path for Firebase project disconnection")


@router.post("/disconnect-project")
async def disconnect_project(request: DisconnectProjectRequest) -> dict:
    """Disconnect from the currently selected Firebase and gcloud project."""
    return await project_service.disconnect_project(request.repo_path)


@router.post("/deploy-project")
async def deploy_firebase_project(request: DeployProjectRequest) -> dict:
    """Deploy Firebase project with flexible options for targets and working directory."""
    return await deploy_service.deploy_project(
        project_id=request.project_id,
        working_directory=request.working_directory,
        targets=request.targets,
        force=request.force
    )


@router.get("/auth-enabled")
async def check_auth_enabled() -> dict:
    """Check if Firebase Auth is enabled in the currently configured project."""
    return await auth_service.check_auth_enabled()


@router.get("/auth-users-count")
async def get_auth_users_count() -> dict:
    """Get the number of registered users in Firebase Auth using Application Default Credentials."""
    return await auth_service.get_users_count()


@router.get("/auth-users-summary")
async def get_auth_users_summary() -> dict:
    """Get detailed summary of all registered users in Firebase Auth."""
    return await auth_service.get_users_summary()


@router.get("/functions")
async def list_firebase_functions() -> dict:
    """List all Firebase functions in the currently configured project."""
    return await functions_service.list_functions()


@router.post("/fetch-firebase-configs")
async def fetch_firebase_configs(request: FetchFirebaseConfigsRequest) -> dict:
    """Fetch Firebase config files (Android, iOS, and Web) and save to Flutter app."""
    return await config_service.fetch_configs(
        project_id=request.project_id,
        flutter_app_path=request.flutter_app_path,
        bundle_id=request.bundle_id,
        firebase_config_path=request.firebase_config_path
    )


class FirebaseSecret(BaseModel):
    """Firebase secret with name and value."""
    name: str = Field(min_length=1, description="Name of the secret in Firebase (e.g., 'API_KEY')")
    value: str = Field(min_length=1, description="Value of the secret")


class SetSecretsRequest(BaseModel):
    """Request to set secrets and environment variables in files and optionally upload one to Firebase."""
    secrets: dict[str, str] = Field(description="Dictionary of secret names to values (e.g., {'API_KEY': 'xxx', 'TOKEN': 'yyy'})")
    env_variables: dict[str, str] = Field(description="Dictionary of environment variable names to values (e.g., {'NODE_ENV': 'development', 'PORT': '3000'})")
    environment: Literal["development", "production"] = Field(description="Target environment ('development' or 'production')")
    working_directory: str = Field(min_length=1, description="Directory where env files will be created")
    firebase_secret: FirebaseSecret | None = Field(default=None, description="Optional Firebase secret to upload (name and value)")
    project_id: str | None = Field(default=None, description="Optional Firebase project ID (uses current project if not specified)")


@router.post("/set-secrets")
async def set_firebase_secrets(request: SetSecretsRequest) -> dict:
    """Create or update environment files and optionally upload one secret to Firebase."""
    firebase_secret_name = request.firebase_secret.name if request.firebase_secret else None
    firebase_secret_value = request.firebase_secret.value if request.firebase_secret else None

    return await functions_service.set_secrets(
        secrets=request.secrets,
        env_variables=request.env_variables,
        environment=request.environment,
        working_directory=request.working_directory,
        firebase_secret_name=firebase_secret_name,
        firebase_secret_value=firebase_secret_value,
        project_id=request.project_id
    )


class GetSecretsRequest(BaseModel):
    """Request to read secrets from environment files."""
    working_directory: str = Field(min_length=1, description="Directory where env files are located")
    environment: Literal["development", "production"] = Field(description="Target environment ('development' or 'production')")


@router.post("/get-secrets")
async def get_firebase_secrets(request: GetSecretsRequest) -> dict:
    """Read secrets from environment files (.env.local or .env.prod.yaml)."""
    return await functions_service.get_secrets(
        working_directory=request.working_directory,
        environment=request.environment
    )


class DeployCloudRunRequest(BaseModel):
    """Request to deploy a Cloud Run service."""
    project_id: str = Field(min_length=1, description="Google Cloud project ID")
    project_directory: str = Field(min_length=1, description="Path to project directory containing source code")
    environment: Literal["development", "production"] = Field(description="Target environment ('development' or 'production')")
    region: str = Field(default="us-east1", description="Google Cloud region (default: 'us-east1')")
    service_name: str | None = Field(default=None, description="Optional service name (defaults to directory name with environment suffix)")


@router.post("/deploy-cloud-run")
async def deploy_cloud_run(request: DeployCloudRunRequest) -> dict:
    """Deploy a Cloud Run service from source with environment-specific configuration."""
    return await cloudrun_service.deploy(
        project_id=request.project_id,
        project_directory=request.project_directory,
        environment=request.environment,
        region=request.region,
        service_name=request.service_name
    )
