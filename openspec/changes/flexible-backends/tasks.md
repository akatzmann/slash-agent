## 1. Flexible Backends Implementation

- [x] 1.1 Implement the `OpenAIBackend` class in `slash_agent/main.py` using standard `AsyncOpenAI`
- [x] 1.2 Update the initialization block in `slash_agent/main.py` to support dynamic loading of backends (`openai`, `ollama`, `azure_openai`, `dummy`)
- [x] 1.3 Update the installer script `bin/installer.sh` to support interactive selection of backend type and store it in `.env`
- [x] 1.4 Create `.env.template` in the project root with examples of all configuration variables
- [x] 1.5 Update `bin/installer.sh` to safely update/amend existing `.env` files with new configuration keys on script updates
- [x] 1.6 Implement a numbered option menu for OpenAI models in `bin/installer.sh`
- [x] 1.7 Add a pip uninstall step for `py-agent-core` in update mode to bypass cache and force update from git

## 2. Documentation

- [x] 2.1 Update `README.md` to briefly explain multi-backend support and list new variables in the environment configuration section
- [x] 2.2 Update `docs/documentation.md` architecture diagram and description, and update the environment variable section

## 3. Verification

- [x] 3.1 Verify default OpenAI backend initializes correctly
- [x] 3.2 Verify Ollama backend configuration still behaves as expected
- [x] 3.3 Verify Dummy backend can be selected and runs successfully
- [ ] 3.4 Verify installer `.env` upgrade/migration logic correctly infers `ollama` backend from port 11434 and appends missing variables
- [ ] 3.5 Verify the OpenAI model selection menu functions correctly during installer run
- [ ] 3.6 Verify that updating forces `py-agent-core` to be reinstalled from Git


