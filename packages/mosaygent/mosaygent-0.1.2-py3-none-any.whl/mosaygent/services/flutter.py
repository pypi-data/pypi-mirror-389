import asyncio
import subprocess
import threading
from collections import deque
from pathlib import Path
from typing import Optional

import httpx

from mosaygent.logger import get_logger

logger = get_logger(__name__)


class FlutterService:
    """Manages the Flutter development server process with hot reload support."""

    def __init__(self, app_dir: Path, web_port: int = 36413):
        self.app_dir = app_dir
        self.web_port = web_port
        self.process: Optional[subprocess.Popen] = None
        self.debounce_timer: Optional[threading.Timer] = None
        self.error_buffer: deque = deque(maxlen=100)
        self.error_thread: Optional[threading.Thread] = None
        self._stop_error_thread = False

    def _read_errors(self):
        """Background thread to capture stderr output."""
        logger.debug("Starting error capture thread")
        try:
            while not self._stop_error_thread and self.process:
                if not self.process.stderr:
                    break

                line = self.process.stderr.readline()
                if not line:
                    if self.process.poll() is not None:
                        break
                    continue

                decoded_line = line.decode('utf-8', errors='replace').rstrip()
                if decoded_line:
                    self.error_buffer.append(decoded_line)
                    logger.warning(f"Flutter stderr: {decoded_line}")
        except Exception as e:
            logger.exception(f"Error in error capture thread: {e}")
        finally:
            logger.debug("Error capture thread stopped")

    def start(self) -> dict:
        """Start the Flutter development server."""
        if self.process and self.process.poll() is None:
            logger.info("Flutter is already running")
            return {"message": "Flutter is already running", "pid": self.process.pid}

        if not self.app_dir.exists():
            logger.error(f"App directory not found: {self.app_dir}")
            raise FileNotFoundError(f"App directory not found: {self.app_dir}")

        self.error_buffer.clear()
        self._stop_error_thread = False

        logger.info(f"Starting Flutter dev server on port {self.web_port}")
        try:
            self.process = subprocess.Popen(
                [
                    "flutter", "run", "-d", "web-server",
                    f"--web-port={self.web_port}",
                    "--web-browser-flag=--window-size=375,667"
                ],
                cwd=str(self.app_dir),
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.info(f"Flutter process started with PID {self.process.pid} with iPhone 7 window size (375x667)")

            self.error_thread = threading.Thread(target=self._read_errors, daemon=True)
            self.error_thread.start()
            logger.info("Error capture enabled - use /flutter/errors to check for issues")

            return {"message": "Flutter process started", "pid": self.process.pid}
        except Exception as e:
            logger.exception(f"Failed to start Flutter: {e}")
            raise

    def stop(self) -> dict:
        """Stop the Flutter development server."""
        if not self.process or self.process.poll() is not None:
            logger.info("Flutter is not running")
            return {"message": "Flutter is not running"}

        logger.info("Stopping Flutter process")
        self._stop_error_thread = True

        try:
            self.process.terminate()
            self.process.wait(timeout=5)
            logger.info("Flutter process stopped gracefully")
        except subprocess.TimeoutExpired:
            logger.warning("Flutter process did not stop gracefully, forcing kill")
            self.process.kill()
            self.process.wait()
        except Exception as e:
            logger.exception(f"Failed to stop Flutter: {e}")
            raise

        if self.error_thread and self.error_thread.is_alive():
            self.error_thread.join(timeout=2)

        return {"message": "Flutter process stopped"}

    def get_status(self) -> dict:
        """Get the current status of the Flutter development server."""
        if not self.process:
            return {"running": False, "message": "Not started"}

        poll_result = self.process.poll()
        if poll_result is None:
            return {
                "running": True,
                "pid": self.process.pid,
                "port": self.web_port
            }
        else:
            return {
                "running": False,
                "exit_code": poll_result
            }

    def trigger_hot_reload(self):
        """Trigger a hot reload on the Flutter process with debouncing."""
        if not self.process or self.process.poll() is not None:
            logger.warning("Cannot hot reload: Flutter is not running")
            return

        if self.debounce_timer:
            self.debounce_timer.cancel()

        logger.debug("Debouncing hot reload (500ms)")
        self.debounce_timer = threading.Timer(0.5, self._do_hot_reload)
        self.debounce_timer.start()

    def _do_hot_reload(self):
        """Perform the actual hot reload."""
        try:
            if self.process and self.process.poll() is None:
                logger.info("Triggering hot reload")
                self.process.stdin.write(b'r\n')
                self.process.stdin.flush()
        except Exception as e:
            logger.exception(f"Failed to trigger hot reload: {e}")

    def trigger_hot_restart(self):
        """Trigger a hot restart on the Flutter process."""
        if not self.process or self.process.poll() is not None:
            logger.warning("Cannot hot restart: Flutter is not running")
            return

        logger.info("Triggering hot restart")
        try:
            self.process.stdin.write(b'R\n')
            self.process.stdin.flush()
        except Exception as e:
            logger.exception(f"Failed to trigger hot restart: {e}")

    async def wait_for_ready(self, timeout: int = 30) -> bool:
        """Wait for the Flutter web server to become ready."""
        logger.info(f"Waiting for Flutter to be ready (timeout: {timeout}s)")
        logger.info("Check your console for Flutter output")

        async with httpx.AsyncClient() as client:
            for i in range(timeout):
                # Check if process is still running
                if self.process and self.process.poll() is not None:
                    logger.error(f"Flutter process died with exit code {self.process.poll()}")
                    logger.error("Check console output above for Flutter error details")
                    return False

                try:
                    response = await client.get(
                        f"http://localhost:{self.web_port}",
                        timeout=1.0
                    )
                    if response.status_code in [200, 404]:
                        logger.info("Flutter web server is ready")
                        return True
                except (httpx.RequestError, httpx.TimeoutException):
                    logger.debug(f"Flutter not ready yet (attempt {i + 1}/{timeout})")
                await asyncio.sleep(1)

        logger.warning("Flutter did not become ready in time")
        logger.warning("Check console output for Flutter status")
        return False

    def get_errors(self) -> list:
        """Get all captured error messages."""
        return list(self.error_buffer)
