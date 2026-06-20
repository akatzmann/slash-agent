## 1. Setup and Initialization Fix

- [x] 1.1 Restructure imports in `slash_agent/main.py` so that `load_dotenv` is defined and executed before importing `py_agent_core.agent` or `slash_agent.tools`.
- [x] 1.2 Implement the `sanitize_proxy_env()` function in `slash_agent/main.py` to synchronize casing, strip wildcards, and append default local bypasses.
- [x] 1.3 Invoke `sanitize_proxy_env()` in `slash_agent/main.py` immediately after `load_dotenv` is called.

## 2. Installer Proxy Bypass

- [x] 2.1 Modify `fetch_ollama_models()` in `bin/installer.sh` to build a custom `urllib.request` opener with an empty `ProxyHandler` when querying `127.0.0.1` or `localhost`.

## 3. Verification and Testing

- [x] 3.1 Create a temporary scratch test to verify that `sanitize_proxy_env()` correctly synchronizes casing, strips wildcards, and appends defaults.
- [x] 3.2 Verify that subprocess commands executed via the PTY bridge inherit the sanitized proxy environment variables.
- [x] 3.3 Verify that the local Ollama backend can be queried correctly in an environment with a global proxy configured.

