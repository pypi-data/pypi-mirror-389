import json
import re
from pathlib import Path

from fastapi import HTTPException

from mosaygent.command_runner import run_command
from mosaygent.logger import get_logger

logger = get_logger(__name__)


class FirebaseConfigService:
    """Manages Firebase configuration file operations."""

    async def _get_android_app_id(self, project_id: str, bundle_id: str) -> str:
        """Get Firebase Android app ID from bundle ID."""
        logger.info(f"Looking up Android app with bundle ID {bundle_id} in project {project_id}")

        result = await run_command(
            ["firebase", "apps:list", "--project", project_id, "--json"],
            timeout=30
        )

        try:
            apps_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Firebase apps list: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse Firebase apps list")

        if not apps_data or "result" not in apps_data:
            logger.error("No apps found in Firebase project")
            raise HTTPException(status_code=404, detail="No apps found in Firebase project")

        android_apps = [
            app for app in apps_data["result"]
            if app.get("platform") == "ANDROID" and app.get("appId")
        ]

        if not android_apps:
            logger.error("No Android apps found in Firebase project")
            raise HTTPException(status_code=404, detail="No Android apps found in project")

        matching_app = next(
            (app for app in android_apps if app.get("namespace") == bundle_id),
            None
        )

        if not matching_app:
            logger.error(f"No Android app found with bundle ID {bundle_id}")
            available_bundles = [app.get("namespace") for app in android_apps]
            raise HTTPException(
                status_code=404,
                detail=f"No Android app found with bundle ID {bundle_id}. Available: {available_bundles}"
            )

        app_id = matching_app["appId"]
        logger.info(f"Found Android app ID: {app_id}")
        return app_id

    async def _get_ios_app_id(self, project_id: str, bundle_id: str) -> str:
        """Get Firebase iOS app ID from bundle ID."""
        logger.info(f"Looking up iOS app with bundle ID {bundle_id} in project {project_id}")

        result = await run_command(
            ["firebase", "apps:list", "--project", project_id, "--json"],
            timeout=30
        )

        try:
            apps_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Firebase apps list: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse Firebase apps list")

        if not apps_data or "result" not in apps_data:
            logger.error("No apps found in Firebase project")
            raise HTTPException(status_code=404, detail="No apps found in Firebase project")

        ios_apps = [
            app for app in apps_data["result"]
            if app.get("platform") == "IOS" and app.get("appId")
        ]

        if not ios_apps:
            logger.error("No iOS apps found in Firebase project")
            raise HTTPException(status_code=404, detail="No iOS apps found in project")

        matching_app = next(
            (app for app in ios_apps if app.get("namespace") == bundle_id),
            None
        )

        if not matching_app:
            logger.error(f"No iOS app found with bundle ID {bundle_id}")
            available_bundles = [app.get("namespace") for app in ios_apps]
            raise HTTPException(
                status_code=404,
                detail=f"No iOS app found with bundle ID {bundle_id}. Available: {available_bundles}"
            )

        app_id = matching_app["appId"]
        logger.info(f"Found iOS app ID: {app_id}")
        return app_id

    async def _get_web_app_id(self, project_id: str) -> str:
        """Get Firebase Web app ID. Assumes only one Web app exists per project."""
        logger.info(f"Looking up Web app in project {project_id}")

        result = await run_command(
            ["firebase", "apps:list", "--project", project_id, "--json"],
            timeout=30
        )

        try:
            apps_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Firebase apps list: {e}")
            raise HTTPException(status_code=500, detail="Failed to parse Firebase apps list")

        if not apps_data or "result" not in apps_data:
            logger.error("No apps found in Firebase project")
            raise HTTPException(status_code=404, detail="No apps found in Firebase project")

        web_apps = [
            app for app in apps_data["result"]
            if app.get("platform") == "WEB" and app.get("appId")
        ]

        if not web_apps:
            logger.error("No Web apps found in Firebase project")
            raise HTTPException(status_code=404, detail="No Web apps found in project")

        if len(web_apps) > 1:
            logger.warning(f"Multiple Web apps found ({len(web_apps)}), using the first one")

        web_app = web_apps[0]
        app_id = web_app["appId"]
        app_name = web_app.get("displayName", "Unknown")
        logger.info(f"Found Web app ID: {app_id} (name: {app_name})")
        return app_id

    def _update_firebase_config_dart(self, file_path: Path, web_config: dict) -> None:
        """Update or create firebase_config.dart file with new web configuration values."""
        logger.info(f"Updating firebase_config.dart at {file_path}")

        if not file_path.exists():
            logger.info(f"firebase_config.dart not found at {file_path}, creating new file")

            file_path.parent.mkdir(parents=True, exist_ok=True)

            template_content = f'''import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

class DefaultFirebaseOptions {{
  static FirebaseOptions get currentPlatform {{
    if (kIsWeb) {{
      return web;
    }}
    switch (defaultTargetPlatform) {{
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      case TargetPlatform.macOS:
        return macos;
      case TargetPlatform.windows:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for windows - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      case TargetPlatform.linux:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for linux - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions are not supported for this platform.',
        );
    }}
  }}

  static const FirebaseOptions web = FirebaseOptions(
    apiKey: "{web_config.get("apiKey", "")}",
    appId: "{web_config.get("appId", "")}",
    messagingSenderId: "{web_config.get("messagingSenderId", "")}",
    projectId: "{web_config.get("projectId", "")}",
    authDomain: "{web_config.get("authDomain", "")}",
    storageBucket: "{web_config.get("storageBucket", "")}",
  );

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: "PLACEHOLDER_API_KEY",
    appId: "PLACEHOLDER_APP_ID",
    messagingSenderId: "{web_config.get("messagingSenderId", "")}",
    projectId: "{web_config.get("projectId", "")}",
    storageBucket: "{web_config.get("storageBucket", "")}",
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: "PLACEHOLDER_API_KEY",
    appId: "PLACEHOLDER_APP_ID",
    messagingSenderId: "{web_config.get("messagingSenderId", "")}",
    projectId: "{web_config.get("projectId", "")}",
    storageBucket: "{web_config.get("storageBucket", "")}",
    iosBundleId: "PLACEHOLDER_BUNDLE_ID",
  );

  static const FirebaseOptions macos = FirebaseOptions(
    apiKey: "PLACEHOLDER_API_KEY",
    appId: "PLACEHOLDER_APP_ID",
    messagingSenderId: "{web_config.get("messagingSenderId", "")}",
    projectId: "{web_config.get("projectId", "")}",
    storageBucket: "{web_config.get("storageBucket", "")}",
    iosBundleId: "PLACEHOLDER_BUNDLE_ID",
  );
}}
'''
            file_path.write_text(template_content)
            logger.info(f"Created new firebase_config.dart at {file_path}")
            return

        content = file_path.read_text()

        replacements = {
            "apiKey": web_config.get("apiKey", ""),
            "authDomain": web_config.get("authDomain", ""),
            "projectId": web_config.get("projectId", ""),
            "storageBucket": web_config.get("storageBucket", ""),
            "messagingSenderId": web_config.get("messagingSenderId", ""),
            "appId": web_config.get("appId", ""),
        }

        for key, value in replacements.items():
            pattern = rf'{key}:\s*"[^"]*"'
            replacement = f'{key}: "{value}"'
            content = re.sub(pattern, replacement, content)
            logger.debug(f"Replaced {key} with {value}")

        file_path.write_text(content)
        logger.info(f"Successfully updated firebase_config.dart at {file_path}")

    async def fetch_configs(
        self,
        project_id: str,
        flutter_app_path: str,
        bundle_id: str,
        firebase_config_path: str | None = None
    ) -> dict:
        """Fetch Firebase config files (Android, iOS, and Web) and save to Flutter app."""
        logger.info(
            f"Fetching Firebase configs for {bundle_id} "
            f"from project {project_id}"
        )

        android_app_id = await self._get_android_app_id(project_id, bundle_id)
        ios_app_id = await self._get_ios_app_id(project_id, bundle_id)
        web_app_id = await self._get_web_app_id(project_id)

        logger.info(f"Downloading Android config for app ID: {android_app_id}")
        android_config_result = await run_command(
            ["firebase", "apps:sdkconfig", "android", android_app_id, "--project", project_id],
            timeout=30
        )

        if not android_config_result.stdout.strip():
            logger.error("Firebase returned empty Android config")
            raise HTTPException(status_code=500, detail="Firebase returned empty Android config")

        try:
            android_config_json = json.loads(android_config_result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse google-services.json: {e}")
            raise HTTPException(status_code=500, detail="Invalid Android config JSON received from Firebase")

        android_target_dir = Path(flutter_app_path) / "android" / "app"
        android_target_file = android_target_dir / "google-services.json"

        logger.info(f"Ensuring Android target directory exists: {android_target_dir}")
        android_target_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Writing google-services.json to: {android_target_file}")
        android_target_file.write_text(json.dumps(android_config_json, indent=2))

        logger.info(f"Successfully saved google-services.json to {android_target_file}")

        logger.info(f"Downloading iOS config for app ID: {ios_app_id}")
        ios_config_result = await run_command(
            ["firebase", "apps:sdkconfig", "ios", ios_app_id, "--project", project_id],
            timeout=30
        )

        if not ios_config_result.stdout.strip():
            logger.error("Firebase returned empty iOS config")
            raise HTTPException(status_code=500, detail="Firebase returned empty iOS config")

        ios_target_dir = Path(flutter_app_path) / "ios" / "Runner"
        ios_target_file = ios_target_dir / "GoogleService-Info.plist"

        logger.info(f"Ensuring iOS target directory exists: {ios_target_dir}")
        ios_target_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Writing GoogleService-Info.plist to: {ios_target_file}")
        ios_target_file.write_text(ios_config_result.stdout)

        logger.info(f"Successfully saved GoogleService-Info.plist to {ios_target_file}")

        logger.info(f"Downloading Web config for app ID: {web_app_id}")
        web_config_result = await run_command(
            ["firebase", "apps:sdkconfig", "web", web_app_id, "--project", project_id],
            timeout=30
        )

        if not web_config_result.stdout.strip():
            logger.error("Firebase returned empty Web config")
            raise HTTPException(status_code=500, detail="Firebase returned empty Web config")

        logger.debug(f"Raw web config output: {web_config_result.stdout[:500]}")

        try:
            web_config_json = json.loads(web_config_result.stdout)
            logger.info("Successfully parsed web config as direct JSON")
        except json.JSONDecodeError:
            logger.debug("Direct JSON parsing failed, trying firebase.initializeApp() pattern")
            config_match = re.search(r'firebase\.initializeApp\((\{[\s\S]*?\})\)', web_config_result.stdout)
            if not config_match:
                logger.error("Could not find firebase.initializeApp() in output and direct JSON parsing failed")
                logger.error(f"Raw output was: {web_config_result.stdout}")
                raise HTTPException(status_code=500, detail="Could not parse Web config from Firebase output")

            try:
                web_config_json = json.loads(config_match.group(1))
                logger.info("Successfully parsed web config from firebase.initializeApp() pattern")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Web config JSON: {e}")
                logger.error(f"Extracted config string: {config_match.group(1)}")
                raise HTTPException(status_code=500, detail="Invalid Web config JSON received from Firebase")

        if firebase_config_path:
            firebase_config_path_obj = Path(firebase_config_path)
            if not firebase_config_path_obj.is_absolute():
                firebase_config_path_obj = Path(flutter_app_path) / firebase_config_path
        else:
            firebase_config_path_obj = Path(flutter_app_path) / "lib" / "backend" / "firebase" / "firebase_config.dart"

        logger.info(f"Using firebase_config path: {firebase_config_path_obj}")

        self._update_firebase_config_dart(firebase_config_path_obj, web_config_json)

        return {
            "message": "Firebase configs downloaded successfully",
            "android_file_path": str(android_target_file),
            "ios_file_path": str(ios_target_file),
            "web_config_path": str(firebase_config_path_obj),
            "project_id": project_id,
            "bundle_id": bundle_id,
        }
