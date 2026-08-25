<div align="center">

# 🐙 GithubMCP

**A Production-Grade Personal Developer Assistant MCP Server**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python)](https://www.python.org/)
[![Managed by: uv](https://img.shields.io/badge/managed%20by-uv-DE5FE9.svg?logo=astral)](https://github.com/astral-sh/uv)
[![MCP Compatible](https://img.shields.io/badge/MCP-Official%20SDK-black.svg)](https://modelcontextprotocol.io/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked with: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

*Seamlessly connect AI models (Claude, Cursor, etc.) to your GitHub workflows, CI/CD pipelines, local workspace context, and code analysis tools.*

</div>

---

## 🌟 Overview

**GithubMCP** is a Model Context Protocol (MCP) server designed for developers. It bridges AI assistants directly with your development environment, enabling them to:
- Inspect GitHub repositories, pull requests, issues, commits, and code across public and private repositories.
- Manage repository privacy & visibility (public/private) directly through conversation.
- Monitor CI/CD workflow runs and parse failed GitHub Actions build steps.
- Inspect local filesystem workspaces safely within user-defined allowed paths.
- Analyze code quality, calculate complexity metrics, find TODOs, and detect potential security smells (hardcoded secrets).

Supports both **STDIO** (Claude Desktop, Cursor) and **SSE** (Server-Sent Events for web clients) transport modes.

---

## 🛠️ Tool Suite Reference

GithubMCP provides **13 specialized tools**:

| Category | Tool Name | Description |
| :--- | :--- | :--- |
| **GitHub** | `search_repos` | Search public & private user/org repositories with language & sort filters. |
| **GitHub** | `inspect_pr` | Fetch PR details, changed files, addition/deletion stats, and review comments. |
| **GitHub** | `inspect_issue` | Inspect issue state, assignees, linked PRs, labels, and recent comments. |
| **GitHub** | `search_code` | Search code patterns across repositories with extension filters. |
| **GitHub** | `recent_commits` | Fetch recent commit history with diff statistics and authors. |
| **GitHub** | `update_repo_visibility` | Change repository visibility between **private** and **public**. |
| **CI/CD** | `check_ci_status` | Monitor GitHub Actions status (success/failure/in-progress) and failed step logs. |
| **Filesystem** | `read_file` | Read local file contents safely with MIME type detection and size validation. |
| **Filesystem** | `list_directory` | List directory tree structure with file sizes, mtime, and glob filters. |
| **Filesystem** | `search_local_files` | Asynchronously grep files for regex/patterns with surrounding line context. |
| **Filesystem** | `get_project_context` | Detect project tech stack (Node, Python, Rust, Go, Docker) & dev commands. |
| **Analysis** | `generate_change_summary` | Compare git refs and categorize commits into Features, Fixes, Breaking Changes, etc. |
| **Analysis** | `analyze_code_quality` | Compute lines of code, complexity estimate, TODO comments, and secret smells. |

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **[uv](https://github.com/astral-sh/uv)** (Fast Python package manager)

Install `uv` (if not already installed):
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone & Setup
```bash
git clone https://github.com/Dhananjayrbiraris/github-mcp.git
cd github-mcp

# Install dependencies and sync virtual environment
uv sync
```

### 3. Environment Configuration
Copy the template `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your GitHub Personal Access Token:
```env
# GitHub Personal Access Token (Classic PAT with 'repo', 'workflow', 'read:user' scopes)
GITHUB_TOKEN=ghp_your_github_token_here

# Default GitHub Username (Optional)
GITHUB_USERNAME=your_username

# Sandboxed directories allowed for local filesystem operations
ALLOWED_PATHS=["~/projects", "~/workspace", "."]

# Max file size limit in MB for reading files
MAX_FILE_SIZE_MB=10

# Default Transport mode: "stdio" or "sse"
TRANSPORT=stdio
```

> **Generating your GitHub Token:**
> Go to [GitHub Settings -> Developer Settings -> Personal access tokens (classic)](https://github.com/settings/tokens/new) and generate a token with `repo`, `workflow`, and `read:user` scopes.

---

## 🤖 Client Setup Guides

### A. Claude Desktop

#### 1. Open the Claude Desktop configuration file:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### 2. Add the `github-mcp` server:

```json
{
  "mcpServers": {
    "github-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/github-mcp",
        "run",
        "python",
        "-m",
        "github_mcp.main",
        "--transport",
        "stdio"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_your_personal_access_token_here"
      }
    }
  }
}
```

*(On Windows, use backslashes e.g. `C:\\Users\\yourname\\path\\to\\github-mcp` or forward slashes).*

#### 3. Restart Claude Desktop
Open Claude Desktop — click the **🔨 Hammer / Tools icon** at the bottom right of the prompt box to view all connected GithubMCP tools.

---

### B. Cursor IDE

In Cursor:
1. Navigate to **Cursor Settings** -> **Features** -> **MCP**.
2. Click **+ Add New MCP Server**.
3. Fill in:
   - **Name:** `github-mcp`
   - **Type:** `command`
   - **Command:** `uv --directory /path/to/github-mcp run python -m github_mcp.main --transport stdio`

---

### C. Server-Sent Events (SSE) Mode / Web Clients

To run the MCP server over HTTP / Server-Sent Events:
```bash
uv run python -m github_mcp.main --transport sse --host 0.0.0.0 --port 8000
```
SSE endpoint will be available at: `http://localhost:8000/sse`

---

## 🔒 Security & Sandboxing

1. **Path Sandboxing:** Local filesystem tools (`read_file`, `list_directory`, `search_local_files`, `get_project_context`) strictly enforce path traversal validation against `ALLOWED_PATHS`. Accessing paths outside the allowlist will raise a `SecurityError`.
2. **Secret Management:** Tokens and credentials are never logged or exposed.
3. **Rate Limit Resilience:** Automatic exponential backoff retries on GitHub API rate limit throttling.

---

## 🧪 Development & Testing

Run the full testing and quality check suite:

```bash
# Run pytest unit tests
uv run pytest

# Run linter
uv run ruff check .

# Check code formatting
uv run ruff format --check .

# Run strict type checking
uv run mypy src/
```

---

## 📁 Repository Structure

```text
github-mcp/
├── .github/workflows/ci.yml # GitHub Actions CI workflow
├── src/github_mcp/
│   ├── __init__.py
│   ├── main.py              # Server entrypoint & MCP tool registrations
│   ├── config.py            # Pydantic Settings model
│   ├── github_tools.py      # GitHub API integrations & visibility controls
│   ├── file_tools.py        # Sandboxed local filesystem operations
│   ├── ci_tools.py          # GitHub Actions CI/CD monitoring
│   ├── analysis_tools.py    # Diff categorization & code quality analyzer
│   └── utils.py             # Path safety, error handling, rate limiting
├── tests/
│   ├── conftest.py          # Pytest fixtures and mocks
│   ├── test_github.py       # GitHub tools unit tests
│   ├── test_files.py        # Filesystem tools unit tests
│   └── test_ci.py           # CI status tools unit tests
├── docs/
│   ├── architecture.md      # System architecture & data flow
│   └── tools_reference.md   # Complete API schemas for all 13 tools
├── pyproject.toml           # Project dependencies & tool configurations
├── .env.example             # Environment variable template
├── CONTRIBUTING.md          # Open-source contribution guidelines
├── SECURITY.md              # Security policy & vulnerability reporting
└── LICENSE                  # MIT License
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — free for personal and commercial use.

---

<div align="center">
Built with ❤️ using the <a href="https://modelcontextprotocol.io/">Model Context Protocol</a> and <a href="https://github.com/astral-sh/uv">UV</a>.
</div>
