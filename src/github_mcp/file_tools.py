"""Local filesystem operations tools for GithubMCP server."""

import asyncio
import fnmatch
import json
import mimetypes
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from github_mcp.config import settings
from github_mcp.utils import FileAccessError, validate_and_resolve_path


async def read_file(path: str) -> dict[str, Any]:
    """Read a local file securely within allowed paths.

    Args:
        path: Relative or absolute path to target file.
    """
    target_path = validate_and_resolve_path(path)

    if not target_path.exists():
        raise FileAccessError(f"File not found: {path}")

    if not target_path.is_file():
        raise FileAccessError(f"Path is not a regular file: {path}")

    file_size_bytes = target_path.stat().st_size
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if file_size_bytes > max_bytes:
        raise FileAccessError(
            f"File size ({file_size_bytes} bytes) exceeds MAX_FILE_SIZE_MB "
            f"({settings.MAX_FILE_SIZE_MB} MB)"
        )

    mime_type, encoding = mimetypes.guess_type(target_path)
    if mime_type is None:
        mime_type = "application/octet-stream"

    # Async read content
    def _read_content() -> tuple[str, bool]:
        try:
            with open(target_path, encoding="utf-8", errors="replace") as f:
                content = f.read(100_000)  # max 100k chars for response safety
                truncated = f.read(1) != ""
                return content, truncated
        except Exception as e:
            raise FileAccessError(f"Error reading file '{path}': {e}") from e

    content, truncated = await asyncio.to_thread(_read_content)

    return {
        "path": str(target_path),
        "size_bytes": file_size_bytes,
        "mime_type": mime_type,
        "encoding": encoding or "utf-8",
        "content": content,
        "is_truncated": truncated,
    }


async def list_directory(
    path: str,
    recursive: bool = False,
    depth_limit: int = 3,
    glob_pattern: str | None = None,
) -> dict[str, Any]:
    """List directory contents recursively or flat within allowed paths.

    Args:
        path: Relative or absolute path to target directory.
        recursive: Whether to search subdirectories recursively.
        depth_limit: Max recursion depth (default: 3).
        glob_pattern: Optional glob pattern filter (e.g. '*.py').
    """
    target_dir = validate_and_resolve_path(path)

    if not target_dir.exists():
        raise FileAccessError(f"Directory not found: {path}")

    if not target_dir.is_dir():
        raise FileAccessError(f"Path is not a directory: {path}")

    def _walk_directory() -> list[dict[str, Any]]:
        results = []

        def _traverse(current: Path, current_depth: int) -> None:
            if current_depth > depth_limit:
                return

            try:
                entries = sorted(
                    list(current.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower())
                )
            except PermissionError:
                return

            for item in entries:
                if item.name.startswith(".") and item.name not in (".env.example",):
                    # Skip hidden files/dirs like .git by default
                    continue

                rel_path = item.relative_to(target_dir)

                if glob_pattern:
                    if not fnmatch.fnmatch(item.name, glob_pattern):
                        continue

                stat = item.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat()

                item_info = {
                    "name": item.name,
                    "relative_path": str(rel_path),
                    "is_directory": item.is_dir(),
                    "size_bytes": stat.st_size if not item.is_dir() else None,
                    "modified": mtime,
                }
                results.append(item_info)

                if recursive and item.is_dir() and current_depth < depth_limit:
                    _traverse(item, current_depth + 1)

        _traverse(target_dir, 1)
        return results

    items = await asyncio.to_thread(_walk_directory)

    return {
        "directory": str(target_dir),
        "total_items": len(items),
        "items": items,
    }


