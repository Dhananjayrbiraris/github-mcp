"""GitHub integration tools for GithubMCP server."""

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from github import Github

from github_mcp.utils import get_github_client, run_async_github_call


async def search_repos(
    query: str = "",
    language: str | None = None,
    sort: str | None = None,
    limit: int = 10,
    github_client: Github | None = None,
) -> list[dict[str, Any]]:
    """Search repositories across public GitHub and authenticated user/org repositories
    (including private repositories).

    Args:
        query: Free text query or search terms (leave empty to list user repositories).
        language: Optional language filter (e.g. 'python', 'typescript').
        sort: Sort criteria ('stars', 'forks', 'updated'). Defaults to 'updated'.
        limit: Max number of results to return (default: 10).
        github_client: Optional pre-configured PyGithub instance.
    """
    client = github_client or get_github_client()
    search_term = query or ""
    if language:
        search_term += f" language:{language}"

    sort_param = sort if sort in ("stars", "forks", "updated") else "updated"

    def _sync_search() -> list[dict[str, Any]]:
        repos_dict: dict[str, dict[str, Any]] = {}

        # 1. Fetch authenticated user's repositories (includes private & public)
        try:
            user = client.get_user()
            repo: Any
            for repo in user.get_repos():
                if query:
                    q_lower = query.lower()
                    if (
                        q_lower not in repo.name.lower()
                        and q_lower not in (repo.description or "").lower()
                    ):
                        continue
                if language and repo.language and repo.language.lower() != language.lower():
                    continue

                repos_dict[repo.full_name] = {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "private": repo.private,
                    "description": repo.description,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "language": repo.language,
                    "url": repo.html_url,
                    "last_pushed": repo.pushed_at.isoformat() if repo.pushed_at else None,
                }
        except Exception:
            pass

        # 2. Global search API if search_term provided and limit not reached
        if search_term and len(repos_dict) < limit:
            try:
                paginated_results = client.search_repositories(
                    query=search_term, sort=sort_param
                )
                r: Any
                for r in paginated_results[:limit]:
                    if r.full_name not in repos_dict:
                        repos_dict[r.full_name] = {
                            "name": r.name,
                            "full_name": r.full_name,
                            "private": r.private,
                            "description": r.description,
                            "stars": r.stargazers_count,
                            "forks": r.forks_count,
                            "language": r.language,
                            "url": r.html_url,
                            "last_pushed": r.pushed_at.isoformat() if r.pushed_at else None,
                        }
            except Exception:
                pass

        results = list(repos_dict.values())
        return results[:limit]

    return await run_async_github_call(_sync_search)


