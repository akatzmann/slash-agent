#!/bin/bash

# Native LLM Agent Shell Integration
# Sourcing this file exposes the '/agent' command.

# Resolve the package root directory relative to this sourced script's location
_SLASH_AGENT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
_SLASH_AGENT_ROOT=$(dirname "$_SLASH_AGENT_ROOT")

function /agent {
    local CONTEXT_FILE
    CONTEXT_FILE=$(mktemp -t agent_context.XXXXXX)
    local SYNC_FILE
    SYNC_FILE=$(mktemp -t agent_sync.XXXXXX)
    
    # 1. Capture recent terminal context
    local TMUX_LINES=${AGENT_TMUX_LINES:-50}
    local HIST_COMMANDS=${AGENT_HISTORY_COMMANDS:-20}
    
    if [ -n "$TMUX" ]; then
        # If running inside tmux, capture the pane scrollback
        tmux capture-pane -p -S -"$TMUX_LINES" > "$CONTEXT_FILE" 2>/dev/null
    else
        # Fallback: capture recent interactive command history
        # We temporarily ensure history is enabled, fetch recent commands, and clean line prefixes
        (
            set -o history 2>/dev/null
            history $((HIST_COMMANDS + 10)) 2>/dev/null | grep -v "/agent" | tail -n "$HIST_COMMANDS" | sed 's/^[ ]*[0-9]*[ ]*//' > "$CONTEXT_FILE"
        ) 2>/dev/null
    fi
    
    # 2. Invoke the Python Agent orchestrator
    # We add our agent shell root to PYTHONPATH and run using the local venv python3
    PYTHONPATH="$_SLASH_AGENT_ROOT" \
    "$_SLASH_AGENT_ROOT/.venv/bin/python3" \
    -m slash_agent.main \
    --context-file "$CONTEXT_FILE" \
    --sync-file "$SYNC_FILE" \
    "$@"
    
    # 3. Synchronize parent shell environment state (cd, exports)
    if [ -s "$SYNC_FILE" ]; then
        source "$SYNC_FILE"
    fi
    
    # 4. Cleanup temporary files
    rm -f "$CONTEXT_FILE" "$SYNC_FILE"
}

echo -e "\033[1;32m[slash-agent] Native integration active. Type '/agent <task>' to use.\033[0m"
if [ -z "$TMUX" ]; then
    echo -e "\033[2;33m[slash-agent] Tip: Running inside tmux gives /agent richer context (live screen capture).\033[0m"
    echo -e "\033[2;33m               Start a session with: tmux\033[0m"
fi

