"""Code analysis and quality tools for GithubMCP server."""

import re
from pathlib import Path
from typing import Any

from github import Github

from github_mcp.file_tools import read_file
from github_mcp.utils import get_github_client, run_async_github_call


async def generate_change_summary(
    repo: str,
    base_ref: str,
    head_ref: str,
    github_client: Github | None = None,
) -> dict[str, Any]:
    """Compare base_ref and head_ref for a repository and generate a categorized change summary.

    Args:
        repo: Repository name in 'owner/repo' format.
        base_ref: Base git reference or commit SHA (e.g. 'main', 'v1.0.0').
        head_ref: Head git reference or commit SHA (e.g. 'feature-branch', 'HEAD').
        github_client: Optional pre-configured PyGithub instance.
    """
    client = github_client or get_github_client()

    def _sync_compare() -> dict[str, Any]:
        gh_repo = client.get_repo(repo)
        comparison = gh_repo.compare(base_ref, head_ref)

        features = []
        fixes = []
        breaking = []
        config_docs = []
        others = []

        for commit in comparison.commits:
            msg = commit.commit.message
            first_line = msg.split("\n")[0].strip()
            item = {
                "sha": commit.sha[:7],
                "author": commit.author.login if commit.author else "unknown",
                "message": first_line,
            }

            msg_lower = msg.lower()
            if "breaking change" in msg_lower or "!:" in msg:
                breaking.append(item)
            elif (
                msg_lower.startswith("feat")
                or "add" in msg_lower
                or "feature" in msg_lower
                or "implement" in msg_lower
            ):
                features.append(item)
            elif msg_lower.startswith("fix") or "bug" in msg_lower or "resolve" in msg_lower:
                fixes.append(item)
            elif any(
                msg_lower.startswith(prefix)
                for prefix in ("chore", "ci", "docs", "style", "refactor", "test", "build")
            ):
                config_docs.append(item)
            else:
                others.append(item)

        files_changed = []
        for f in comparison.files or []:
            files_changed.append(
                {
                    "filename": f.filename,
                    "status": f.status,
                    "additions": f.additions,
                    "deletions": f.deletions,
                }
            )

        return {
            "repo": repo,
            "base_ref": base_ref,
            "head_ref": head_ref,
            "total_commits": len(list(comparison.commits)),
            "ahead_by": comparison.ahead_by,
            "behind_by": comparison.behind_by,
            "files_changed_count": len(comparison.files or []),
            "categorized_changes": {
                "breaking_changes": breaking,
                "new_features": features,
                "bug_fixes": fixes,
                "config_and_docs": config_docs,
                "other_commits": others,
            },
            "changed_files_summary": files_changed[:20],
        }

    return await run_async_github_call(_sync_compare)


async def analyze_code_quality(path: str) -> dict[str, Any]:
    """Analyze local file code metrics, TODOs/FIXMEs, estimated complexity, and security smells.

    Args:
        path: Relative or absolute path to target file.
    """
    file_info = await read_file(path)
    content = file_info["content"]
    file_path = Path(file_info["path"])

    lines = content.splitlines()
    total_lines = len(lines)
    blank_lines = 0
    comment_lines = 0
    todo_comments = []
    security_smells = []
    complexity_keywords_count = 0
    max_nesting = 0

    # Common secret patterns
    secret_patterns = [
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token pattern detected"),
        (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key pattern detected"),
        (r"-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----", "Private key string detected"),
        (
            r"(?i)(api[_-]?key|secret|password|passwd|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}['\"]",
            "Possible hardcoded API key or credential",
        ),
    ]

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
            continue

        # Check comment lines
        if (
            stripped.startswith("#")
            or stripped.startswith("//")
            or stripped.startswith("/*")
            or stripped.startswith("*")
        ):
            comment_lines += 1

        # Check TODO / FIXME
        if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.IGNORECASE):
            todo_comments.append(
                {
                    "line_number": idx,
                    "content": stripped,
                }
            )

        # Estimate complexity based on decision structures
        control_matches = len(
            re.findall(r"\b(if|elif|else|for|while|try|except|case|catch|switch)\b", line)
        )
        complexity_keywords_count += control_matches

        # Estimate nesting depth via indentation spaces
        indentation = len(line) - len(line.lstrip(" "))
        nesting = indentation // 4
        if nesting > max_nesting:
            max_nesting = nesting

        # Security smells detection
        for pattern, desc in secret_patterns:
            if re.search(pattern, line):
                security_smells.append(
                    {
                        "line_number": idx,
                        "description": desc,
                        "snippet": stripped[:60],
                    }
                )

    code_lines = total_lines - blank_lines - comment_lines

    return {
        "file": str(file_path),
        "extension": file_path.suffix,
        "metrics": {
            "total_lines": total_lines,
            "code_lines": max(0, code_lines),
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
            "cyclomatic_complexity_estimate": 1 + complexity_keywords_count,
            "max_indentation_depth": max_nesting,
        },
        "todo_fixme_count": len(todo_comments),
        "todo_fixme_list": todo_comments,
        "security_smells_count": len(security_smells),
        "security_smells": security_smells,
    }
