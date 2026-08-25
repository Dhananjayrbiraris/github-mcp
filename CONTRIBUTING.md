# Contributing to GithubMCP

Thank you for your interest in contributing to **GithubMCP**! We welcome bug reports, feature suggestions, documentation improvements, and pull requests.

---

## 🛠️ Development Setup

### 1. Prerequisites
- Python 3.11+
- [UV package manager](https://github.com/astral-sh/uv) (recommended) or pip

### 2. Clone and Install Dependencies
```bash
git clone https://github.com/Dhananjayrbiraris/github-mcp.git
cd github-mcp

# Install dependencies and setup virtual environment
uv sync --all-groups
```

### 3. Setup Environment Variables
```bash
cp .env.example .env
# Edit .env and configure your GITHUB_TOKEN
```

---

## 🧪 Testing and Quality Checks

Before submitting a Pull Request, ensure that all quality gates pass:

```bash
# 1. Run unit tests
uv run pytest

# 2. Run linter
uv run ruff check .

# 3. Check formatting
uv run ruff format --check .

# 4. Run static type checking
uv run mypy src/
```

---

## 🚀 Pull Request Guidelines

1. Fork the repository and create a new feature branch:
   ```bash
   git checkout -b feature/my-new-tool
   ```
2. Commit your changes with clear, concise messages.
3. Add unit tests in `tests/` covering new tools or changes.
4. Ensure all CI checks (pytest, ruff, mypy) pass.
5. Push to your fork and submit a Pull Request.

---

## 📄 License
By contributing to GithubMCP, you agree that your contributions will be licensed under the [MIT License](LICENSE).
