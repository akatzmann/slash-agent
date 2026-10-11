"""Shell initialization and profile integration for slash-agent.

Provides multi-shell wrapper generation (Bash, Zsh, Ksh, Fish) and
idempotent shell profile installation re-using existing proven mechanisms.
"""

import os
import platform
from typing import Dict, Optional, Tuple

SUPPORTED_SHELLS = ("bash", "zsh", "fish", "ksh")


def detect_shell(env: Optional[Dict[str, str]] = None) -> str:
    """Detect the active shell type from environment variables."""
    if env is None:
        env = os.environ

    if env.get("ZSH_VERSION"):
        return "zsh"

    raw_shell = env.get("SHELL", "")
    shell_name = os.path.basename(raw_shell).lower()
    if shell_name in ("zsh", "fish", "ksh", "bash"):
        return shell_name
    elif shell_name == "mksh":
        return "ksh"

    return "bash"


def resolve_shell_profile(
    shell: str, home_dir: Optional[str] = None, os_type: Optional[str] = None
) -> str:
    """Resolve the default RC profile file for the target shell and OS."""
    if home_dir is None:
        home_dir = os.path.expanduser("~")
    if os_type is None:
        os_type = platform.system()

    if shell == "zsh":
        return os.path.join(home_dir, ".zshrc")
    elif shell == "fish":
        return os.path.join(home_dir, ".config", "fish", "config.fish")
    elif shell == "ksh":
        return os.path.join(home_dir, ".kshrc")
    elif shell == "bash":
        if os_type == "Darwin":
            bash_profile = os.path.join(home_dir, ".bash_profile")
            profile = os.path.join(home_dir, ".profile")
            if os.path.exists(bash_profile):
                return bash_profile
            elif os.path.exists(profile):
                return profile
            return bash_profile
        return os.path.join(home_dir, ".bashrc")

    return os.path.join(home_dir, ".bashrc")


