# Security Policy

We take the security and privacy of `slash-agent` seriously. This document outlines supported versions and instructions for reporting security vulnerabilities privately.

---

## Supported Versions

Only the latest release version of `slash-agent` is actively supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| v0.1.x  | :white_check_mark: |
| < v0.1  | :x:                |

---

## Privacy & Local Integrity

`slash-agent` is designed with privacy-first principles:
* **No Telemetry**: The agent does not track keystrokes, log background analytics, or transmit session data to third-party tracking servers.
* **Bring Your Own Keys (BYOK)**: Requests are sent directly from your client to configured LLM provider API endpoints.
* **Air-Gapped / Offline Capable**: When pointed to local endpoints (such as Ollama at `http://127.0.0.1:11434`), zero data leaves your machine.

---

## Reporting a Vulnerability

If you discover a security vulnerability in this project (including command injection vectors or unsanitized input risks), please **do not** open a public issue. 

Instead, report it privately through one of the following channels:
* **GitHub Private Vulnerability Reporting**: Submit a report privately via the "Security" tab of this repository on GitHub.
* **Maintainer Contact**: Contact project maintainer `@akatzmann` directly on GitHub.

Please include the following details in your report:
* A detailed description of the vulnerability.
* Steps to reproduce or a minimal proof-of-concept script.
* Potential impact on local terminal sessions or environment variables.

---

## Disclosure Process

Upon receiving a private security report:
1. **Acknowledgment**: The maintainers will acknowledge receipt within 48 hours.
2. **Investigation**: We will investigate and verify the vulnerability privately.
3. **Patch & Advisory**: We will develop a fix, issue a patch release, and publish a security advisory.
