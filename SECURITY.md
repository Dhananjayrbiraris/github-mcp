# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability or potential exploit within **GithubMCP**, please **do not** open a public GitHub issue.

Instead, please report security issues privately to the project maintainer via:
- Email: `dhananjayrbiraris@gmail.com` or through [GitHub Private Vulnerability Reporting](https://github.com/Dhananjayrbiraris/github-mcp/security/advisories/new).

Please include:
- A description of the issue and potential impact
- Steps or proof-of-concept to reproduce the issue
- Any potential mitigation suggestions

We will investigate and respond to security advisories promptly.

---

## 🔒 Security Best Practices for Users
- **Never commit `.env` files** containing your GitHub personal access tokens.
- Restrict `ALLOWED_PATHS` in `config.py` / `.env` to trusted directories to ensure local filesystem operations remain safely sandboxed.
- Regularly rotate your GitHub Personal Access Tokens.
