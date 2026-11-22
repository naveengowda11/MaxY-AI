"""Safe local tools. No model-generated shell or arbitrary code execution."""
import platform
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar


class ToolError(RuntimeError):
    """A registered tool rejected an action or could not complete it."""


class ToolRegistry:
    READABLE_EXTENSIONS: ClassVar[set[str]] = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".log", ".py"}
    MAX_READ_BYTES = 1024 * 1024

    def __init__(self, allowed_roots: list[Path],
                 app_launcher: Callable[[str], None] | None = None) -> None:
        self.allowed_roots = [Path(root).expanduser().resolve() for root in allowed_roots]
        self.app_launcher = app_launcher or self._launch_windows_app
        self._tools = {
            "launch_app": self.launch_app,
            "list_files": self.list_files,
            "search_files": self.search_files,
            "read_text_file": self.read_text_file,
        }

    def descriptions(self) -> list[dict[str, str]]:
        return [
            {"name": "launch_app", "description": "Launch a fixed allow-listed Windows app."},
            {"name": "list_files", "description": "List names inside MAXY workspace."},
            {"name": "search_files", "description": "Search names inside MAXY workspace."},
            {"name": "read_text_file", "description": "Read a small text file in MAXY workspace."},
        ]

    def get(self, name: str):
        if name not in self._tools:
            raise ToolError("That tool is not registered.")
        return self._tools[name]

    def _root(self) -> Path:
        if not self.allowed_roots:
            raise ToolError("No MAXY workspace folder is configured.")
        root = self.allowed_roots[0]
        root.mkdir(parents=True, exist_ok=True)
        return root.resolve()

    def _safe_path(self, relative_path: Any) -> Path:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ToolError("A relative workspace path is required.")
        root = self._root()
        candidate = (root / relative_path).resolve()
        if candidate == root or root not in candidate.parents:
            raise ToolError("The requested path is outside the MAXY workspace.")
        return candidate

    def preview(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.get(name)
        if name == "launch_app":
            app = arguments.get("app")
            if app not in {"notepad", "calculator", "paint", "explorer"}:
                raise ToolError("Allowed apps: notepad, calculator, paint, explorer.")
            return {"action": "Launch application", "target": app}
        if name == "list_files":
            directory = arguments.get("directory", ".")
            path = self._root() if directory == "." else self._safe_path(directory)
            if not path.is_dir():
                raise ToolError("That workspace location is not a directory.")
            return {"action": "List files", "directory": str(path.relative_to(self._root()))}
        if name == "search_files":
            query = arguments.get("query")
            if not isinstance(query, str) or not query.strip() or len(query) > 120:
                raise ToolError("Enter a file-name search (1–120 characters).")
            return {"action": "Search file names", "query": query}
        if name == "read_text_file":
            path = self._safe_path(arguments.get("path", ""))
            if not path.is_file() or path.is_symlink():
                raise ToolError("That workspace file is not a regular file.")
            if path.suffix.lower() not in self.READABLE_EXTENSIONS:
                raise ToolError("This file type is not enabled for text reading.")
            if path.stat().st_size > self.MAX_READ_BYTES:
                raise ToolError("The file is over the 1 MB reading limit.")
            return {"action": "Read text file", "path": str(path.relative_to(self._root()))}
        raise ToolError("No preview is available.")

    def launch_app(self, arguments: dict[str, Any]) -> dict[str, Any]:
        app = arguments.get("app")
        if app not in {"notepad", "calculator", "paint", "explorer"}:
            raise ToolError("Allowed apps: notepad, calculator, paint, explorer.")
        self.app_launcher(app)
        return {"message": f"Launch request sent for {app}.", "app": app}

    @staticmethod
    def _launch_windows_app(app: str) -> None:
        if platform.system() != "Windows":
            raise ToolError("Application launching is supported on Windows only.")
        commands = {"notepad": ["notepad.exe"], "calculator": ["calc.exe"],
                    "paint": ["mspaint.exe"], "explorer": ["explorer.exe"]}
        try:
            subprocess.Popen(commands[app], shell=False)
        except OSError as exc:
            raise ToolError(f"Windows could not start {app}.") from exc

    def list_files(self, arguments: dict[str, Any]) -> dict[str, Any]:
        relative = arguments.get("directory", ".")
        directory = self._root() if relative == "." else self._safe_path(relative)
        if not directory.is_dir():
            raise ToolError("That workspace location is not a directory.")
        names = sorted(p.name for p in directory.iterdir() if not p.is_symlink())
        return {"directory": str(directory.relative_to(self._root())), "files": names[:200]}

    def search_files(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip() or len(query) > 120:
            raise ToolError("Enter a file-name search (1–120 characters).")
        results = [str(p.relative_to(self._root())) for p in self._root().rglob("*")
                   if p.is_file() and not p.is_symlink()
                   and query.casefold() in p.name.casefold()]
        return {"query": query, "matches": results[:100]}

    def read_text_file(self, arguments: dict[str, Any]) -> dict[str, Any]:
        path = self._safe_path(arguments.get("path", ""))
        if not path.is_file() or path.is_symlink():
            raise ToolError("That workspace file is not a regular file.")
        if path.suffix.lower() not in self.READABLE_EXTENSIONS:
            raise ToolError("This file type is not enabled for text reading.")
        if path.stat().st_size > self.MAX_READ_BYTES:
            raise ToolError("The file is over the 1 MB reading limit.")
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            raise ToolError("Could not read this file as UTF-8 text.") from exc
        return {"path": str(path.relative_to(self._root())), "content": content}
