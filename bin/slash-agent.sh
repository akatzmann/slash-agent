#!/bin/bash

# Native LLM Agent Shell Integration
# Sourcing this file exposes the '/agent' command.

# Resolve the package root directory relative to this sourced script's location
if [ -n "$ZSH_VERSION" ]; then
    _SLASH_AGENT_ROOT=$(cd -- "$(dirname -- "${(%):-%N}")" &> /dev/null && pwd)
elif [ -n "$KSH_VERSION" ] && [ -n "${.sh.file}" ]; then
    _SLASH_AGENT_ROOT=$(cd -- "$(dirname -- "${.sh.file}")" &> /dev/null && pwd)
elif [ -n "$BASH_SOURCE" ]; then
    _SLASH_AGENT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
else
    _SLASH_AGENT_ROOT=$(cd -- "$(dirname -- "$0")" &> /dev/null && pwd)
fi
_SLASH_AGENT_ROOT=$(dirname "$_SLASH_AGENT_ROOT")

function _agent_run {
    local CONTEXT_FILE
    CONTEXT_FILE=$(mktemp "${TMPDIR:-/tmp}/agent_context.XXXXXX")
    local SYNC_FILE
    SYNC_FILE=$(mktemp "${TMPDIR:-/tmp}/agent_sync.XXXXXX")
    
    # 1. Capture recent terminal context
    local TMUX_LINES=${AGENT_TMUX_LINES:-50}
    local HIST_COMMANDS=${AGENT_HISTORY_COMMANDS:-20}
    
    if [ -n "$TMUX" ]; then
        # If running inside tmux, capture the pane scrollback
        tmux capture-pane -p -S -"$TMUX_LINES" > "$CONTEXT_FILE" 2>/dev/null
    else
        # Fallback: capture recent interactive command history
        if [ -n "$ZSH_VERSION" ]; then
            # Zsh history capture
            fc -ln -"$HIST_COMMANDS" | grep -v "/agent" > "$CONTEXT_FILE" 2>/dev/null
        else
            # Bash/Ksh history capture
            (
                set -o history 2>/dev/null
                history $((HIST_COMMANDS + 10)) 2>/dev/null | grep -v "/agent" | tail -n "$HIST_COMMANDS" | sed 's/^[ ]*[0-9]*[ ]*//' > "$CONTEXT_FILE"
            ) 2>/dev/null
        fi
    fi
    
    # Detect active shell to pass to python orchestrator
    local ACTIVE_SHELL="bash"
    if [ -n "$ZSH_VERSION" ]; then
        ACTIVE_SHELL="zsh"
    elif [ -n "$KSH_VERSION" ]; then
        ACTIVE_SHELL="ksh"
    fi
    
    # 2. Invoke the Python Agent orchestrator
    # We add our agent shell root to PYTHONPATH and run using the local venv python3
    PYTHONPATH="$_SLASH_AGENT_ROOT" \
    "$_SLASH_AGENT_ROOT/.venv/bin/python3" \
    -m slash_agent.main \
    --context-file "$CONTEXT_FILE" \
    --sync-file "$SYNC_FILE" \
    --shell "$ACTIVE_SHELL" \
    "$@"
    
    # 3. Synchronize parent shell environment state (cd, exports)
    if [ -s "$SYNC_FILE" ]; then
        source "$SYNC_FILE"
    fi
    
    # 4. Cleanup temporary files
    rm -f "$CONTEXT_FILE" "$SYNC_FILE"
}

if [ -n "$KSH_VERSION" ]; then
    function agent {
        _agent_run "$@"
    }
else
    function /agent {
        _agent_run "$@"
    }
    function agent {
        _agent_run "$@"
    }
fi

echo -e "\033[1;32m[slash-agent] Native integration active. Type '/agent <task>' or 'agent <task>' to use.\033[0m"
if [ -z "$TMUX" ]; then
    echo -e "\033[2;33m[slash-agent] Tip: Running inside tmux gives /agent richer context (live screen capture).\033[0m"
    echo -e "\033[2;33m               Start a session with: tmux\033[0m"
fi

