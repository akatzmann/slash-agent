## Context

The current Python agent orchestrator starts a subprocess with its current environment state, which is tracked globally via the `session_state` import inside `slash_agent.tools`. 
When running behind proxy servers, connections to the LLM backend (like external OpenAI API or local Ollama API) are routed through proxies. However, local backends should bypass the proxy. Because `httpx` (the HTTP library powering the backend SDKs) does not support shell-style wildcards (e.g. `*.local`) or CIDR notation in `no_proxy`/`NO_PROXY`, and does not automatically bypass local hosts, local connections will fail and attempt to go through corporate proxies. 
Additionally, because `.env` variables are loaded after `tools` initializes its environment cache, variables defined in `.env` (including proxy settings) are omitted from subshell command runs.

## Goals / Non-Goals

**Goals:**
- Fix the startup initialization sequence in `main.py` to ensure that `.env` loading and environment sanitization occur before tools import.
- Perform automated sanitization of proxy environment variables (`http_proxy`, `https_proxy`, `no_proxy`, and their uppercase variations) at agent startup.
- Strip wildcards (`*`, `*.`) from proxy bypass settings to guarantee compatibility with `httpx`.
- Synchronize casing variations (lowercase/uppercase) of proxy environment variables to satisfy both Linux shell requirements and Python library conventions.
- Inject default local bypasses (`localhost`, `127.0.0.1`) when a proxy is set.
- Ensure the `installer.sh` Ollama verification bypasses system proxies when querying `127.0.0.1` or `localhost`.

**Non-Goals:**
- Adding general CIDR parsing/subnet expansion logic to `no_proxy` (as expanding large CIDR subnets like `/8` would crash the environment block size limits; users must list explicit IPs for custom internal subnets).
- Modifying proxy transport mounts inside the underlying third-party SDKs (`openai` / `ollama`) directly.

## Decisions

### Decision 1: Shift Module Import Sequence in `main.py`
- **Choice:** Move `.env` loading and proxy sanitization to the top of `main.py` before importing `slash_agent.tools`.
- **Rationale:** `slash_agent.tools` instantiates a global `session_state` singleton which copies `os.environ` inside its constructor. By loading `.env` and sanitizing the environment beforehand, `session_state` is guaranteed to have the correct proxy environment variables and will propagate them to any shell commands run by the agent.
- **Alternatives Considered:** Updating `session_state.env_vars` explicitly inside `main.py` after loading `.env`. This was rejected because it introduces double-maintenance of the environment copy logic and creates potential drift between `os.environ` and `session_state.env_vars`.

### Decision 2: Bidirectional Casing Synchronization of Proxy Variables
- **Choice:** Synchronize both lowercase and uppercase variations (`http_proxy` ◄► `HTTP_PROXY`, etc.) in `os.environ`.
- **Rationale:** Linux-native CLI tools (like `curl` or Go-based utilities) strictly prefer lowercase proxy variables, whereas Python libraries typically query uppercase versions. Writing identical sanitized strings to both ensures tool-agnostic compatibility under subshell executions.

### Decision 3: Use urllib ProxyHandler for Local Probe in Installer
- **Choice:** Build a custom urllib opener with an empty `ProxyHandler` during local probes in `installer.sh` to bypass proxy configuration.
- **Rationale:** Querying `127.0.0.1` or `localhost` to check if Ollama is running should never route through a corporate proxy. Overriding the handler inside python's inline execution bypasses any active proxy variables cleanly without altering the host's actual environment state.

## Risks / Trade-offs

- **[Risk]** Sanitized environment variables could cause discrepancies if parent shell variables are overwritten.
  - *Mitigation:* `main.py` uses `get_env_diff()` to sync modifications back to the parent shell. Since the parent shell is synced using difference mapping, and we only synchronize existing proxy variables, we will not write diff commands for unchanged proxy variables.
- **[Risk]** CIDR subnets in `no_proxy` (e.g. `10.0.0.0/8`) remain unsupported by `httpx`.
  - *Mitigation:* This is documented in the design non-goals. Users must specify exact IP addresses for internal hosts if they wish to bypass proxies in `httpx`-based clients.
