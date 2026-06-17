## 1. Flexible Backends Implementation

- [x] 1.1 Implement the `OpenAIBackend` class in `slash_agent/main.py` using standard `AsyncOpenAI`
- [x] 1.2 Update the initialization block in `slash_agent/main.py` to support dynamic loading of backends (`openai`, `ollama`, `azure_openai`, `dummy`)
- [x] 1.3 Update the installer script `bin/installer.sh` to support interactive selection of backend type and store it in `.env`

## 2. Verification

- [x] 2.1 Verify default OpenAI backend initializes correctly
- [x] 2.2 Verify Ollama backend configuration still behaves as expected
- [x] 2.3 Verify Dummy backend can be selected and runs successfully
