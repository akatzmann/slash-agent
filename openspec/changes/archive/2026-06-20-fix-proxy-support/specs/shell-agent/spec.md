## ADDED Requirements

### Requirement: Proxy Environment Normalization and Sync
The system SHALL normalize, sanitize, and bidirectionally synchronize proxy environment variables (`HTTP_PROXY`/`http_proxy`, `HTTPS_PROXY`/`https_proxy`, `NO_PROXY`/`no_proxy`) at startup. It MUST:
1. Ensure both lowercase (Linux-preferred) and uppercase (Python-preferred) variations of each variable have identical values.
2. Strip shell-style wildcards (e.g., `*` or `*.`) from `NO_PROXY`/`no_proxy` values for compatibility with HTTP clients (e.g. `httpx`).
3. Automatically append default local bypasses (`localhost`, `127.0.0.1`) to `NO_PROXY`/`no_proxy` if any HTTP/HTTPS proxy is configured.
4. Ensure the sanitized environment is fully loaded before initializing any agent core systems and propagated statefully to PTY subprocess command executions.

#### Scenario: Sanitizing wildcards and adding local bypasses
- **WHEN** the agent starts and `HTTP_PROXY` is set to `http://proxy.example.com` and `no_proxy` is set to `*.local,10.0.0.1`
- **THEN** the system SHALL update `os.environ` and `session_state.env_vars` so that both `no_proxy` and `NO_PROXY` contain `local,10.0.0.1,localhost,127.0.0.1` and both `HTTP_PROXY` and `http_proxy` contain `http://proxy.example.com`.