async def search_local_files(
    path: str,
    pattern: str,
    case_sensitive: bool = False,
    file_type: str | None = None,
) -> list[dict[str, Any]]:
    """Search for pattern across local text files in directory.

    Args:
        path: Base directory to search.
        pattern: Pattern or string to find.
        case_sensitive: Whether match should be case sensitive (default: False).
        file_type: Optional file extension filter (e.g. 'py', 'ts').
    """
    target_dir = validate_and_resolve_path(path)

    if not target_dir.exists() or not target_dir.is_dir():
        raise FileAccessError(f"Directory not found: {path}")

    flags = 0 if case_sensitive else re.IGNORECASE

    def _sync_search() -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        ext_filter = f".{file_type.lstrip('.')}" if file_type else None

        for item in target_dir.rglob("*"):
            if len(matches) >= 100:
                break

            if item.is_dir() or item.name.startswith("."):
                continue

            if ext_filter and item.suffix != ext_filter:
                continue

            try:
                with open(item, encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, start=1):
                    if re.search(pattern, line, flags):
                        start_idx = max(0, i - 2)
                        end_idx = min(len(lines), i + 1)
                        context = [
                            f"{line_num}: {lines[line_num - 1].rstrip()}"
                            for line_num in range(start_idx + 1, end_idx + 1)
                        ]
                        matches.append(
                            {
                                "file": str(item.relative_to(target_dir)),
                                "line_number": i,
                                "line_content": line.strip(),
                                "context": context,
                            }
                        )
                        if len(matches) >= 100:
                            break
            except Exception:
                continue

        return matches

    return await asyncio.to_thread(_sync_search)


async def get_project_context(root_path: str) -> dict[str, Any]:
    """Detect project structure, stack, key dependencies, and dev commands.

    Args:
        root_path: Path to root project directory.
    """
    target_dir = validate_and_resolve_path(root_path)

    if not target_dir.exists() or not target_dir.is_dir():
        raise FileAccessError(f"Directory not found: {root_path}")

    def _sync_detect() -> dict[str, Any]:
        detected_types = []
        config_files = []
        dependencies: list[str] = []
        dev_commands: list[str] = []

        # Check Node.js
        pkg_json = target_dir / "package.json"
        if pkg_json.exists():
            detected_types.append("Node.js / JavaScript / TypeScript")
            config_files.append("package.json")
            dev_commands.extend(["npm install", "npm test", "npm run build"])
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                deps = list(data.get("dependencies", {}).keys())
                dev_deps = list(data.get("devDependencies", {}).keys())
                dependencies.extend(deps[:10] + dev_deps[:10])
            except Exception:
                pass

        # Check Python
        pyproject = target_dir / "pyproject.toml"
        requirements = target_dir / "requirements.txt"
        setup_py = target_dir / "setup.py"
        if pyproject.exists() or requirements.exists() or setup_py.exists():
            detected_types.append("Python")
            if pyproject.exists():
                config_files.append("pyproject.toml")
                dev_commands.extend(["uv sync", "pytest", "ruff check ."])
            if requirements.exists():
                config_files.append("requirements.txt")
                try:
                    lines = requirements.read_text(encoding="utf-8").splitlines()
                    dependencies.extend(
                        [
                            line.strip()
                            for line in lines
                            if line.strip() and not line.startswith("#")
                        ][:15]
                    )
                except Exception:
                    pass
            if setup_py.exists():
                config_files.append("setup.py")

        # Check Rust
        cargo = target_dir / "Cargo.toml"
        if cargo.exists():
            detected_types.append("Rust")
            config_files.append("Cargo.toml")
            dev_commands.extend(["cargo build", "cargo test", "cargo run"])

        # Check Go
        go_mod = target_dir / "go.mod"
        if go_mod.exists():
            detected_types.append("Go")
            config_files.append("go.mod")
            dev_commands.extend(["go build", "go test ./..."])

        # Check Docker
        dockerfile = target_dir / "Dockerfile"
        if dockerfile.exists():
            detected_types.append("Docker")
            config_files.append("Dockerfile")
            dev_commands.append("docker build -t app .")

        return {
            "root": str(target_dir),
            "project_types": detected_types if detected_types else ["Generic File Directory"],
            "config_files_found": config_files,
            "sample_dependencies": list(set(dependencies))[:20],
            "suggested_dev_commands": list(set(dev_commands)),
        }

    return await asyncio.to_thread(_sync_detect)
