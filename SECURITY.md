# Security Policy

This document outlines the security policies, vulnerability reporting procedure, and secure development guidelines for the LFSD repository.

## Supported Versions

We actively support and apply security patches to the following versions of the application:

| Version | Supported |
| ------- | --------- |
| v2.x.x  | ✅ Yes    |
| v1.x.x  | ❌ No     |

## Reporting a Vulnerability

If you identify a security vulnerability within this repository or the running deployment, please do **NOT** open a public GitHub issue. Instead, report it responsibly:

1. **Contact Email**: Please send reports to [security@helmory.com](mailto:security@helmory.com).
2. **Details to Include**:
   - Description of the vulnerability or suspected bug.
   - Step-by-step instructions to reproduce the issue.
   - Potential impact of the issue.
3. **Response Timeline**: The security team will acknowledge receipt of your report within 48 hours and coordinate a remediation timeline.

## Secure Development Guidelines for Contributors

All contributors must adhere to the following secure coding practices to prevent credential leaks and common vulnerabilities:

### 1. Zero Secret Hardcoding
- Never hardcode API keys, passwords, private keys, database connection strings, or Auth0 secrets in the codebase.
- Use `core/config.py` and environment variables (via `.env` files locally or GCP Cloud Run environment variables in production).
- Ensure `.gitignore` ignores local `.env` and `*.key` / `secrets.json` files.

### 2. Dependency Management
- Only add verified, reputable packages to `requirements.txt`.
- Pin version numbers where appropriate to prevent supply-chain dependency hijacking.

### 3. Automated Scanning Tools
We use the following tools in our local testing and CI/CD pipelines to enforce code security:
- **Bandit**: Scans python code for common vulnerabilities (e.g. SQL injection, unsafe deserialization, shell execution).
- **Safety**: Scans dependency manifests (`requirements.txt`) against a database of known package CVEs.

To run these checks locally:
```bash
# Install development requirements
pip install -r backend/requirements-dev.txt

# Run Bandit code scan
bandit -r backend/

# Run Safety dependency scan
safety check -r backend/requirements.txt
```
