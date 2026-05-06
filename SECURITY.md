# Security Policy

## Scope

This skill is **read-only** by design. It does not create, modify, or delete any AWS or Kubernetes resources. All operations are `describe`, `list`, and `get` calls.

Generated manifests in `target/` directories are proposals only — they are never applied automatically.

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do NOT open a public GitHub issue** for security vulnerabilities.
2. Email the maintainer directly or use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability).
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

- **Acknowledgment:** Within 48 hours
- **Assessment:** Within 7 days
- **Fix (if applicable):** Within 30 days for critical issues

## Security Best Practices for Users

- Use **least-privilege IAM permissions** — only grant the permissions listed in [Required Permissions](README.md#required-permissions).
- Review generated manifests in `target/` before applying to any cluster.
- Do not commit AWS credentials, tokens, or secrets to this repository.
- Keep MCP server dependencies up to date.
