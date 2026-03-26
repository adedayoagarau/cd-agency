"""File system tools for agent use."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Any

from runtime.tools.base import Tool, ToolResult

# Safety: prevent reading outside project directory
_BLOCKED_PATTERNS = {"*.env", "*.key", "*.pem", "*credentials*", "*secret*"}


def _is_safe_path(path: Path, root: Path) -> bool:
    """Check that path is within root and not a sensitive file."""
    try:
        resolved = path.resolve()
        root_resolved = root.resolve()
        if not str(resolved).startswith(str(root_resolved)):
            return False
    except (OSError, ValueError):
        return False

    name = path.name.lower()
    for pattern in _BLOCKED_PATTERNS:
        if fnmatch.fnmatch(name, pattern):
            return False

    return True


class ReadFile(Tool):
    """Read a file and return its contents."""

    name = "read_file"
    description = (
        "Read a file from the project directory and return its contents. "
        "Useful for reading existing UI copy, documentation, or config files."
    )
    parameters = {
        "path": {"type": "string", "description": "Relative path to the file"},
        "max_lines": {
            "type": "integer",
            "description": "Maximum lines to read (default: 200)",
            "optional": True,
        },
    }

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(".")

    def execute(self, **kwargs: Any) -> ToolResult:
        path_str = kwargs.get("path", "")
        max_lines = kwargs.get("max_lines", 200)
        if not path_str:
            return ToolResult(success=False, error="No path provided")

        path = self._root / path_str
        if not _is_safe_path(path, self._root):
            return ToolResult(success=False, error=f"Access denied: {path_str}")
        if not path.is_file():
            return ToolResult(success=False, error=f"File not found: {path_str}")

        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            content = "\n".join(lines[:max_lines])
            truncated = len(lines) > max_lines
            return ToolResult(
                success=True,
                data={
                    "path": path_str,
                    "content": content,
                    "total_lines": len(lines),
                    "truncated": truncated,
                },
            )
        except OSError as e:
            return ToolResult(success=False, error=str(e))


class WriteFile(Tool):
    """Write content to a file."""

    name = "write_file"
    description = (
        "Write content to a file in the project directory. "
        "Creates the file if it doesn't exist, overwrites if it does."
    )
    parameters = {
        "path": {"type": "string", "description": "Relative path to the file"},
        "content": {"type": "string", "description": "Content to write"},
    }

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(".")

    def execute(self, **kwargs: Any) -> ToolResult:
        path_str = kwargs.get("path", "")
        content = kwargs.get("content", "")
        if not path_str:
            return ToolResult(success=False, error="No path provided")

        path = self._root / path_str
        if not _is_safe_path(path, self._root):
            return ToolResult(success=False, error=f"Access denied: {path_str}")

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return ToolResult(
                success=True,
                data={"path": path_str, "bytes_written": len(content.encode("utf-8"))},
            )
        except OSError as e:
            return ToolResult(success=False, error=str(e))


class ListDirectory(Tool):
    """List files in a directory."""

    name = "list_directory"
    description = "List files and subdirectories in a project directory."
    parameters = {
        "path": {
            "type": "string",
            "description": "Relative path to directory (default: project root)",
            "optional": True,
        },
        "pattern": {
            "type": "string",
            "description": "Glob pattern to filter results, e.g. '*.md'",
            "optional": True,
        },
    }

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(".")

    def execute(self, **kwargs: Any) -> ToolResult:
        path_str = kwargs.get("path", ".")
        pattern = kwargs.get("pattern", "*")

        path = self._root / path_str
        if not _is_safe_path(path, self._root) and path_str != ".":
            return ToolResult(success=False, error=f"Access denied: {path_str}")
        if not path.is_dir():
            return ToolResult(success=False, error=f"Not a directory: {path_str}")

        try:
            entries = sorted(path.glob(pattern))
            files = [str(e.relative_to(self._root)) for e in entries[:100]]
            return ToolResult(
                success=True,
                data={"path": path_str, "entries": files, "count": len(files)},
            )
        except OSError as e:
            return ToolResult(success=False, error=str(e))


class SearchFiles(Tool):
    """Search for patterns in project files."""

    name = "search_files"
    description = (
        "Search for a text pattern across project files. "
        "Returns matching lines with file paths and line numbers."
    )
    parameters = {
        "pattern": {"type": "string", "description": "Text or regex pattern to search for"},
        "file_pattern": {
            "type": "string",
            "description": "Glob pattern to filter files, e.g. '**/*.ts'",
            "optional": True,
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of matches to return (default: 20)",
            "optional": True,
        },
    }

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(".")

    def execute(self, **kwargs: Any) -> ToolResult:
        pattern_str = kwargs.get("pattern", "")
        file_pattern = kwargs.get("file_pattern", "**/*")
        max_results = kwargs.get("max_results", 20)

        if not pattern_str:
            return ToolResult(success=False, error="No search pattern provided")

        try:
            regex = re.compile(pattern_str, re.IGNORECASE)
        except re.error as e:
            return ToolResult(success=False, error=f"Invalid regex: {e}")

        matches: list[dict[str, Any]] = []
        for filepath in self._root.glob(file_pattern):
            if not filepath.is_file():
                continue
            if not _is_safe_path(filepath, self._root):
                continue
            if "node_modules" in filepath.parts or ".git" in filepath.parts:
                continue

            try:
                text = filepath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            for i, line in enumerate(text.splitlines(), 1):
                if regex.search(line):
                    matches.append({
                        "file": str(filepath.relative_to(self._root)),
                        "line": i,
                        "content": line.strip()[:200],
                    })
                    if len(matches) >= max_results:
                        break
            if len(matches) >= max_results:
                break

        return ToolResult(
            success=True,
            data={"pattern": pattern_str, "matches": matches, "count": len(matches)},
        )
