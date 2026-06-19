# Native LLM Agent Fish Shell Integration
# Sourcing this file exposes the '/agent' and 'agent' commands.

# Resolve the package root directory relative to this sourced script's location
set -l _SLASH_AGENT_ROOT (dirname (dirname (status filename)))

function agent -d "Native LLM Agent Terminal Copilot"
    set -l CONTEXT_FILE (mktemp -t agent_context.XXXXXX)
    set -l SYNC_FILE (mktemp -t agent_sync.XXXXXX)
    
    # 1. Capture recent terminal context
    set -l TMUX_LINES 50
    if set -q AGENT_TMUX_LINES
        set TMUX_LINES $AGENT_TMUX_LINES
    end
    
    set -l HIST_COMMANDS 20
    if set -q AGENT_HISTORY_COMMANDS
        set HIST_COMMANDS $AGENT_HISTORY_COMMANDS
    end
    
    if set -q TMUX
        # If running inside tmux, capture the pane scrollback
        tmux capture-pane -p -S -"$TMUX_LINES" > "$CONTEXT_FILE" 2>/dev/null
    else
        # Fallback: capture recent interactive command history from Fish
        history | head -n "$HIST_COMMANDS" > "$CONTEXT_FILE" 2>/dev/null
    end
    
    # 2. Invoke the Python Agent orchestrator passing --shell fish
    env PYTHONPATH="$_SLASH_AGENT_ROOT" \
    "$_SLASH_AGENT_ROOT/.venv/bin/python3" \
    -m slash_agent.main \
    --context-file "$CONTEXT_FILE" \
    --sync-file "$SYNC_FILE" \
    --shell fish \
    $argv
    
    # 3. Synchronize parent shell environment state (cd, set -gx)
    if test -s "$SYNC_FILE"
        source "$SYNC_FILE"
    end
    
    # 4. Cleanup temporary files
    rm -f "$CONTEXT_FILE" "$SYNC_FILE"
end

echo -e "\033[1;32m[slash-agent] Native integration active. Type 'agent <task>' to use.\033[0m"
if not set -q TMUX
    echo -e "\033[2;33m[slash-agent] Tip: Running inside tmux gives /agent richer context (live screen capture).\033[0m"
    echo -e "\033[2;33m               Start a session with: tmux\033[0m"
end
