"""Small, conservative command parser for safe local tools.

Only narrowly recognized commands are converted to proposals. Unknown or ambiguous
requests remain ordinary assistant conversations.
"""
import re
from typing import Any


class ToolIntentParser:
    """Map a few explicit phrases to registered tool names and validated arguments."""

    _APP_NAMES = {
        "calculator": "calculator",
        "calc": "calculator",
        "notepad": "notepad",
        "paint": "paint",
        "file explorer": "explorer",
        "explorer": "explorer",
    }

    def parse(self, message: str) -> tuple[str, dict[str, Any]] | None:
        text = " ".join(message.strip().lower().split())
        text = re.sub(r"^(?:maxy[, ]+)?(?:please )?", "", text)
        text = text.rstrip(".!?")

        app_match = re.fullmatch(
            r"(?:open|launch|start) (calculator|calc|notepad|paint|file explorer|explorer)(?: app| application)?",
            text,
        )
        if app_match:
            return "launch_app", {"app": self._APP_NAMES[app_match.group(1)]}

        if re.fullmatch(r"(?:list|show) (?:my )?(?:workspace )?files", text):
            return "list_files", {"directory": "."}

        folder_match = re.fullmatch(
            r"(?:list|show) files (?:in|inside) (?:my )?(?:workspace/)?([a-z0-9_./-]+)",
            text,
        )
        if folder_match:
            return "list_files", {"directory": folder_match.group(1)}

        search_match = re.fullmatch(
            r"(?:find|search) (?:my )?(?:file|files|document|documents|project|folder)"
            r"(?: named| called| containing| for| about)? (.+)",
            text,
        )
        if search_match:
            query = search_match.group(1).strip().strip('"').strip("'")
            if query and len(query) <= 120:
                return "search_files", {"query": query}

        read_match = re.fullmatch(
            r"(?:read|show contents of|open) (?:the )?file (.+)",
            text,
        )
        if read_match:
            path = read_match.group(1).strip().strip('"').strip("'")
            if path and len(path) <= 240:
                return "read_text_file", {"path": path}

        return None
