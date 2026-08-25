"""Unit tests for GitHub integration tools using PyGithub mocks."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from github_mcp.analysis_tools import generate_change_summary
from github_mcp.github_tools import (
    inspect_issue,
    inspect_pr,
    recent_commits,
    search_code,
    search_repos,
)


@pytest.mark.asyncio
async def test_search_repos(mock_github: MagicMock) -> None:
    mock_repo = MagicMock()
    mock_repo.name = "test-repo"
    mock_repo.full_name = "user/test-repo"
    mock_repo.description = "A test repo"
    mock_repo.stargazers_count = 100
    mock_repo.forks_count = 20
    mock_repo.language = "Python"
    mock_repo.html_url = "https://github.com/user/test-repo"
    mock_repo.pushed_at = datetime(2026, 1, 1, tzinfo=UTC)

    mock_github.search_repositories.return_value = [mock_repo]

    results = await search_repos("test", language="python", limit=5, github_client=mock_github)
    assert len(results) == 1
    assert results[0]["name"] == "test-repo"
    assert results[0]["stars"] == 100
    assert results[0]["language"] == "Python"


@pytest.mark.asyncio
async def test_inspect_pr(mock_github: MagicMock) -> None:
    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_pr.title = "Add feature X"
    mock_pr.number = 42
    mock_pr.user.login = "octocat"
    mock_pr.state = "open"
    mock_pr.merged = False
    mock_pr.mergeable = True
    mock_pr.body = "Implements feature X"
    mock_pr.labels = []
    mock_pr.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    mock_pr.updated_at = datetime(2026, 1, 2, tzinfo=UTC)
    mock_pr.merged_at = None
    mock_pr.additions = 50
    mock_pr.deletions = 10
    mock_pr.changed_files = 2

    mock_file1 = MagicMock()
    mock_file1.filename = "src/app.py"
    mock_file1.status = "modified"
    mock_file1.additions = 30
    mock_file1.deletions = 5
    mock_file1.changes = 35
    mock_file1.patch = "@@ -1,3 +1,5 @@"

    mock_pr.get_files.return_value = [mock_file1]
    mock_pr.get_review_comments.return_value = []
    mock_repo.get_pull.return_value = mock_pr
    mock_github.get_repo.return_value = mock_repo

    res = await inspect_pr("user/repo", 42, github_client=mock_github)
    assert res["title"] == "Add feature X"
    assert res["author"] == "octocat"
    assert res["additions"] == 50
    assert len(res["changed_files"]) == 1


@pytest.mark.asyncio
async def test_inspect_issue(mock_github: MagicMock) -> None:
    mock_repo = MagicMock()
    mock_issue = MagicMock()
    mock_issue.title = "Bug in login"
    mock_issue.number = 15
    mock_issue.user.login = "alice"
    mock_issue.state = "open"
    mock_issue.body = "Fixes #10 and closes pull/20"
    mock_issue.labels = []
    mock_issue.assignees = []
    mock_issue.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    mock_issue.updated_at = datetime(2026, 1, 2, tzinfo=UTC)
    mock_issue.closed_at = None
    mock_issue.comments = 0
    mock_issue.get_comments.return_value = []

    mock_repo.get_issue.return_value = mock_issue
    mock_github.get_repo.return_value = mock_repo

    res = await inspect_issue("user/repo", 15, github_client=mock_github)
    assert res["title"] == "Bug in login"
    assert res["number"] == 15
    assert 20 in res["linked_prs"]


@pytest.mark.asyncio
async def test_search_code(mock_github: MagicMock) -> None:
    mock_item = MagicMock()
    mock_item.path = "main.py"
    mock_item.html_url = "https://github.com/user/repo/blob/main/main.py"
    mock_item.sha = "abc1234"
    mock_item.text_matches = None

    mock_github.search_code.return_value = [mock_item]

    res = await search_code(
        ["user/repo"], "def main", file_extension="py", github_client=mock_github
    )
    assert len(res) == 1
    assert res[0]["path"] == "main.py"


@pytest.mark.asyncio
async def test_recent_commits(mock_github: MagicMock) -> None:
    mock_repo = MagicMock()
    mock_commit = MagicMock()
    mock_commit.sha = "1234567890abcdef"
    mock_commit.author.login = "bob"
    mock_commit.commit.message = "feat: initial commit"
    mock_commit.commit.author.date = datetime(2026, 1, 1, tzinfo=UTC)
    mock_commit.files = [MagicMock()]
    mock_commit.stats.additions = 100
    mock_commit.stats.deletions = 5

    mock_repo.get_commits.return_value = [mock_commit]
    mock_github.get_repo.return_value = mock_repo

    res = await recent_commits("user/repo", days=7, github_client=mock_github)
    assert len(res) == 1
    assert res[0]["short_sha"] == "1234567"
    assert res[0]["author"] == "bob"


@pytest.mark.asyncio
async def test_generate_change_summary(mock_github: MagicMock) -> None:
    mock_repo = MagicMock()
    mock_comparison = MagicMock()
    mock_comparison.ahead_by = 2
    mock_comparison.behind_by = 0

    c1 = MagicMock()
    c1.sha = "abc1111"
    c1.author.login = "dev1"
    c1.commit.message = "feat: add user authentication"

    c2 = MagicMock()
    c2.sha = "abc2222"
    c2.author.login = "dev2"
    c2.commit.message = "fix: resolve token expiry bug"

    mock_comparison.commits = [c1, c2]
    mock_comparison.files = []

    mock_repo.compare.return_value = mock_comparison
    mock_github.get_repo.return_value = mock_repo

    res = await generate_change_summary("user/repo", "v1.0", "v1.1", github_client=mock_github)
    assert res["total_commits"] == 2
    assert len(res["categorized_changes"]["new_features"]) == 1
    assert len(res["categorized_changes"]["bug_fixes"]) == 1


@pytest.mark.asyncio
async def test_update_repo_visibility(mock_github: MagicMock) -> None:
    from github_mcp.github_tools import update_repo_visibility

    mock_repo = MagicMock()
    mock_repo.full_name = "user/repo"
    mock_repo.private = True
    mock_repo.html_url = "https://github.com/user/repo"

    mock_github.get_repo.return_value = mock_repo

    res = await update_repo_visibility("user/repo", private=True, github_client=mock_github)
    assert res["status"] == "success"
    assert res["private"] is True
    assert res["repo"] == "user/repo"