async def inspect_pr(
    repo: str,
    pr_number: int,
    github_client: Github | None = None,
) -> dict[str, Any]:
    """Fetch pull request details including changed files, diff stats, and review comments.

    Args:
        repo: Repository name in 'owner/repo' format.
        pr_number: Pull request number.
        github_client: Optional pre-configured PyGithub instance.
    """
    client = github_client or get_github_client()

    def _sync_inspect_pr() -> dict[str, Any]:
        gh_repo = client.get_repo(repo)
        pr = gh_repo.get_pull(pr_number)

        changed_files = []
        for f in pr.get_files():
            changed_files.append(
                {
                    "filename": f.filename,
                    "status": f.status,
                    "additions": f.additions,
                    "deletions": f.deletions,
                    "changes": f.changes,
                    "patch_snippet": f.patch[:500] if f.patch else None,
                }
            )

        review_comments = []
        for c in pr.get_review_comments():
            review_comments.append(
                {
                    "id": c.id,
                    "user": c.user.login if c.user else "unknown",
                    "body": c.body,
                    "path": c.path,
                    "line": c.line,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
            )

        return {
            "title": pr.title,
            "number": pr.number,
            "author": pr.user.login if pr.user else "unknown",
            "state": pr.state,
            "merged": pr.merged,
            "mergeable": pr.mergeable,
            "body": pr.body,
            "labels": [label.name for label in pr.labels],
            "created_at": pr.created_at.isoformat() if pr.created_at else None,
            "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
            "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files_count": pr.changed_files,
            "changed_files": changed_files,
            "review_comments": review_comments,
        }

    return await run_async_github_call(_sync_inspect_pr)


async def inspect_issue(
    repo: str,
    issue_number: int,
    github_client: Github | None = None,
) -> dict[str, Any]:
    """Fetch issue details including assignees, labels, linked PRs, and comments.

    Args:
        repo: Repository name in 'owner/repo' format.
        issue_number: Issue number.
        github_client: Optional pre-configured PyGithub instance.
    """
    client = github_client or get_github_client()

    def _sync_inspect_issue() -> dict[str, Any]:
        gh_repo = client.get_repo(repo)
        issue = gh_repo.get_issue(issue_number)

        comments = []
        linked_prs = []

        # Find linked PR mentions in body and comments
        text_to_search = (issue.body or "") + " "
        for c in issue.get_comments():
            text_to_search += (c.body or "") + " "
            comments.append(
                {
                    "user": c.user.login if c.user else "unknown",
                    "body": c.body,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
            )

        # Regex search for PR references
        pr_matches = set(
            re.findall(
                r"(?:closes|fixes|resolves|see|pr)?\s*#(\d+)|pull/(\d+)",
                text_to_search,
                re.IGNORECASE,
            )
        )
        for match in pr_matches:
            num = match[0] or match[1]
            if num and int(num) != issue_number:
                linked_prs.append(int(num))

        return {
            "title": issue.title,
            "number": issue.number,
            "author": issue.user.login if issue.user else "unknown",
            "state": issue.state,
            "body": issue.body,
            "labels": [label.name for label in issue.labels],
            "assignees": [a.login for a in issue.assignees],
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            "linked_prs": sorted(list(set(linked_prs))),
            "comments_count": issue.comments,
            "comments": comments,
        }

    return await run_async_github_call(_sync_inspect_issue)


async def search_code(
    repos: list[str],
    pattern: str,
    file_extension: str | None = None,
    github_client: Github | None = None,
) -> list[dict[str, Any]]:
    """Search code across given repositories matching pattern and optional extension.

    Args:
        repos: List of repo names in 'owner/repo' format.
        pattern: Code search term or pattern.
        file_extension: Optional file extension filter (e.g. 'py', 'json', 'ts').
        github_client: Optional pre-configured PyGithub instance.
    """
    client = github_client or get_github_client()

    def _sync_search_code() -> list[dict[str, Any]]:
        results = []
        for repo in repos:
            query = f"{pattern} repo:{repo}"
            if file_extension:
                ext = file_extension.lstrip(".")
                query += f" extension:{ext}"

            code_matches = client.search_code(query=query)
            item: Any
            for item in code_matches[:15]:
                snippet = None
                if item.text_matches:
                    snippet = "\n".join(
                        [tm.get("fragment", "") for tm in item.text_matches if isinstance(tm, dict)]
                    )

                results.append(
                    {
                        "repo": repo,
                        "path": item.path,
                        "url": item.html_url,
                        "sha": item.sha,
                        "snippet": snippet,
                    }
                )
        return results

    return await run_async_github_call(_sync_search_code)


async def recent_commits(
    repo: str,
    branch: str = "main",
    days: int = 7,
    limit: int = 20,
    github_client: Github | None = None,
) -> list[dict[str, Any]]:
    """Fetch recent commits for a repository branch within the specified days lookback.

    Args:
        repo: Repository name in 'owner/repo' format.
        branch: Branch name (default: 'main').
        days: Days lookback (default: 7).
        limit: Maximum number of commits (default: 20).
        github_client: Optional pre-configured PyGithub instance.
    """
    client = github_client or get_github_client()
    since_date = datetime.now(UTC) - timedelta(days=days)

    def _sync_recent_commits() -> list[dict[str, Any]]:
        gh_repo = client.get_repo(repo)
        commits_paginated = gh_repo.get_commits(sha=branch, since=since_date)

        commits_list = []
        commit: Any
        for commit in commits_paginated[:limit]:
            author_name = "unknown"
            if commit.author:
                author_name = commit.author.login
            elif commit.commit.author:
                author_name = commit.commit.author.name or "unknown"

            commits_list.append(
                {
                    "sha": commit.sha,
                    "short_sha": commit.sha[:7],
                    "author": author_name,
                    "message": commit.commit.message,
                    "timestamp": (
                        commit.commit.author.date.isoformat()
                        if commit.commit.author and commit.commit.author.date
                        else None
                    ),
                    "files_changed_count": len(commit.files) if commit.files else 0,
                    "additions": commit.stats.additions if commit.stats else 0,
                    "deletions": commit.stats.deletions if commit.stats else 0,
                }
            )
        return commits_list

    return await run_async_github_call(_sync_recent_commits)


async def update_repo_visibility(
    repo: str,
    private: bool,
    github_client: Github | None = None,
) -> dict[str, Any]:
    """Change visibility of a repository to private or public.

    Args:
        repo: Repository name in 'owner/repo' format (or just repository name).
        private: True to set repository to private, False to set to public.
        github_client: Optional pre-configured PyGithub instance.
    """
    client = github_client or get_github_client()

    def _sync_edit() -> dict[str, Any]:
        full_repo_name = repo
        if "/" not in full_repo_name:
            user = client.get_user()
            full_repo_name = f"{user.login}/{repo}"

        gh_repo = client.get_repo(full_repo_name)
        gh_repo.edit(private=private)

        updated_repo = client.get_repo(full_repo_name)

        vis_str = "private" if updated_repo.private else "public"
        return {
            "status": "success",
            "repo": updated_repo.full_name,
            "private": updated_repo.private,
            "url": updated_repo.html_url,
            "message": (
                f"Successfully updated repository '{updated_repo.full_name}' "
                f"visibility to {vis_str}."
            ),
        }

    return await run_async_github_call(_sync_edit)