def install_init_hook(
    shell: str, home_dir: Optional[str] = None, cmd_name: str = "agent"
) -> Tuple[bool, str]:
    """Idempotently install the initialization line into the target shell RC file."""
    rc_path = resolve_shell_profile(shell, home_dir=home_dir)
    parent_dir = os.path.dirname(rc_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    if not os.path.exists(rc_path):
        with open(rc_path, "w") as f:
            f.write("")

    if shell == "fish":
        if cmd_name == "agent":
            hook_line = "slash-agent init fish | source"
        else:
            hook_line = f"slash-agent init fish --cmd {cmd_name} | source"
    else:
        if cmd_name == "agent":
            hook_line = f'eval "$(slash-agent init {shell})"'
        else:
            hook_line = f'eval "$(slash-agent init {shell} --cmd {cmd_name})"'

    with open(rc_path, "r", errors="ignore") as f:
        content = f.read()

    if hook_line in content:
        return False, rc_path

    with open(rc_path, "a") as f:
        f.write(f"\n# slash-agent Integration\n{hook_line}\n")

    return True, rc_path


def generate_init_script(shell: str, cmd_name: str = "agent") -> str:
    """Generate sourceable shell initialization script for the given shell."""
    shell = shell.lower()
    if shell not in SUPPORTED_SHELLS:
        raise ValueError(
            f"Unsupported shell: '{shell}'. Supported shells: {', '.join(SUPPORTED_SHELLS)}"
        )

    if shell == "fish":
        return _generate_fish_script(cmd_name)
    else:
        return _generate_posix_script(shell, cmd_name)


def _generate_posix_script(shell: str, cmd: str) -> str:
    """Generate POSIX-compatible shell script for Bash, Zsh, or Ksh."""
    history_capture = f"""        if [ -n "$ZSH_VERSION" ]; then
            fc -ln -"$HIST_COMMANDS" | grep -v "{cmd}" > "$CONTEXT_FILE" 2>/dev/null
        else
            (
                set -o history 2>/dev/null
                history $((HIST_COMMANDS + 10)) 2>/dev/null | grep -v "{cmd}" | tail -n "$HIST_COMMANDS" | sed 's/^[ ]*[0-9]*[ ]*//' > "$CONTEXT_FILE"
            ) 2>/dev/null
        fi"""

    if shell == "ksh":
        fn_definitions = f"""function {cmd} {{
    _{cmd}_run "$@"
}}"""
    else:
        fn_definitions = f"""function /{cmd} {{
    _{cmd}_run "$@"
}}
function {cmd} {{
    _{cmd}_run "$@"
}}"""

    return f"""# Native LLM Agent Shell Integration ({shell})
function _{cmd}_run {{
    if [ "$1" = "--configure" ] || [ "$1" = "-c" ]; then
        if command -v slash-agent >/dev/null 2>&1; then
            slash-agent --configure
        fi
        return $?
    fi
    if [ "$1" = "--upgrade" ] || [ "$1" = "--update" ] || [ "$1" = "-u" ]; then
        if command -v slash-agent >/dev/null 2>&1; then
            slash-agent --update
        fi
        return $?
    fi

    local CONTEXT_FILE
    CONTEXT_FILE=$(mktemp "${{TMPDIR:-/tmp}}/agent_context.XXXXXX")
    local SYNC_FILE
    SYNC_FILE=$(mktemp "${{TMPDIR:-/tmp}}/agent_sync.XXXXXX")

    local TMUX_LINES=${{AGENT_TMUX_LINES:-50}}
    local HIST_COMMANDS=${{AGENT_HISTORY_COMMANDS:-20}}

    if [ -n "$TMUX" ]; then
        tmux capture-pane -p -S -"$TMUX_LINES" > "$CONTEXT_FILE" 2>/dev/null
    else
{history_capture}
    fi

    local ACTIVE_SHELL="{shell}"
    if [ -n "$ZSH_VERSION" ]; then
        ACTIVE_SHELL="zsh"
    elif [ -n "$KSH_VERSION" ]; then
        ACTIVE_SHELL="ksh"
    fi

    slash-agent \\
        --context-file "$CONTEXT_FILE" \\
        --sync-file "$SYNC_FILE" \\
        --shell "$ACTIVE_SHELL" \\
        "$@"

    if [ -s "$SYNC_FILE" ]; then
        source "$SYNC_FILE"
    fi

    rm -f "$CONTEXT_FILE" "$SYNC_FILE"
}}

{fn_definitions}
"""


def _generate_fish_script(cmd: str) -> str:
    """Generate Fish shell integration script."""
    return f"""# Native LLM Agent Fish Shell Integration
function {cmd} -d "Native LLM Agent Terminal Copilot"
    if test "$argv[1]" = "--configure" -o "$argv[1]" = "-c"
        if type -q slash-agent
            slash-agent --configure
        end
        return
    end
    if test "$argv[1]" = "--upgrade" -o "$argv[1]" = "--update" -o "$argv[1]" = "-u"
        if type -q slash-agent
            slash-agent --update
        end
        return
    end

    set -l CONTEXT_FILE (mktemp -t agent_context.XXXXXX)
    set -l SYNC_FILE (mktemp -t agent_sync.XXXXXX)

    set -l TMUX_LINES 50
    if set -q AGENT_TMUX_LINES
        set TMUX_LINES $AGENT_TMUX_LINES
    end

    set -l HIST_COMMANDS 20
    if set -q AGENT_HISTORY_COMMANDS
        set HIST_COMMANDS $AGENT_HISTORY_COMMANDS
    end

    if set -q TMUX
        tmux capture-pane -p -S -"$TMUX_LINES" > "$CONTEXT_FILE" 2>/dev/null
    else
        history | head -n "$HIST_COMMANDS" > "$CONTEXT_FILE" 2>/dev/null
    end

    slash-agent \\
        --context-file "$CONTEXT_FILE" \\
        --sync-file "$SYNC_FILE" \\
        --shell fish \\
        $argv

    if test -s "$SYNC_FILE"
        source "$SYNC_FILE"
    end

    rm -f "$CONTEXT_FILE" "$SYNC_FILE"
end

function /{cmd} -d "Native LLM Agent Terminal Copilot"
    {cmd} $argv
end
"""
