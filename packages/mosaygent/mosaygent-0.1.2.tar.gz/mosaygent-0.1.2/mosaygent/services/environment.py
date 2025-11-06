import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil

from mosaygent.logger import get_logger

logger = get_logger(__name__)


class EnvironmentService:
    """Manages project directory and codebase detection."""

    def __init__(self):
        self.project_dir: Optional[Path] = None
        self.config_file = Path.home() / ".mosayic" / "config.txt"
        self._load_project_dir()

    def _load_project_dir(self):
        """Load project directory from config file."""
        if self.config_file.exists():
            try:
                dir_path = self.config_file.read_text().strip()
                if dir_path and Path(dir_path).exists():
                    self.project_dir = Path(dir_path)
                    logger.info(f"Loaded project directory: {self.project_dir}")
            except Exception as e:
                logger.error(f"Failed to load project directory: {e}")

    def set_project_dir(self, path: str) -> bool:
        """Set and persist the project directory."""
        logger.info(f"set_project_dir called with path: {path}, current project_dir: {self.project_dir}")

        dir_path = Path(path)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory does not exist: {path}")

        if not dir_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")

        self.project_dir = dir_path

        # Save to config
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(str(dir_path))
        logger.info(f"Successfully updated project directory to: {self.project_dir}")
        return True

    def get_project_dir(self) -> Optional[str]:
        """Get the current project directory."""
        return str(self.project_dir) if self.project_dir else None

    def check_codebase_status(self, codebase_type: str) -> dict:
        """Check status of a specific codebase (api or flutter)."""
        if not self.project_dir:
            logger.warning("check_codebase_status called but project_dir is not set")
            return {"error": "Project directory not set"}

        logger.info(f"Checking {codebase_type} codebase status in project_dir: {self.project_dir}")

        if codebase_type == "api":
            codebase_dir = self._find_python_codebase()
            marker_file = "pyproject.toml"
        elif codebase_type == "flutter":
            codebase_dir = self.project_dir / "flutterapp"
            marker_file = "pubspec.yaml"
        else:
            return {"error": "Invalid codebase type"}

        if not codebase_dir:
            return {
                "detected": False,
                "path": None,
                "repository_url": None,
                "git": None,
                "running": False,
                "dependencies": False,
                "last_modified": None,
            }

        status = {
            "detected": False,
            "path": str(codebase_dir),
            "repository_url": None,
            "git": None,
            "running": False,
            "dependencies": False,
            "last_modified": None,
        }

        # Check if directory and marker file exist
        if not codebase_dir.exists() or not (codebase_dir / marker_file).exists():
            return status

        status["detected"] = True

        # Check git status
        status["git"] = self._check_git_status(codebase_dir)

        # Extract repository URL from git status if available
        if status["git"] and status["git"].get("remote", {}).get("has_remote"):
            status["repository_url"] = status["git"]["remote"]["remote_url"]
            logger.info(f"Repository URL for {codebase_type}: {status['repository_url']}")

        # Check if running
        if codebase_type == "api":
            status["running"] = self._check_port_in_use(8080)
        elif codebase_type == "flutter":
            status["running"] = self._check_port_in_use(36413)

        # Check dependencies
        if codebase_type == "api":
            status["dependencies"] = (codebase_dir / ".venv").exists()
        elif codebase_type == "flutter":
            status["dependencies"] = (codebase_dir / ".dart_tool").exists()

        # Get last modified time
        status["last_modified"] = self._get_last_modified(codebase_dir)

        return status

    def _find_python_codebase(self) -> Optional[Path]:
        """Find a valid Python codebase, excluding internal tooling directories."""
        if not self.project_dir:
            return None

        excluded_dirs = ["pymosayic", "pymosaygent"]

        logger.info(f"Searching for Python codebase in {self.project_dir}")

        for subdir in sorted(self.project_dir.iterdir()):
            if not subdir.is_dir() or subdir.name in excluded_dirs or subdir.name.startswith('.'):
                continue

            if (subdir / "pyproject.toml").exists():
                logger.info(f"Found Python codebase: {subdir}")
                return subdir

        logger.info(f"No valid Python codebase found in {self.project_dir}")
        return None

    def _get_git_remote_info(self, repo_dir: Path) -> dict:
        """Get git remote information for a repository.

        Args:
            repo_dir: Path to the git repository

        Returns:
            Dict with has_remote (bool) and remote_url (str or None)
        """
        logger.info(f"Checking git remote for repository: {repo_dir}")

        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                remote_url = result.stdout.strip()
                logger.info(f"Found git remote: {remote_url}")
                return {
                    "has_remote": True,
                    "remote_url": remote_url
                }

            logger.info("No git remote configured")
            return {
                "has_remote": False,
                "remote_url": None
            }
        except Exception as e:
            logger.warning(f"Error checking git remote: {e}")
            return {
                "has_remote": False,
                "remote_url": None
            }

    def _check_git_status(self, repo_dir: Path) -> Optional[dict]:
        """Check git status of a repository."""
        if not (repo_dir / ".git").exists():
            return None

        try:
            # Get current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            branch = result.stdout.strip() if result.returncode == 0 else "unknown"

            # Check if dirty
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            is_dirty = bool(result.stdout.strip()) if result.returncode == 0 else False

            # Get remote info
            remote_info = self._get_git_remote_info(repo_dir)

            return {
                "branch": branch,
                "dirty": is_dirty,
                "remote": remote_info,
            }
        except Exception as e:
            logger.debug(f"Failed to check git status: {e}")
            return None

    def _check_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return True
            return False
        except Exception:
            return False

    def _get_last_modified(self, directory: Path) -> Optional[str]:
        """Get the last modified time of files in a directory."""
        try:
            latest_time = 0
            for root, dirs, files in os.walk(directory):
                # Skip hidden and common excluded directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]

                for file in files:
                    if not file.startswith('.'):
                        file_path = Path(root) / file
                        try:
                            mtime = file_path.stat().st_mtime
                            latest_time = max(latest_time, mtime)
                        except Exception:
                            continue

            if latest_time > 0:
                dt = datetime.fromtimestamp(latest_time)
                return dt.isoformat()
            return None
        except Exception as e:
            logger.debug(f"Failed to get last modified time: {e}")
            return None

    def analyze_python_codebase(self, directory_path: str) -> dict:
        """Analyze if a directory contains a Python codebase."""
        logger.info(f"Analyzing directory for Python codebase: {directory_path}")

        dir_path = Path(directory_path)

        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {directory_path}")
            raise FileNotFoundError(f"Directory does not exist: {directory_path}")

        if not dir_path.is_dir():
            logger.warning(f"Path is not a directory: {directory_path}")
            raise NotADirectoryError(f"Path is not a directory: {directory_path}")

        excluded_dirs = ["pymosayic", "pymosaygent"]
        dir_name = dir_path.name

        if dir_name in excluded_dirs:
            logger.info(f"Directory {dir_name} is excluded, searching for alternative Python codebase")
            parent_dir = dir_path.parent

            for subdir in sorted(parent_dir.iterdir()):
                if not subdir.is_dir() or subdir.name in excluded_dirs or subdir.name.startswith('.'):
                    continue

                if (subdir / "pyproject.toml").exists():
                    logger.info(f"Found alternative Python codebase: {subdir}")
                    return {
                        "is_python_codebase": True,
                        "path": str(subdir),
                        "marker_file": "pyproject.toml",
                        "marker_exists": True,
                        "venv_exists": (subdir / ".venv").exists(),
                        "git_initialized": (subdir / ".git").exists(),
                        "redirected_from": str(dir_path)
                    }

            logger.info(f"No alternative Python codebase found in {parent_dir}")
            return {
                "is_python_codebase": False,
                "path": str(dir_path),
                "marker_file": "pyproject.toml",
                "marker_exists": False,
                "reason": f"Directory '{dir_name}' is excluded and no alternative found"
            }

        pyproject_path = dir_path / "pyproject.toml"
        is_python_codebase = pyproject_path.exists()

        logger.info(f"Python codebase detected: {is_python_codebase} at {directory_path}")

        result = {
            "is_python_codebase": is_python_codebase,
            "path": str(dir_path),
            "marker_file": "pyproject.toml",
            "marker_exists": is_python_codebase,
        }

        if is_python_codebase:
            result["venv_exists"] = (dir_path / ".venv").exists()
            result["git_initialized"] = (dir_path / ".git").exists()

        return result

    def analyze_flutter_codebase(self, directory_path: str) -> dict:
        """Analyze if a directory contains a Flutter codebase."""
        logger.info(f"Analyzing directory for Flutter codebase: {directory_path}")

        dir_path = Path(directory_path)

        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {directory_path}")
            raise FileNotFoundError(f"Directory does not exist: {directory_path}")

        if not dir_path.is_dir():
            logger.warning(f"Path is not a directory: {directory_path}")
            raise NotADirectoryError(f"Path is not a directory: {directory_path}")

        pubspec_path = dir_path / "pubspec.yaml"
        is_flutter_codebase = pubspec_path.exists()

        logger.info(f"Flutter codebase detected: {is_flutter_codebase} at {directory_path}")

        result = {
            "is_flutter_codebase": is_flutter_codebase,
            "path": str(dir_path),
            "marker_file": "pubspec.yaml",
            "marker_exists": is_flutter_codebase,
        }

        if is_flutter_codebase:
            result["dependencies_installed"] = (dir_path / ".dart_tool").exists()
            result["git_initialized"] = (dir_path / ".git").exists()

        return result

    async def clone_repository(self, repo_type: str) -> dict:
        """Clone a repository (api or flutter)."""
        if not self.project_dir:
            raise ValueError("Project directory not set")

        repos = {
            "api": ("git@github.com:mosayic-io/python-api.git", "pymosaygent"),
            "flutter": ("git@github.com:mosayic-io/flutterapp.git", "flutterapp"),
        }

        if repo_type not in repos:
            raise ValueError(f"Invalid repository type: {repo_type}")

        url, dir_name = repos[repo_type]
        target_dir = self.project_dir / dir_name

        if target_dir.exists():
            raise FileExistsError(f"Directory already exists: {target_dir}")

        logger.info(f"Cloning {repo_type} repository to {target_dir}")

        try:
            result = subprocess.run(
                ["git", "clone", url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"Git clone failed: {result.stderr}")

            return {
                "success": True,
                "path": str(target_dir),
                "message": f"Successfully cloned {repo_type} repository"
            }
        except subprocess.TimeoutExpired:
            raise RuntimeError("Clone operation timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to clone repository: {str(e)}")
