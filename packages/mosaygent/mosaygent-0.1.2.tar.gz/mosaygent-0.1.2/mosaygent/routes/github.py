import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mosaygent.command_runner import run_command, run_command_streaming
from mosaygent.logger import get_logger
from mosaygent.services.environment import EnvironmentService

logger = get_logger(__name__)

router = APIRouter(
    prefix='/github',
    tags=['GitHub Routes'],
)

env_service = EnvironmentService()


@router.get("/gh-installed")
async def check_gh_installed() -> dict:
    """Check if GitHub CLI (gh) is installed."""
    logger.info("Checking if gh CLI is installed")

    result = await run_command(["gh", "--version"], timeout=5, raise_on_error=False)

    if result.success:
        version_match = re.search(r'gh version (\S+)', result.stdout)
        version = version_match.group(1) if version_match else result.stdout.strip()
        logger.info(f"gh CLI is installed: {version}")

        return {
            "installed": True,
            "version": version,
        }

    logger.warning("gh CLI is not installed")
    return {
        "installed": False,
        "install_instructions": {
            "macos": "brew install gh",
            "linux": "See https://github.com/cli/cli/blob/trunk/docs/install_linux.md",
            "windows": "winget install --id GitHub.cli",
        }
    }



@router.get("/auth-status")
async def check_auth_status() -> dict:
    """Check GitHub CLI authentication status."""
    logger.info("Checking gh auth status")

    result = await run_command(["gh", "auth", "status"], timeout=5, raise_on_error=False)

    if result.success:
        logger.info("User is logged in to GitHub CLI")
        return {
            "logged_in": True,
            "output": result.stdout.strip(),
        }

    logger.warning("User is not logged in to GitHub CLI")
    return {
        "logged_in": False,
        "message": "Run 'gh auth login' to authenticate",
    }


@router.post("/auth-login")
async def initiate_auth_login() -> dict:
    """Initiate GitHub CLI login using PTY - prints authentication URL in server logs."""
    logger.info("Initiating gh auth login with PTY")

    try:
        import pty
        import os
        import select

        master, slave = pty.openpty()

        import subprocess
        process = subprocess.Popen(
            ["gh", "auth", "login", "--web"],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            text=True,
        )

        os.close(slave)

        output_lines = []

        while True:
            ready, _, _ = select.select([master], [], [], 1.0)
            if ready:
                try:
                    data = os.read(master, 1024).decode()
                    if not data:
                        break
                    logger.info(f"[gh] {data.rstrip()}")
                    output_lines.append(data)

                    if "What is your preferred protocol" in data or "HTTPS" in data and "SSH" in data:
                        logger.info("Selecting SSH for git protocol")
                        os.write(master, b"\x1b[B\n")  # Down arrow + Enter to select SSH
                    elif "Upload your SSH public key" in data:
                        logger.info("Selecting YES to upload SSH public key")
                        os.write(master, b"\x1b[D\n")  # Left arrow to select Yes, then Enter
                    elif "Press Enter" in data:
                        logger.info("Sending Enter to continue")
                        os.write(master, b"\n")
                    elif "Login with a web browser" in data:
                        logger.info("Selecting web browser login")
                        os.write(master, b"\n")
                except OSError:
                    break

            if process.poll() is not None:
                break

        os.close(master)
        process.wait()

        output = ''.join(output_lines)

        logger.info(f"gh auth login completed with code {process.returncode}")
        return {
            "message": "Check server logs for authentication URL and code",
            "output": output,
        }

    except Exception as e:
        logger.error(f"GitHub CLI login failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )


class CommitPushRequest(BaseModel):
    """Request model for commit and push operations."""
    message: str
    add_all: bool = True
    repo_path: Optional[str] = None


class SwitchBranchRequest(BaseModel):
    """Request model for branch switching operations."""
    branch_name: str
    commit_message: str = "WIP: auto-commit before branch switch"
    repo_path: Optional[str] = None


@router.post("/commit-push")
async def commit_and_push(request: CommitPushRequest) -> dict:
    """Add, commit, and push changes to GitHub.

    Rejects requests if the current branch is 'main' with a 428 status code.
    """
    logger.info("Starting commit and push operation")

    if request.repo_path:
        project_dir = request.repo_path
        logger.info(f"Using provided repo path: {project_dir}")
    elif env_service.project_dir:
        project_dir = str(env_service.project_dir)
        logger.info(f"Using project directory: {project_dir}")
    else:
        logger.error("No repository path provided and project directory not set")
        raise HTTPException(
            status_code=500,
            detail="No repo_path provided and project directory not configured"
        )

    branch_result = await run_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        timeout=5,
        cwd=project_dir,
        raise_on_error=False
    )

    if not branch_result.success:
        logger.error("Failed to get current branch")
        raise HTTPException(
            status_code=500,
            detail="Failed to determine current branch"
        )

    current_branch = branch_result.stdout.strip()
    logger.info(f"Current branch: {current_branch}")

    if current_branch == "main":
        logger.warning("Rejected commit-push attempt on main branch")
        raise HTTPException(
            status_code=428,
            detail="Cannot commit and push directly to main branch. Please use a feature branch."
        )

    try:
        if request.add_all:
            logger.info("Running git add -A")
            add_result = run_command_streaming(
                ["git", "add", "-A"],
                timeout=30,
                cwd=project_dir
            )
            logger.info(f"Git add completed: {add_result.stdout.strip()}")

        logger.info(f"Committing with message: {request.message}")
        commit_result = run_command_streaming(
            ["git", "commit", "-m", request.message],
            timeout=30,
            cwd=project_dir
        )
        logger.info(f"Git commit completed: {commit_result.stdout.strip()}")

        logger.info(f"Pushing to remote branch: {current_branch}")
        push_result = run_command_streaming(
            ["git", "push", "origin", current_branch],
            timeout=120,
            cwd=project_dir
        )
        logger.info(f"Git push completed: {push_result.stdout.strip()}")

        logger.info("Commit and push operation completed successfully")
        return {
            "branch": current_branch,
            "commit_message": request.message,
            "push_output": push_result.stdout.strip()
        }

    except Exception as e:
        logger.exception(f"Commit and push operation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Git operation failed: {str(e)}"
        )


