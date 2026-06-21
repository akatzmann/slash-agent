## Context

The installer configuration wizard in `bin/installer.sh` allows users to configure the backend, endpoint, model, etc. However, the existing `AGENT_ENDPOINT` and `AGENT_MODEL` values loaded from `.env` are reset to empty strings on lines 212 and 213, right before the interactive prompt selection begins. This wipes out the defaults even if the user retains their current backend.

## Goals / Non-Goals

**Goals:**
- Preserve existing `AGENT_ENDPOINT` and `AGENT_MODEL` defaults when running the configuration wizard without switching the backend.
- Clear those variables only when the user is changing to a different backend, so they get the default settings for the new backend.

**Non-Goals:**
- We are not changing how the `.env` values are written.
- We are not modifying the logic for other backends (like Ollama or OpenAI) except for keeping their defaults when configured.

## Decisions

- **Conditional Clearing**: Identify the chosen backend mapping from the `BACKEND_CHOICE` integer, and compare it with the sourced `AGENT_BACKEND` string.
- **Implementation**:
  ```bash
  CHOSEN_BACKEND=""
  if [ "$BACKEND_CHOICE" = "1" ]; then CHOSEN_BACKEND="openai"
  elif [ "$BACKEND_CHOICE" = "2" ]; then CHOSEN_BACKEND="ollama"
  elif [ "$BACKEND_CHOICE" = "3" ]; then CHOSEN_BACKEND="azure_openai"
  elif [ "$BACKEND_CHOICE" = "4" ]; then CHOSEN_BACKEND="dummy"
  fi

  if [ "$CHOSEN_BACKEND" != "$AGENT_BACKEND" ]; then
      AGENT_ENDPOINT=""
      AGENT_MODEL=""
  fi
  AGENT_BACKEND="$CHOSEN_BACKEND"
  ```
  This is chosen over unconditionally keeping the old defaults to prevent leaking cross-backend configurations (e.g. an Azure OpenAI URL leaking into the Ollama endpoint prompt).

## Risks / Trade-offs

- **Risk**: User selects the same backend but wanted to reset to defaults.
- **Mitigation**: The prompt shows the previous configuration as the default in brackets. If they want to change it, they can simply type the new value (or leave it empty/backspace it) as they see fit.
