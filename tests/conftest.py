"""Pytest configuration, fixtures, and mocks for GithubMCP tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from github_mcp.config import settings


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory and add it to ALLOWED_PATHS settings."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp).resolve()
        original_paths = settings.ALLOWED_PATHS
        settings.ALLOWED_PATHS = [str(tmp_path)]
        yield tmp_path
        settings.ALLOWED_PATHS = original_paths


@pytest.fixture
def mock_github() -> MagicMock:
    """Mock PyGithub instance for testing GitHub tools."""
    mock_gh = MagicMock()
    return mock_gh
