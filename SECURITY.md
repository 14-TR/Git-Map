# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.6.x   | ✅ Current |
| < 0.6   | ❌ No longer supported |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please report it privately:

1. Open a [GitHub Security Advisory](https://github.com/14-TR/Git-Map/security/advisories/new) — this creates a private, encrypted channel with the maintainer.
2. Alternatively, contact the maintainer directly via the email listed at [ingramgeoai.com](https://ingramgeoai.com).

Include:
- A description of the vulnerability and its potential impact
- Steps to reproduce or proof-of-concept (if applicable)
- Any suggested remediation

You can expect an acknowledgment within **72 hours** and a resolution timeline within **14 days** for confirmed vulnerabilities.

## Scope

This policy covers:

- `gitmap_core` library
- `gitmap` CLI application
- MCP server

## Credential Handling Notes

Git-Map stores ArcGIS credentials (username, password, Portal URL) in `.gitmap/config.json` within your project directory. **Do not commit this file to version control.** The default `.gitignore` excludes it, but verify your setup if you maintain a custom ignore file.

Never share your `.gitmap/config.json` or `.env` files publicly.
