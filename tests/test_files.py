"""Unit tests for local filesystem operations and code quality tools."""

from pathlib import Path

import pytest

from github_mcp.analysis_tools import analyze_code_quality
from github_mcp.file_tools import (
    get_project_context,
    list_directory,
    read_file,
    search_local_files,
)
from github_mcp.utils import FileAccessError, SecurityError


@pytest.mark.asyncio
async def test_read_file_success(temp_dir: Path) -> None:
    test_file = temp_dir / "sample.txt"
    test_file.write_text("Hello MCP World!", encoding="utf-8")

    result = await read_file(str(test_file))
    assert result["size_bytes"] == 16
    assert result["content"] == "Hello MCP World!"
    assert result["is_truncated"] is False


@pytest.mark.asyncio
async def test_read_file_not_found(temp_dir: Path) -> None:
    missing_file = temp_dir / "non_existent.txt"
    with pytest.raises(FileAccessError, match="File not found"):
        await read_file(str(missing_file))


@pytest.mark.asyncio
async def test_read_file_security_violation() -> None:
    import sys

    # Attempt path traversal outside allowed temp dir (cross-platform)
    forbidden_path = (
        "C:/Windows/System32/drivers/etc/hosts" if sys.platform == "win32" else "/etc/shadow"
    )
    with pytest.raises(SecurityError, match="Access denied"):
        await read_file(forbidden_path)


@pytest.mark.asyncio
async def test_list_directory(temp_dir: Path) -> None:
    (temp_dir / "sub_dir").mkdir()
    (temp_dir / "file1.py").write_text("print('test1')", encoding="utf-8")
    (temp_dir / "file2.txt").write_text("test2", encoding="utf-8")

    result = await list_directory(str(temp_dir), glob_pattern="*.py")
    assert result["total_items"] == 1
    assert result["items"][0]["name"] == "file1.py"


@pytest.mark.asyncio
async def test_search_local_files(temp_dir: Path) -> None:
    (temp_dir / "code.py").write_text(
        "def my_func():\n    # TODO: fix this bug\n    return 42\n", encoding="utf-8"
    )

    matches = await search_local_files(str(temp_dir), pattern="TODO")
    assert len(matches) == 1
    assert matches[0]["file"] == "code.py"
    assert matches[0]["line_number"] == 2
    assert "TODO: fix this bug" in matches[0]["line_content"]


@pytest.mark.asyncio
async def test_get_project_context(temp_dir: Path) -> None:
    (temp_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
    (temp_dir / "requirements.txt").write_text("pytest>=8.0.0\n", encoding="utf-8")

    context = await get_project_context(str(temp_dir))
    assert "Python" in context["project_types"]
    assert "pyproject.toml" in context["config_files_found"]
    assert "pytest>=8.0.0" in context["sample_dependencies"]
    assert any("pytest" in cmd for cmd in context["suggested_dev_commands"])


@pytest.mark.asyncio
async def test_analyze_code_quality(temp_dir: Path) -> None:
    code_file = temp_dir / "app.py"
    code_content = (
        "# Sample script\n"
        "def run():\n"
        "    # TODO: clean secret\n"
        "    api_key = 'ghp_1234567890abcdef1234567890abcdef1234'\n"
        "    if True:\n"
        "        return True\n"
    )
    code_file.write_text(code_content, encoding="utf-8")

    result = await analyze_code_quality(str(code_file))
    assert result["metrics"]["total_lines"] == 6
    assert result["todo_fixme_count"] == 1
    assert result["security_smells_count"] >= 1
    assert "GitHub Personal Access Token" in result["security_smells"][0]["description"]
