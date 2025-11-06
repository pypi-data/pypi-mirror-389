"""
Command execution module for running CLI tools and subprocesses.

Provides standardized command execution with proper error handling,
timeout management, and structured results using Pydantic models.
"""

import subprocess
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field
from mosaygent.logger import get_logger

logger = get_logger(__name__)


class CommandResult(BaseModel):
    """Result of a subprocess command execution."""

    model_config = {"frozen": True}

    success: bool = Field(description="Whether the command executed successfully")
    stdout: str = Field(description="Standard output from the command")
    stderr: str = Field(default="", description="Standard error from the command")
    return_code: int = Field(description="Exit code from the command")
    command: List[str] = Field(description="The command that was executed")  # Make immutable

    @property
    def output(self) -> str:
        """Get cleaned stdout."""
        return self.stdout.strip()

    def to_response(self) -> dict:
        """
        Convert to a standardized API response format.

        Returns:
            Dictionary with status, output, and optional error info
        """
        response = {
            "status": "success" if self.success else "error",
            "output": self.output,
        }

        if self.stderr:
            response["stderr"] = self.stderr.strip()

        if not self.success:
            response["return_code"] = self.return_code

        return response


class CommandConfig(BaseModel):
    """Configuration for command execution."""

    command: List[str] = Field(min_length=1, description="Command and arguments to execute")
    timeout: int = Field(default=30, gt=0, le=600, description="Timeout in seconds (max 5 min)")
    cwd: Optional[str] = Field(default=None, description="Working directory for command")
    raise_on_error: bool = Field(default=True, description="Raise HTTPException on command failure")


def run_command_streaming(
    command: List[str],
    timeout: int = 30,
    cwd: Optional[str] = None,
) -> CommandResult:
    """
    Run command and stream output to logs in real-time.

    Args:
        command: List of command arguments
        timeout: Maximum execution time in seconds
        cwd: Working directory for the command

    Returns:
        CommandResult with execution details

    Raises:
        subprocess.TimeoutExpired: If command times out
        FileNotFoundError: If command not found
    """
    config = CommandConfig(
        command=command,
        timeout=timeout,
        cwd=cwd,
        raise_on_error=True,
    )

    try:
        process = subprocess.Popen(
            config.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=config.cwd,
        )

        stdout_lines = []
        stderr_lines = []

        for line in process.stdout:
            line_stripped = line.rstrip()
            logger.info(f"[stdout] {line_stripped}")
            stdout_lines.append(line)

        process.wait(timeout=config.timeout)

        stderr = process.stderr.read()
        if stderr:
            logger.error(f"[stderr] {stderr}")
            stderr_lines.append(stderr)

        result = CommandResult(
            success=process.returncode == 0,
            stdout=''.join(stdout_lines),
            stderr=''.join(stderr_lines),
            return_code=process.returncode,
            command=config.command,
        )

        if result.success:
            logger.info(f"Command completed successfully: {' '.join(config.command)}")
        else:
            logger.error(f"Command failed with code {result.return_code}: {' '.join(config.command)}")

        return result

    except FileNotFoundError:
        logger.error(f"Command not found: {config.command[0]}")
        raise

    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {config.timeout} seconds: {' '.join(config.command)}")
        process.kill()
        raise


async def run_command(
    command: List[str],
    timeout: int = 30,
    cwd: Optional[str] = None,
    raise_on_error: bool = True,
) -> CommandResult:
    """
    Execute a subprocess command with standardized error handling.

    Args:
        command: List of command arguments (e.g., ['flutter', '--version'])
        timeout: Maximum execution time in seconds (default: 30, max: 300)
        cwd: Working directory for the command
        raise_on_error: Whether to raise HTTPException on errors

    Returns:
        CommandResult with execution details

    Raises:
        HTTPException: If raise_on_error is True and command fails
            - 404: Command not found in PATH
            - 408: Command timed out
            - 500: Command failed or other error

    Examples:
        >>> result = await run_command(['git', 'status'])
        >>> result = await run_command(['npm', 'install'], timeout=120)
        >>> result = await run_command(['ls'], cwd='/tmp', raise_on_error=False)
    """
    # Validate config
    config = CommandConfig(
        command=command,
        timeout=timeout,
        cwd=cwd,
        raise_on_error=raise_on_error,
    )

    try:
        result = subprocess.run(
            config.command,
            capture_output=True,
            text=True,
            timeout=config.timeout,
            cwd=config.cwd,
        )

        command_result = CommandResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
            command=config.command,
        )

        if config.raise_on_error and not command_result.success:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"Command '{' '.join(config.command)}' failed",
                    "stderr": result.stderr.strip(),
                    "return_code": result.returncode,
                },
            )

        return command_result

    except FileNotFoundError:
        if config.raise_on_error:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Command '{config.command[0]}' not found",
                    "message": "Is it installed and in PATH?",
                },
            )
        return CommandResult(
            success=False,
            stdout="",
            stderr=f"Command '{config.command[0]}' not found",
            return_code=-1,
            command=config.command,
        )

    except subprocess.TimeoutExpired:
        if config.raise_on_error:
            raise HTTPException(
                status_code=408,
                detail={
                    "error": "Command timed out",
                    "command": ' '.join(config.command),
                    "timeout_seconds": config.timeout,
                },
            )
        return CommandResult(
            success=False,
            stdout="",
            stderr=f"Timeout after {config.timeout} seconds",
            return_code=-1,
            command=config.command,
        )

    except Exception as e:
        if config.raise_on_error:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Unexpected error executing command",
                    "command": ' '.join(config.command),
                    "message": str(e),
                },
            )
        return CommandResult(
            success=False,
            stdout="",
            stderr=str(e),
            return_code=-1,
            command=config.command,
        )
