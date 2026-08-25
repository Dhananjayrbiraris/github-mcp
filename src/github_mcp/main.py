"""Main entry point for GithubMCP server."""

import argparse
from typing import Any

from mcp.server import MCPServer

from github_mcp.analysis_tools import (
    analyze_code_quality,
    generate_change_summary,
)
from github_mcp.ci_tools import (
    check_ci_status,
)
from github_mcp.config import settings
from github_mcp.file_tools import (
    get_project_context,
    list_directory,
    read_file,
    search_local_files,
)
from github_mcp.github_tools import (
    inspect_issue,
    inspect_pr,
    recent_commits,
    search_code,
    search_repos,
    update_repo_visibility,
)
from github_mcp.utils import logger

# Initialize MCPServer instance
app = MCPServer(
    name="GithubMCP",
    description=(
        "Personal Developer Assistant MCP Server for GitHub workflow, "
        "CI/CD, local files, and code analysis."
    ),
)


# A. GitHub Tools
@app.tool(
    name="search_repos",
    description=(
        "Search GitHub repositories matching query, optional language filter, and sort order."
    ),
)
async def tool_search_repos(
    query: str = "",
    language: str | None = None,
    sort: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    return await search_repos(query=query, language=language, sort=sort, limit=limit)


@app.tool(
    name="inspect_pr",
    description=(
        "Fetch pull request details including changed files, diff stats, "
        "additions/deletions, and review comments."
    ),
)
async def tool_inspect_pr(repo: str, pr_number: int) -> dict[str, Any]:
    return await inspect_pr(repo=repo, pr_number=pr_number)


@app.tool(
    name="inspect_issue",
    description=(
        "Fetch issue details including assignees, state, labels, linked PRs, and recent comments."
    ),
)
async def tool_inspect_issue(repo: str, issue_number: int) -> dict[str, Any]:
    return await inspect_issue(repo=repo, issue_number=issue_number)


@app.tool(
    name="search_code",
    description=(
        "Search code across specified repositories matching pattern and optional "
        "file extension filter."
    ),
)
async def tool_search_code(
    repos: list[str],
    pattern: str,
    file_extension: str | None = None,
) -> list[dict[str, Any]]:
    return await search_code(repos=repos, pattern=pattern, file_extension=file_extension)


@app.tool(
    name="recent_commits",
    description=(
        "Fetch recent commits for a repository branch within lookback days with commit stats."
    ),
)
async def tool_recent_commits(
    repo: str,
    branch: str = "main",
    days: int = 7,
    limit: int = 20,
) -> list[dict[str, Any]]:
    return await recent_commits(repo=repo, branch=branch, days=days, limit=limit)


@app.tool(
    name="update_repo_visibility",
    description=(
        "Update the privacy/visibility settings of a repository to make it private or public."
    ),
)
async def tool_update_repo_visibility(repo: str, private: bool) -> dict[str, Any]:
    return await update_repo_visibility(repo=repo, private=private)


# B. CI/CD Monitoring Tools
@app.tool(
    name="check_ci_status",
    description=(
        "Check current build status (success/failure/in_progress), duration, log URL, "
        "and summary of failed steps for GitHub Actions."
    ),
)
async def tool_check_ci_status(
    repo: str,
    branch: str = "main",
    platform: str = "github_actions",
) -> dict[str, Any]:
    return await check_ci_status(repo=repo, branch=branch, platform=platform)


# C. Local Filesystem Tools
@app.tool(
    name="read_file",
    description=(
        "Read file contents securely within allowed directories with MIME type "
        "detection and size validation."
    ),
)
async def tool_read_file(path: str) -> dict[str, Any]:
    return await read_file(path=path)


@app.tool(
    name="list_directory",
    description=(
        "List directory structure, files, subdirectories, sizes, and modification dates "
        "with optional depth limit and glob filter."
    ),
)
async def tool_list_directory(
    path: str,
    recursive: bool = False,
    depth_limit: int = 3,
    glob_pattern: str | None = None,
) -> dict[str, Any]:
    return await list_directory(
        path=path,
        recursive=recursive,
        depth_limit=depth_limit,
        glob_pattern=glob_pattern,
    )


@app.tool(
    name="search_local_files",
    description=(
        "Search local directory files for text matching pattern with line numbers "
        "and surrounding context."
    ),
)
async def tool_search_local_files(
    path: str,
    pattern: str,
    case_sensitive: bool = False,
    file_type: str | None = None,
) -> list[dict[str, Any]]:
    return await search_local_files(
        path=path,
        pattern=pattern,
        case_sensitive=case_sensitive,
        file_type=file_type,
    )


@app.tool(
    name="get_project_context",
    description=(
        "Detect project type (Node, Python, Rust, Go, Docker), key config files, "
        "sample dependencies, and suggested dev commands."
    ),
)
async def tool_get_project_context(root_path: str) -> dict[str, Any]:
    return await get_project_context(root_path=root_path)


# D. Code Analysis Tools
@app.tool(
    name="generate_change_summary",
    description=(
        "Compare base and head git refs for a repository and generate a human-readable "
        "summary categorized by Features, Fixes, Breaking Changes, and Config Updates."
    ),
)
async def tool_generate_change_summary(
    repo: str,
    base_ref: str,
    head_ref: str,
) -> dict[str, Any]:
    return await generate_change_summary(repo=repo, base_ref=base_ref, head_ref=head_ref)


@app.tool(
    name="analyze_code_quality",
    description=(
        "Analyze file metrics (line counts, comment ratio, complexity estimate), "
        "TODO/FIXME comments, and potential security smells (hardcoded secrets)."
    ),
)
async def tool_analyze_code_quality(path: str) -> dict[str, Any]:
    return await analyze_code_quality(path=path)


def run_stdio() -> None:
    """Run server in stdio mode."""
    logger.info("Starting GithubMCP server in STDIO mode...")
    app.run(transport="stdio")


def run_sse(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run server in SSE mode via uvicorn/FastAPI."""
    logger.info(f"Starting GithubMCP server in SSE mode on {host}:{port}...")
    app.run(transport="sse", host=host, port=port)


def main() -> None:
    """CLI Entrypoint parsing command line arguments and environment defaults."""
    parser = argparse.ArgumentParser(description="GithubMCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=settings.TRANSPORT,
        help="Transport protocol mode (stdio or sse). Default from .env or stdio.",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host address for SSE mode.")
    parser.add_argument("--port", type=int, default=8000, help="Port number for SSE mode.")

    args = parser.parse_args()

    if args.transport == "sse":
        run_sse(host=args.host, port=args.port)
    else:
        run_stdio()


if __name__ == "__main__":
    main()
