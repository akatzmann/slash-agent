## 1. Environment Template Configuration

- [x] 1.1 Add `AGENT_TEMPERATURE` and `AGENT_TOP_P` placeholders to `.env.template` with explanatory comments.
- [x] 1.2 Update README.md and docs/documentation.md to document AGENT_TEMPERATURE and AGENT_TOP_P.
- [x] 1.3 Refine reasoning model wording in comments, documentation, and OpenSpec artifacts to specify OpenAI o-series models.

## 2. Core Python Backend Integration

- [x] 2.1 Parse `AGENT_TEMPERATURE` and `AGENT_TOP_P` environment variables as float or `None` in `slash_agent/main.py`.
- [x] 2.2 Forward the parsed `temperature` and `top_p` arguments to `OpenAIBackend`, `OllamaBackend`, and `AzureOpenAIBackend` constructor calls in `slash_agent/main.py`.

## 3. Installer and Configuration Integration

- [x] 3.1 Update the missing-key verification loop in `bin/installer.sh` to include `AGENT_TEMPERATURE` and `AGENT_TOP_P` as empty string placeholders.
- [x] 3.2 Update the configuration file saving block in `bin/installer.sh` to write `AGENT_TEMPERATURE` and `AGENT_TOP_P` settings.

## 4. Manual Verification

- [x] 4.1 Run the installer script in configure mode (`/agent --configure`) and verify that `AGENT_TEMPERATURE` and `AGENT_TOP_P` are appended to the configuration file.
- [x] 4.2 Verify the agent runs without errors when `AGENT_TEMPERATURE` and `AGENT_TOP_P` are unset or set.
