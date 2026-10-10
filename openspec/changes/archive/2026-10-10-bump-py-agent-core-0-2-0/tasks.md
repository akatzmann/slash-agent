## 1. Dependencies & Engine

- [x] 1.1 Update `requirements.txt` to pin `py-agent-core` to `git+https://github.com/akatzmann/py-agent-core.git@v0.2.0`
- [x] 1.2 Verify `py-agent-core` 0.2.0 installation in `.venv`

## 2. Backend Defaults & Logic

- [x] 2.1 Update `slash_agent/main.py` default model fallback to `gpt-6.1-sol` for `azure_openai`
- [x] 2.2 Update `slash_agent/main.py` default model fallback to `gpt-6.1-sol` for `openai`

## 3. Configuration & Installer Templates

- [x] 3.1 Update `.env.template` model documentation to reference `gpt-6.1-sol` for `openai` and `azure_openai`
- [x] 3.2 Update `bin/installer.sh` default model prompt and seed values for `azure_openai` and `openai`
- [x] 3.3 Update `bin/installer.ps1` default model prompt and seed values for `azure_openai` and `openai`

## 4. Documentation

- [x] 4.1 Update `docs/documentation.md` backend and model tables to specify `gpt-6.1-sol`
- [x] 4.2 Update `README.md` to reference `gpt-6.1-sol`

## 5. Verification

- [x] 5.1 Run test suite to verify no regressions in unit tests
- [x] 5.2 Validate backend resolution in `slash_agent/main.py`
