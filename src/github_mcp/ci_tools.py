"""CI/CD monitoring tools for GithubMCP server."""

from typing import Any

from github import Github

from github_mcp.utils import get_github_client, run_async_github_call


async def check_ci_status(
    repo: str,
    branch: str = "main",
    platform: str = "github_actions",
    github_client: Github | None = None,
) -> dict[str, Any]:
    """Check current CI/CD status for a repository branch.

    Args:
        repo: Repository name in 'owner/repo' format.
        branch: Branch name or git ref (default: 'main').
        platform: CI platform name (default: 'github_actions').
        github_client: Optional pre-configured PyGithub instance.
    """
    if platform.lower() not in ("github_actions", "actions", "github"):
        return {
            "status": "error",
            "message": (
                f"Unsupported CI platform: {platform}. Currently supported: 'github_actions'."
            ),
        }

    client = github_client or get_github_client()

    def _sync_check_ci() -> dict[str, Any]:
        gh_repo = client.get_repo(repo)
        runs: Any = gh_repo.get_workflow_runs(branch=branch)  # type: ignore[arg-type]

        latest_runs = []
        for run in list(runs)[:5]:
            failed_steps = []
            if run.conclusion == "failure":
                try:
                    jobs = run.jobs()
                    for job in jobs:
                        if job.conclusion == "failure":
                            for step in job.steps:
                                if step.conclusion == "failure":
                                    failed_steps.append(
                                        {
                                            "job_name": job.name,
                                            "step_name": step.name,
                                            "number": step.number,
                                            "conclusion": step.conclusion,
                                        }
                                    )
                except Exception:
                    pass

            duration_seconds = None
            if run.created_at and run.updated_at:
                duration_seconds = int((run.updated_at - run.created_at).total_seconds())

            latest_runs.append(
                {
                    "id": run.id,
                    "name": run.name,
                    "head_branch": run.head_branch,
                    "event": run.event,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "html_url": run.html_url,
                    "duration_seconds": duration_seconds,
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                    "failed_steps": failed_steps,
                }
            )

        overall_status = "unknown"
        if latest_runs:
            first = latest_runs[0]
            if first["status"] in ("in_progress", "queued"):
                overall_status = first["status"]
            else:
                overall_status = first["conclusion"] or first["status"]

        return {
            "repo": repo,
            "branch": branch,
            "platform": "github_actions",
            "overall_status": overall_status,
            "latest_run": latest_runs[0] if latest_runs else None,
            "recent_runs": latest_runs,
        }

    return await run_async_github_call(_sync_check_ci)
