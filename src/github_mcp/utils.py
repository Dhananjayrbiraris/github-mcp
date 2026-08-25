"""Utility functions and error handlers for GithubMCP."""

import asyncio
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from github import Github, RateLimitExceededException
from github.GithubException import GithubException

from github_mcp.config import settings

logger = logging.getLogger("github_mcp")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class SecurityError(Exception):
    """Raised when a security policy or path restriction is violated."""


class GitHubAPIError(Exception):
    """Raised when a GitHub API operation fails."""


class FileAccessError(Exception):
    """Raised when a file operation fails."""


def is_path_allowed(target: str | Path, allowed_paths: list[Path] | None = None) -> bool:
    """Check if target path is safely within one of the allowed base directories."""
    if allowed_paths is None:
        allowed_paths = settings.get_allowed_paths()

    try:
        candidate = Path(target).expanduser().resolve()
    except Exception:
        return False

    for base in allowed_paths:
        try:
            resolved_base = base.expanduser().resolve()
            # If candidate is equal to or relative to base
            if candidate == resolved_base or resolved_base in candidate.parents:
                return True
        except Exception:
            continue
    return False


def validate_and_resolve_path(target: str | Path) -> Path:
    """Validate path safety and return resolved Path object."""
    candidate = Path(target).expanduser().resolve()
    allowed = settings.get_allowed_paths()
    if not is_path_allowed(candidate, allowed):
        raise SecurityError(
            f"Access denied: Path '{target}' resolves to '{candidate}', "
            f"which is outside allowed paths."
        )
    return candidate


T = TypeVar("T")


async def run_async_github_call(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a synchronous PyGithub call in async executor with exponential backoff."""
    max_retries = 3
    delay = 1.0

    def _wrapper() -> T:
        nonlocal delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except RateLimitExceededException as e:
                if attempt == max_retries - 1:
                    raise GitHubAPIError(f"GitHub Rate Limit Exceeded: {e}") from e
                logger.warning(
                    f"Rate limit exceeded. Retrying in {delay}s... "
                    f"(Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                delay *= 2.0
            except GithubException as e:
                raise GitHubAPIError(f"GitHub API Error [{e.status}]: {e.data}") from e
            except Exception as e:
                raise GitHubAPIError(f"Unexpected GitHub API Error: {e}") from e
        raise GitHubAPIError("Failed after retries")

    return await asyncio.to_thread(_wrapper)


def get_github_client(token: str | None = None) -> Github:
    """Return an authenticated or unauthenticated PyGithub instance."""
    tok = token or settings.GITHUB_TOKEN
    if tok:
        return Github(auth=None, login_or_token=tok)
    return Github()
