# GithubMCP Tools Reference

Detailed input parameters and output schemas for all 12 tools provided by the `GithubMCP` server.

---

## 1. GitHub Integration Tools

### 1. `search_repos`
Search GitHub repositories with optional language filtering and sort order.
- **Inputs**:
  - `query` (str): Search term or repository name query.
  - `language` (str, optional): Language filter (e.g. `'python'`, `'typescript'`).
  - `sort` (str, optional): Sort criteria (`'stars'`, `'forks'`, `'updated'`). Default: `'stars'`.
  - `limit` (int, default: 10): Maximum number of results.
- **Output Schema**:
  - Array of objects containing `name`, `full_name`, `description`, `stars`, `forks`, `language`, `url`, `last_pushed`.

### 2. `inspect_pr`
Inspect pull request details, file diff statistics, and review comments.
- **Inputs**:
  - `repo` (str): Repository in `'owner/repo'` format.
  - `pr_number` (int): Pull request number.
- **Output Schema**:
  - Object containing `title`, `number`, `author`, `state`, `merged`, `mergeable`, `body`, `labels`, `created_at`, `additions`, `deletions`, `changed_files`, `review_comments`.

### 3. `inspect_issue`
Inspect issue details, assignees, linked PRs, and recent comments.
- **Inputs**:
  - `repo` (str): Repository in `'owner/repo'` format.
  - `issue_number` (int): Issue number.
- **Output Schema**:
  - Object containing `title`, `number`, `author`, `state`, `body`, `labels`, `assignees`, `created_at`, `linked_prs`, `comments_count`, `comments`.

### 4. `search_code`
Search code across specific repositories with pattern matching and file extension filters.
- **Inputs**:
  - `repos` (list[str]): List of repository names in `'owner/repo'` format.
  - `pattern` (str): Code pattern or regex to search for.
  - `file_extension` (str, optional): Extension filter (e.g. `'py'`, `'ts'`).
- **Output Schema**:
  - Array of objects containing `repo`, `path`, `url`, `sha`, `snippet`.

### 5. `recent_commits`
Fetch recent commits for a repository branch within a lookback period.
- **Inputs**:
  - `repo` (str): Repository in `'owner/repo'` format.
  - `branch` (str, default: `'main'`): Target branch.
  - `days` (int, default: 7): Days lookback.
  - `limit` (int, default: 20): Maximum number of commits.
- **Output Schema**:
  - Array of objects containing `sha`, `short_sha`, `author`, `message`, `timestamp`, `files_changed_count`, `additions`, `deletions`.

### 6. `create_pull_request`
Create a new pull request in a GitHub repository.
- **Inputs**:
  - `repo` (str): Repository in `'owner/repo'` format.
  - `title` (str): Pull request title.
  - `head` (str): Branch containing changes.
  - `base` (str, default: `'main'`): Target branch to merge into.
  - `body` (str, optional): Description of the PR.
  - `draft` (bool, default: False): Whether to create as draft.
- **Output Schema**:
  - Object containing `status`, `number`, `title`, `url`, `head`, `base`, `draft`, `state`, `message`.

### 7. `create_branch`
Create a new git branch in a GitHub repository off of an existing branch.
- **Inputs**:
  - `repo` (str): Repository in `'owner/repo'` format.
  - `branch` (str): Name of the new branch.
  - `from_branch` (str, default: `'main'`): Base branch name.
- **Output Schema**:
  - Object containing `status`, `repo`, `branch`, `from_branch`, `sha`, `message`.

### 8. `create_or_update_file`
Create or update and commit a file directly on a GitHub branch.
- **Inputs**:
  - `repo` (str): Repository in `'owner/repo'` format.
  - `path` (str): Target file path in the repository.
  - `content` (str): File text content.
  - `message` (str): Git commit message.
  - `branch` (str, default: `'main'`): Target branch.
- **Output Schema**:
  - Object containing `status`, `repo`, `path`, `action`, `branch`, `commit_sha`, `message`.

### 9. `create_issue`
Create a new issue in a GitHub repository.
- **Inputs**:
  - `repo` (str): Repository in `'owner/repo'` format.
  - `title` (str): Issue title.
  - `body` (str, optional): Issue description.
  - `labels` (list[str], optional): List of label names.
  - `assignees` (list[str], optional): List of usernames to assign.
- **Output Schema**:
  - Object containing `status`, `number`, `title`, `url`, `state`, `labels`, `assignees`, `message`.

### 10. `update_repo_visibility`
Update the privacy/visibility settings of a repository to make it private or public.
- **Inputs**:
  - `repo` (str): Repository name in `'owner/repo'` format (or repository name).
  - `private` (bool): `True` to make private, `False` to make public.
- **Output Schema**:
  - Object containing `status`, `repo`, `private`, `url`, `message`.

---

## 2. CI/CD Monitoring Tools

### 6. `check_ci_status`
Check CI/CD build status, workflow duration, log links, and failed steps summary.
- **Inputs**:
  - `repo` (str): Repository in `'owner/repo'` format.
  - `branch` (str, default: `'main'`): Target branch or ref.
  - `platform` (str, default: `'github_actions'`): CI platform.
- **Output Schema**:
  - Object containing `repo`, `branch`, `platform`, `overall_status`, `latest_run`, `recent_runs` (including `failed_steps`).

---

## 3. Local Filesystem Tools

### 7. `read_file`
Safely read file content within allowed paths.
- **Inputs**:
  - `path` (str): Relative or absolute path to local file.
- **Output Schema**:
  - Object containing `path`, `size_bytes`, `mime_type`, `encoding`, `content`, `is_truncated`.

### 8. `list_directory`
List directory tree structure with file sizes and modification dates.
- **Inputs**:
  - `path` (str): Target directory path.
  - `recursive` (bool, default: False): Enable recursive directory listing.
  - `depth_limit` (int, default: 3): Maximum depth when recursive.
  - `glob_pattern` (str, optional): Glob filter (e.g. `'*.py'`).
- **Output Schema**:
  - Object containing `directory`, `total_items`, `items`.

### 9. `search_local_files`
Search local text files for pattern with line numbers and surrounding context.
- **Inputs**:
  - `path` (str): Base directory path.
  - `pattern` (str): Search pattern or keyword.
  - `case_sensitive` (bool, default: False): Case sensitivity flag.
  - `file_type` (str, optional): Extension filter (e.g. `'py'`).
- **Output Schema**:
  - Array of objects containing `file`, `line_number`, `line_content`, `context`.

### 10. `get_project_context`
Detect project stack, key config files, dependencies, and dev commands.
- **Inputs**:
  - `root_path` (str): Root project directory path.
- **Output Schema**:
  - Object containing `root`, `project_types`, `config_files_found`, `sample_dependencies`, `suggested_dev_commands`.

---

## 4. Code Analysis Tools

### 11. `generate_change_summary`
Categorize changes between base and head git refs into Features, Fixes, Breaking Changes, and Config Updates.
- **Inputs**:
  - `repo` (str): Repository in `'owner/repo'` format.
  - `base_ref` (str): Base ref or commit SHA.
  - `head_ref` (str): Head ref or commit SHA.
- **Output Schema**:
  - Object containing `repo`, `base_ref`, `head_ref`, `total_commits`, `categorized_changes`, `changed_files_summary`.

### 12. `analyze_code_quality`
Analyze local file metrics, TODO comments, complexity estimates, and hardcoded secret smells.
- **Inputs**:
  - `path` (str): Target file path.
- **Output Schema**:
  - Object containing `file`, `extension`, `metrics`, `todo_fixme_count`, `todo_fixme_list`, `security_smells_count`, `security_smells`.
