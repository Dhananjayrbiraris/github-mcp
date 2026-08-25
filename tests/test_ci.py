"""Unit tests for CI/CD tools using PyGithub mocks."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from github_mcp.ci_tools import check_ci_status


@pytest.mark.asyncio
async def test_check_ci_status_success(mock_github: MagicMock) -> None:
    mock_repo = MagicMock()
    mock_run = MagicMock()
    mock_run.id = 101
    mock_run.name = "CI Workflow"
    mock_run.head_branch = "main"
    mock_run.event = "push"
    mock_run.status = "completed"
    mock_run.conclusion = "success"
    mock_run.html_url = "https://github.com/user/repo/actions/runs/101"
    mock_run.created_at = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    mock_run.updated_at = datetime(2026, 1, 1, 10, 2, 30, tzinfo=UTC)

    mock_repo.get_workflow_runs.return_value = [mock_run]
    mock_github.get_repo.return_value = mock_repo

    res = await check_ci_status("user/repo", branch="main", github_client=mock_github)
    assert res["overall_status"] == "success"
    assert res["latest_run"]["id"] == 101
    assert res["latest_run"]["duration_seconds"] == 150


@pytest.mark.asyncio
async def test_check_ci_status_failure(mock_github: MagicMock) -> None:
    mock_repo = MagicMock()
    mock_run = MagicMock()
    mock_run.id = 102
    mock_run.name = "CI Workflow"
    mock_run.head_branch = "main"
    mock_run.event = "push"
    mock_run.status = "completed"
    mock_run.conclusion = "failure"
    mock_run.html_url = "https://github.com/user/repo/actions/runs/102"
    mock_run.created_at = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    mock_run.updated_at = datetime(2026, 1, 1, 10, 1, 0, tzinfo=UTC)

    mock_job = MagicMock()
    mock_job.name = "build-and-test"
    mock_job.conclusion = "failure"

    mock_step = MagicMock()
    mock_step.name = "Run unit tests"
    mock_step.number = 4
    mock_step.conclusion = "failure"

    mock_job.steps = [mock_step]
    mock_run.jobs.return_value = [mock_job]

    mock_repo.get_workflow_runs.return_value = [mock_run]
    mock_github.get_repo.return_value = mock_repo

    res = await check_ci_status("user/repo", branch="main", github_client=mock_github)
    assert res["overall_status"] == "failure"
    failed_steps = res["latest_run"]["failed_steps"]
    assert len(failed_steps) == 1
    assert failed_steps[0]["step_name"] == "Run unit tests"