@router.post("/switch-branch")
async def switch_branch(request: SwitchBranchRequest) -> dict:
    """Switch to a different branch, committing any unsaved changes first."""
    logger.info(f"Attempting to switch to branch: {request.branch_name}")

    if request.repo_path:
        project_dir = request.repo_path
        logger.info(f"Using provided repo path: {project_dir}")
    elif env_service.project_dir:
        project_dir = str(env_service.project_dir)
        logger.info(f"Using project directory: {project_dir}")
    else:
        logger.error("No repository path provided and project directory not set")
        raise HTTPException(
            status_code=500,
            detail="No repo_path provided and project directory not configured"
        )

    status_result = await run_command(
        ["git", "status", "--porcelain"],
        timeout=5,
        cwd=project_dir,
        raise_on_error=False
    )

    if not status_result.success:
        logger.error(f"Failed to check git status. Return code: {status_result.return_code}, stderr: {status_result.stderr}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check repository status: {status_result.stderr or 'Unknown error'}"
        )

    has_changes = bool(status_result.stdout.strip())
    committed = False

    if has_changes:
        logger.info("Detected uncommitted changes, committing before switch")
        try:
            logger.info("Running git add -A")
            add_result = run_command_streaming(
                ["git", "add", "-A"],
                timeout=30,
                cwd=project_dir
            )
            logger.info(f"Git add completed: {add_result.stdout.strip()}")

            logger.info(f"Committing with message: {request.commit_message}")
            commit_result = run_command_streaming(
                ["git", "commit", "-m", request.commit_message],
                timeout=30,
                cwd=project_dir
            )
            logger.info(f"Git commit completed: {commit_result.stdout.strip()}")
            committed = True

        except Exception as e:
            logger.exception(f"Failed to commit changes: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to commit changes before switching: {str(e)}"
            )
    else:
        logger.info("No uncommitted changes detected")

    try:
        logger.info(f"Switching to branch: {request.branch_name}")
        checkout_result = run_command_streaming(
            ["git", "checkout", request.branch_name],
            timeout=30,
            cwd=project_dir
        )
        logger.info(f"Branch switch completed: {checkout_result.stdout.strip()}")

        logger.info(f"Successfully switched to branch: {request.branch_name}")
        return {
            "branch": request.branch_name,
            "changes_committed": committed,
            "commit_message": request.commit_message if committed else None,
            "output": checkout_result.stdout.strip()
        }

    except Exception as e:
        logger.exception(f"Failed to switch branch: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to switch branch: {str(e)}"
        )
