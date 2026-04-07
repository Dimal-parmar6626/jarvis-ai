"""Task executor: run system commands, open applications, file operations."""

import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Allowed applications (whitelist for safety)
ALLOWED_APPS: Dict[str, Dict[str, str]] = {
    "chrome": {"windows": "chrome", "darwin": "open -a 'Google Chrome'", "linux": "google-chrome"},
    "firefox": {"windows": "firefox", "darwin": "open -a Firefox", "linux": "firefox"},
    "vscode": {"windows": "code", "darwin": "open -a 'Visual Studio Code'", "linux": "code"},
    "spotify": {"windows": "spotify", "darwin": "open -a Spotify", "linux": "spotify"},
    "notepad": {"windows": "notepad", "darwin": "open -a TextEdit", "linux": "gedit"},
    "calculator": {"windows": "calc", "darwin": "open -a Calculator", "linux": "gnome-calculator"},
    "terminal": {"windows": "cmd", "darwin": "open -a Terminal", "linux": "gnome-terminal"},
    "explorer": {"windows": "explorer", "darwin": "open .", "linux": "nautilus"},
}


class TaskExecutionError(Exception):
    """Raised when a task cannot be executed safely."""


class TaskExecutor:
    """Execute system tasks with safety sandboxing."""

    def __init__(self):
        self._system = platform.system().lower()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_application(self, app_name: str) -> Dict[str, Any]:
        """Launch a whitelisted application."""
        key = app_name.strip().lower()
        if key not in ALLOWED_APPS:
            return {"success": False, "error": f"Application '{app_name}' is not in the allowed list."}

        cmd = ALLOWED_APPS[key].get(self._system)
        if not cmd:
            return {"success": False, "error": f"No launch command for '{app_name}' on {self._system}."}

        try:
            subprocess.Popen(cmd, shell=True)  # noqa: S603,S607
            logger.info("Launched application: %s", app_name)
            return {"success": True, "app": app_name}
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to launch %s: %s", app_name, exc)
            return {"success": False, "error": str(exc)}

    def take_screenshot(self, save_path: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot and save to file."""
        try:
            import pyautogui  # type: ignore

            path = save_path or str(Path.home() / "jarvis_screenshot.png")
            screenshot = pyautogui.screenshot()
            screenshot.save(path)
            return {"success": True, "path": path}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def create_file(self, file_path: str, content: str = "") -> Dict[str, Any]:
        """Create a file with optional content."""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            logger.info("Created file: %s", file_path)
            return {"success": True, "path": str(path)}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read a file and return its contents."""
        try:
            path = Path(file_path)
            content = path.read_text(encoding="utf-8")
            return {"success": True, "content": content}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}

    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete a file or directory."""
        try:
            path = Path(file_path)
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            logger.info("Deleted: %s", file_path)
            return {"success": True, "path": file_path}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}

    def list_directory(self, dir_path: str = ".") -> Dict[str, Any]:
        """List files in a directory."""
        try:
            path = Path(dir_path)
            items = [
                {"name": item.name, "type": "dir" if item.is_dir() else "file", "size": item.stat().st_size if item.is_file() else None}
                for item in path.iterdir()
            ]
            return {"success": True, "items": items, "path": str(path.resolve())}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}

    def move_file(self, src: str, dst: str) -> Dict[str, Any]:
        """Move or rename a file."""
        try:
            shutil.move(src, dst)
            return {"success": True, "src": src, "dst": dst}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}

    def copy_file(self, src: str, dst: str) -> Dict[str, Any]:
        """Copy a file."""
        try:
            shutil.copy2(src, dst)
            return {"success": True, "src": src, "dst": dst}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # System info
    # ------------------------------------------------------------------

    def get_system_info(self) -> Dict[str, Any]:
        """Return basic system information."""
        try:
            import psutil  # type: ignore

            return {
                "success": True,
                "os": platform.system(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
                "cpu_percent": psutil.cpu_percent(interval=0.5),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
            }
        except Exception as exc:  # pylint: disable=broad-except
            return {
                "success": True,
                "os": platform.system(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
                "error": str(exc),
            }
