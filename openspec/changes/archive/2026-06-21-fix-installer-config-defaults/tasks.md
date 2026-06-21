## 1. Implementation

- [x] 1.1 Map user's backend selection to string representation in `bin/installer.sh`
- [x] 1.2 Clear `AGENT_ENDPOINT` and `AGENT_MODEL` variables only if the chosen backend is different from the currently configured backend `AGENT_BACKEND`
- [x] 1.3 Assign the chosen backend string back to `AGENT_BACKEND`

## 2. Verification

- [x] 2.1 Set up a dummy `.env` configuration containing dummy endpoint and model for `azure_openai` backend
- [x] 2.2 Run `bin/installer.sh --configure` and select `3` (Azure OpenAI)
- [x] 2.3 Verify that the dummy endpoint and model are presented as default options in the prompts
- [x] 2.4 Verify that pressing Enter without typing inputs preserves these values in the generated `.env` file
