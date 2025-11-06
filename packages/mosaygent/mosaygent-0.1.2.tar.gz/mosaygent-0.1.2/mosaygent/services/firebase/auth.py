import firebase_admin
from fastapi import HTTPException
from firebase_admin import auth, credentials

from mosaygent.command_runner import run_command
from mosaygent.logger import get_logger

logger = get_logger(__name__)


class FirebaseAuthService:
    """Manages Firebase Authentication user management."""

    async def check_auth_enabled(self) -> dict:
        """Check if Firebase Auth is enabled in the currently configured project."""
        logger.info("Checking if Firebase Auth is enabled")

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
        logger.info(f"Checking Firebase Auth for project: {project_id}")

        result = await run_command(
            [
                "gcloud", "services", "list",
                "--enabled",
                "--project", project_id,
                "--filter=name:identitytoolkit.googleapis.com",
                "--format=value(name)"
            ],
            timeout=30,
            raise_on_error=False
        )

        if not result.success:
            logger.error(f"Failed to check Firebase Auth status: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check Firebase Auth status: {result.stderr}"
            )

        auth_enabled = "identitytoolkit.googleapis.com" in result.stdout

        if auth_enabled:
            logger.info(f"Firebase Auth is enabled in project {project_id}")
        else:
            logger.info(f"Firebase Auth is not enabled in project {project_id}")

        return {
            "project_id": project_id,
            "auth_enabled": auth_enabled,
        }

    async def get_users_count(self) -> dict:
        """Get the number of registered users in Firebase Auth using Application Default Credentials."""
        logger.info("Fetching Firebase Auth users count")

        try:
            app_name = "auth_count_default"

            try:
                app = firebase_admin.get_app(name=app_name)
                logger.debug("Using existing Firebase Admin app")
            except ValueError:
                logger.info("Initializing Firebase Admin SDK with Application Default Credentials")
                cred = credentials.ApplicationDefault()
                app = firebase_admin.initialize_app(cred, name=app_name)
                logger.info("Successfully initialized Firebase Admin SDK")

            project_id = app.project_id
            logger.info(f"Counting Firebase Auth users for project: {project_id}")

            logger.debug("Listing Firebase Auth users")
            user_count = 0
            page = auth.list_users(app=app)

            while page:
                user_count += len(page.users)
                logger.debug(f"Processed batch, current count: {user_count}")
                page = page.get_next_page()

            logger.info(f"Found {user_count} registered users in project {project_id}")

            return {
                "project_id": project_id,
                "user_count": user_count,
            }

        except auth.UnexpectedResponseError as e:
            logger.error(f"Firebase Auth API error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Firebase Auth API error: {str(e)}"
            )
        except Exception as e:
            logger.exception(f"Failed to count Firebase Auth users: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to count Firebase Auth users: {str(e)}"
            )

    async def get_users_summary(self) -> dict:
        """Get detailed summary of all registered users in Firebase Auth."""
        logger.info("Fetching Firebase Auth users summary")

        try:
            app_name = "auth_summary_default"

            try:
                app = firebase_admin.get_app(name=app_name)
                logger.debug("Using existing Firebase Admin app")
            except ValueError:
                logger.info("Initializing Firebase Admin SDK with Application Default Credentials")
                cred = credentials.ApplicationDefault()
                app = firebase_admin.initialize_app(cred, name=app_name)
                logger.info("Successfully initialized Firebase Admin SDK")

            project_id = app.project_id
            logger.info(f"Fetching users summary for project: {project_id}")

            logger.debug("Listing Firebase Auth users with details")
            users_list = []
            page = auth.list_users(app=app)

            while page:
                for user in page.users:
                    user_data = {
                        "uid": user.uid,
                        "email": user.email,
                        "phone_number": user.phone_number,
                        "display_name": user.display_name,
                        "photo_url": user.photo_url,
                        "disabled": user.disabled,
                        "email_verified": user.email_verified,
                        "provider_id": getattr(user, "provider_id", None),
                        "tenant_id": user.tenant_id,
                        "custom_claims": user.custom_claims,
                    }

                    if user.user_metadata:
                        user_data["metadata"] = {
                            "creation_timestamp": user.user_metadata.creation_timestamp,
                            "last_sign_in_timestamp": user.user_metadata.last_sign_in_timestamp,
                            "last_refresh_timestamp": getattr(user.user_metadata, "last_refresh_timestamp", None),
                        }
                    else:
                        user_data["metadata"] = None

                    if user.provider_data:
                        user_data["providers"] = [
                            {
                                "provider_id": provider.provider_id,
                                "uid": provider.uid,
                                "email": provider.email,
                                "display_name": provider.display_name,
                                "photo_url": provider.photo_url,
                                "phone_number": provider.phone_number,
                            }
                            for provider in user.provider_data
                        ]
                    else:
                        user_data["providers"] = []

                    if hasattr(user, "tokens_valid_after_timestamp"):
                        user_data["tokens_valid_after_timestamp"] = user.tokens_valid_after_timestamp
                    else:
                        user_data["tokens_valid_after_timestamp"] = None

                    users_list.append(user_data)

                logger.debug(f"Processed batch, current total: {len(users_list)}")
                page = page.get_next_page()

            logger.info(f"Retrieved details for {len(users_list)} users in project {project_id}")

            return {
                "project_id": project_id,
                "user_count": len(users_list),
                "users": users_list,
            }

        except auth.UnexpectedResponseError as e:
            logger.error(f"Firebase Auth API error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Firebase Auth API error: {str(e)}"
            )
        except Exception as e:
            logger.exception(f"Failed to fetch Firebase Auth users summary: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch Firebase Auth users summary: {str(e)}"
            )
