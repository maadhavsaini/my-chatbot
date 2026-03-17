# Security Policy

## Supported Versions

| Version | Supported         |
| ------- | ----------------- |
| 1.0.x   | ✅ Active support |

## Reporting a Vulnerability

At Veritax, we take security seriously. If you discover a vulnerability, please follow responsible disclosure practices.

**Do not open a public GitHub issue for security vulnerabilities.**

### How to Report

Please reach out through our GitHub repository by opening a **private security advisory**.

Please include:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested remediation (optional)

### What to Expect

- **Acknowledgement** within 48 hours
- **Status update** within 7 days
- **Resolution timeline** communicated as soon as assessed

We appreciate responsible disclosure and will credit researchers who report valid vulnerabilities.

## Security Practices

Veritax implements the following security measures:

- All passwords are hashed using SHA-256 before storage
- No plaintext credentials are ever stored or logged
- API keys are stored as environment variables, never in code
- User sessions are managed via browser sessionStorage
- All data in transit is encrypted via HTTPS
- Database access is restricted via Supabase Row Level Security

## Scope

The following are **in scope** for security reports:

- Authentication bypass
- Data exposure or leakage
- SQL injection or database vulnerabilities
- Cross-site scripting (XSS)
- Cross-site request forgery (CSRF)

The following are **out of scope**:

- Social engineering attacks
- Denial of service attacks
- Issues in third-party dependencies (report to them directly)

## Responsible Disclosure

We ask that you:

- Give us reasonable time to fix issues before public disclosure
- Avoid accessing or modifying other users' data
- Do not perform actions that could harm the availability of the service

Thank you for helping keep Veritax safe. 🖤

---

_Veritax · 2026_
