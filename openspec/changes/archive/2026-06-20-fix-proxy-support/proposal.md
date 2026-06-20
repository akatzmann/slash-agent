## Why

In network environments configured with system-wide proxies (such as corporate intranets), standard HTTP clients often face connection errors when trying to reach local or internal endpoints (like a local Ollama instance running at `127.0.0.1:11434`). 

Currently, `slash-agent` does not explicitly handle or sanitize proxy environment variables (`http_proxy`, `https_proxy`, `no_proxy`/`NO_PROXY`). Under `httpx` (used by the OpenAI and Ollama client backends), requests to local hosts can be erroneously routed to external proxies because:
1. `httpx` fails to parse shell-style wildcards (e.g., `*.local`) in the `no_proxy`/`NO_PROXY` environment variables.
2. `httpx` does not support CIDR ranges (e.g., `127.0.0.0/8`).
3. `httpx` does not automatically bypass local addresses (`127.0.0.1`, `localhost`) if a proxy is configured and no bypass is explicitly specified.
4. Linux utilities prefer lowercase proxy variables, whereas Python libraries often look for uppercase variations, creating inconsistency.
5. In [main.py](../../../slash_agent/main.py), `.env` variables are loaded after the terminal tools import and copy `os.environ`, meaning proxy configurations in `.env` are lost when launching subprocesses.

This change introduces automatic sanitization and bidirectional case-synchronization of proxy variables, making the agent robust to local proxy routing rules.

## What Changes

- Modify `slash_agent.main` initialization to run `.env` loading and proxy environment sanitization **before** importing `slash_agent.tools`, ensuring the tools' global state captures the correct variables.
- Introduce a sanitization routine that strips shell-style wildcards (`*` or `*.`) from proxy bypass environment variables (`no_proxy`, `NO_PROXY`) for compatibility with Python's HTTP clients.
- Automatically inject local default bypasses (`localhost`, `127.0.0.1`) into `no_proxy` and `NO_PROXY` when any HTTP/HTTPS proxy is configured, ensuring local LLM backends (like Ollama) are not routed through external proxies.
- Synchronize case variations (`http_proxy` ◄► `HTTP_PROXY`, `https_proxy` ◄► `HTTPS_PROXY`, `no_proxy` ◄► `NO_PROXY`) so they contain identical values, supporting both Linux shell tools and Python packages consistently.
- Patch [installer.sh](../../../bin/installer.sh) to explicitly bypass proxy routing during local Ollama service discovery.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `shell-agent`: Enforce proxy environment variable normalization, synchronization, and default local host bypasses for both the orchestrator process and child command executions.
- `simple-installer`: Bypass proxy handlers when probing local services during interactive configuration/installation.

## Impact

- **Affected Code:**
  - [slash_agent/main.py](../../../slash_agent/main.py): Import order and env sanitization logic.
  - [bin/installer.sh](../../../bin/installer.sh): Proxy bypass in python inline probe.
- **Dependencies:** None.
- **APIs:** None.
