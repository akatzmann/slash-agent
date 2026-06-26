import asyncio
import argparse
import sys
import os
import re

def get_config_path() -> str:
    """Resolve the configuration file path, respecting overrides and XDG specs."""
    custom_path = os.environ.get("SLASH_AGENT_CONFIG_FILE")
    if custom_path:
        return os.path.abspath(custom_path)

    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        config_dir = os.path.join(xdg_config, "slash-agent")
    else:
        home = os.environ.get("HOME")
        if home:
            config_dir = os.path.join(home, ".config", "slash-agent")
        else:
            # Fallback to repo root if HOME is undefined
            repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(repo_root, ".env")

    return os.path.join(config_dir, "env")

def load_dotenv(env_path: str):
    """Manually parse .env file to load variables into os.environ."""
    if os.path.exists(env_path):
        with open(env_path, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v

def migrate_legacy_config(repo_root: str, target_path: str):
    """Migrate legacy repo-root .env to target_path if legacy exists (and merge if both exist)."""
    legacy_path = os.path.join(repo_root, ".env")
    if not os.path.exists(legacy_path):
        return

    # Check if legacy path is actually same as target path (prevent self-loop)
    if os.path.abspath(legacy_path) == os.path.abspath(target_path):
        return

    # Read legacy env
    legacy_vars = {}
    with open(legacy_path, "r", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                legacy_vars[k] = v

    # If legacy is empty, just delete it
    if not legacy_vars:
        try:
            os.remove(legacy_path)
        except Exception:
            pass
        return

    # Read existing target env if it exists
    target_vars = {}
    if os.path.exists(target_path):
        with open(target_path, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    target_vars[k] = v

    # Merge: keep existing target vars, fill in missing from legacy
    merged = False
    for k, v in legacy_vars.items():
        if k not in target_vars:
            target_vars[k] = v
            merged = True

    # Save to target path
    if merged or not os.path.exists(target_path):
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        try:
            fd = os.open(target_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as f:
                for k, v in target_vars.items():
                    f.write(f'{k}="{v}"\n')
        except Exception:
            with open(target_path, "w") as f:
                for k, v in target_vars.items():
                    f.write(f'{k}="{v}"\n')
            try:
                os.chmod(target_path, 0o600)
            except Exception:
                pass

    # Delete legacy .env
    try:
        os.remove(legacy_path)
    except Exception:
        pass

# Migrate and load configuration
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = get_config_path()
migrate_legacy_config(repo_root, config_path)
load_dotenv(config_path)


def sanitize_proxy_env():
    """Sanitize proxy environment variables for compatibility and sync casing."""
    # 1. Synchronize proxy endpoints across both cases
    for upper, lower in (("HTTP_PROXY", "http_proxy"), ("HTTPS_PROXY", "https_proxy")):
        val = os.environ.get(lower) or os.environ.get(upper)
        if val:
            os.environ[lower] = val
            os.environ[upper] = val

    # 2. Extract bypass values from whichever case is defined
    raw_no_proxy = os.environ.get("no_proxy") or os.environ.get("NO_PROXY") or ""
    
    entries = []
    if raw_no_proxy:
        for entry in re.split(r'[\s,]+', raw_no_proxy):
            entry = entry.strip()
            if not entry:
                continue
            # Strip wildcards (*.domain.com -> domain.com) since httpx doesn't support them
            if entry.startswith("*."):
                entry = entry[2:]
            elif entry.startswith("*"):
                entry = entry[1:]
            entries.append(entry)
            
    # 3. If a proxy is configured, ensure localhost/127.0.0.1 bypasses are present
    has_proxy = any(os.environ.get(k) for k in ("http_proxy", "https_proxy"))
    if has_proxy:
        if "localhost" not in entries:
            entries.append("localhost")
        if "127.0.0.1" not in entries:
            entries.append("127.0.0.1")
            
    # 4. Write back sanitized values to both lowercase and uppercase keys
    if entries:
        no_proxy_str = ",".join(entries)
        os.environ["no_proxy"] = no_proxy_str
        os.environ["NO_PROXY"] = no_proxy_str

sanitize_proxy_env()

# Save starting environment for diff sync on exit (after loading .env and sanitization)
STARTING_ENV = os.environ.copy()

def parse_skill_metadata(skill_file: str, fallback_name: str) -> tuple[str, str]:
    """Parse YAML frontmatter of SKILL.md using a regex-based parser, falling back gracefully on error."""
    name = fallback_name
    desc = f"Custom skill from {fallback_name}"
    
    try:
        with open(skill_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        # Match YAML frontmatter between --- and --- at the start of the file
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            yaml_block = match.group(1)
            for line in yaml_block.splitlines():
                # Skip indented lines (nested keys)
                if line.startswith(" ") or line.startswith("\t"):
                    continue
                line_stripped = line.strip()
                if not line_stripped or line_stripped.startswith("#"):
                    continue
                if ":" in line_stripped:
                    k, v = line_stripped.split(":", 1)
                    k = k.strip().lower()
                    v = v.strip().strip("'\"")
                    if k == "name" and v:
                        name = v
                    elif k == "description" and v:
                        desc = v
    except Exception:
        pass
        
    return name, desc

GLOBAL_SKILLS_DIRS = [
    "~/.config/slash-agent/skills",
    "~/.claude/skills",
    "~/.copilot/skills",
    "~/.gemini/config/skills",
]

LOCAL_SKILLS_DIRS = [
    ".agent/skills",
    ".claude/skills",
    ".github/skills"
]

def find_project_root(local_dirs: list[str] = LOCAL_SKILLS_DIRS) -> str:
    """Traverse upwards from the current working directory to find a project root."""
    current = os.getcwd()
    while True:
        # Check if any standard project markers or local skill dirs exist here
        if os.path.isdir(os.path.join(current, ".git")):
            return current
        for local_dir in local_dirs:
            if os.path.isdir(os.path.join(current, local_dir)):
                return current
        # Move up to parent
        parent = os.path.dirname(current)
        if parent == current: # Reached root '/'
            break
        current = parent
    return os.getcwd() # Fallback to CWD

def discover_skills() -> list[dict[str, str]]:
    """Scan standard global and project-local paths for SKILL.md files and return deduplicated entries."""
    dirs_to_scan = []
    # Scan global paths first, so local paths override on name collisions
    for path in GLOBAL_SKILLS_DIRS:
        abs_path = os.path.abspath(os.path.expanduser(path))
        dirs_to_scan.append((abs_path, "global"))
        
    project_root = find_project_root(LOCAL_SKILLS_DIRS)
    for path in LOCAL_SKILLS_DIRS:
        abs_path = os.path.abspath(os.path.join(project_root, path))
        dirs_to_scan.append((abs_path, "local"))
        
    skills = {}
    
    for scan_dir, source in dirs_to_scan:
        if not os.path.isdir(scan_dir):
            continue
        try:
            for item in os.listdir(scan_dir):
                item_path = os.path.join(scan_dir, item)
                if os.path.isdir(item_path):
                    skill_file = os.path.join(item_path, "SKILL.md")
                    if os.path.isfile(skill_file):
                        name, desc = parse_skill_metadata(skill_file, item)
                        # Project-local overrides global due to dict update order
                        skills[name] = {
                            "name": name,
                            "description": desc,
                            "path": skill_file,
                            "source": source
                        }
        except Exception:
            pass
            
    return list(skills.values())

def build_skills_prompt(skills: list[dict[str, str]]) -> str:
    """Construct the system prompt block for available agent skills."""
    if not skills:
        return ""
        
    prompt_lines = [
        "\n# Available Agent Skills",
        "The following specialized skills are available to you. If a task can be addressed by one of these skills, you MUST prioritize using the skill and its instructions over generic tool execution (like running custom shell commands or writing ad-hoc scripts). If a task requires one of these skills, you MUST read its detailed instructions first using the `read_skill_instructions` tool, then follow the steps exactly:\n"
    ]
    for skill in skills:
        prompt_lines.append(f"* **{skill['name']}**: {skill['description']}")
        prompt_lines.append(f"  - Instructions path: {skill['path']}\n")
        
    return "\n".join(prompt_lines)

# Import agent and tools (ensuring tools capture the sanitized os.environ in session_state)
from py_agent_core.agent import Agent
from slash_agent.tools import execute_command, request_user_input, read_skill_instructions, read_file, write_file, edit_file, session_state

def get_env_diff(shell: str = "bash") -> str:
    """Computes the difference between starting env and current session state env,
    returning shell-compatible environment update statements.
    """
    diff_cmds = []
    
    # Check for changes or additions
    for k, v in session_state.env_vars.items():
        # Skip standard read-only or session-specific terminal vars
        if k in ('_', 'SHLVL', 'PWD', 'OLDPWD', 'HISTSIZE', 'HISTFILE'):
            continue
        if k not in STARTING_ENV or STARTING_ENV[k] != v:
            import shlex
            if shell == "fish":
                diff_cmds.append(f'set -gx {k} {shlex.quote(v)}')
            else:
                diff_cmds.append(f'export {k}={shlex.quote(v)}')
            
    # Check for removals
    for k in STARTING_ENV:
        if k not in session_state.env_vars:
            if shell == "fish":
                diff_cmds.append(f'set -e {k}')
            else:
                diff_cmds.append(f'unset {k}')
            
    return "\n".join(diff_cmds)

async def main_async():
    parser = argparse.ArgumentParser(description="Native LLM Agent Shell Integration")
    parser.add_argument("--context-file", type=str, help="File containing captured terminal history/context")
    parser.add_argument("--sync-file", type=str, help="Temp file to write environment sync commands for parent shell")
    parser.add_argument("--shell", type=str, default="bash", choices=["bash", "zsh", "ksh", "fish"], help="The active host shell type")
    parser.add_argument("-y", "--yes", action="store_true", help="Auto-confirm all commands")
    parser.add_argument("--unsafe-yes", action="store_true", help="Auto-confirm even critical/dangerous commands")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Dry run simulation mode")
    parser.add_argument("prompt", nargs="*", help="The user prompt or task")
    
    args = parser.parse_args()
    
    # Configure session flags
    session_state.auto_confirm = args.yes or args.unsafe_yes
    session_state.unsafe_confirm = args.unsafe_yes
    session_state.dry_run = args.dry_run
    
    # Read captured context
    captured_context = ""
    if args.context_file and os.path.exists(args.context_file):
        try:
            with open(args.context_file, "r", errors="ignore") as f:
                captured_context = f.read().strip()
        except Exception as e:
            print(f"\033[1;31m[Error] Failed to read context file:\033[0m {e}")
            
    # Reconstruct prompt
    user_prompt = " ".join(args.prompt).strip()
    if not user_prompt:
        if captured_context:
            user_prompt = "Diagnose the recent terminal screen outputs and command history to find and fix any errors."
        else:
            parser.print_help()
            sys.exit(0)
            
    # Add captured terminal history as system context if present
    env_context = (
        f"# Environment Context\n"
        f"- Active User: {os.getlogin()} (UID: {os.getuid()})\n"
        f"- Current Working Directory: {os.getcwd()}\n\n"
    )
    if captured_context:
        full_prompt = (
            f"{env_context}"
            f"# Primary Directive\n"
            f"You MUST accomplish the following task: {user_prompt}\n\n"
            f"# Context Instructions\n"
            f"The terminal outputs and history below are provided strictly for background reference. "
            f"Do NOT attempt to fix errors found in this history unless the task above explicitly asks you to fix or diagnose them.\n\n"
            f"# Terminal Context Background\n"
            f"```text\n"
            f"{captured_context}\n"
            f"```"
        )
    else:
        full_prompt = (
            f"{env_context}"
            f"# Primary Directive\n"
            f"You MUST accomplish the following task: {user_prompt}"
        )
        
    # Retrieve model, endpoint, backend, and behavior configurations from environment variables
    backend_type = os.environ.get("AGENT_BACKEND", "ollama").lower()
    endpoint = os.environ.get("AGENT_ENDPOINT", "")
    model = os.environ.get("AGENT_MODEL", "")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    thinking_level = os.environ.get("AGENT_THINKING_LEVEL", "off").lower()

    # Parse sampling parameters
    temp_env = os.environ.get("AGENT_TEMPERATURE", "").strip()
    top_p_env = os.environ.get("AGENT_TOP_P", "").strip()
    
    temperature = None
    if temp_env:
        try:
            temperature = float(temp_env)
        except ValueError:
            print(f"\033[1;33m[Warning] Invalid AGENT_TEMPERATURE '{temp_env}'. Ignoring.\033[0m")
            
    top_p = None
    if top_p_env:
        try:
            top_p = float(top_p_env)
        except ValueError:
            print(f"\033[1;33m[Warning] Invalid AGENT_TOP_P '{top_p_env}'. Ignoring.\033[0m")

    print(f"\033[1;34m[slash-agent] Using backend '{backend_type}'...\033[0m")

    try:
        if backend_type == "openai":
            from openai import AsyncOpenAI
            from py_agent_core.backends.openai import OpenAIBackend
            resolved_model = model or "gpt-5.4-nano"
            client_kwargs = {}
            if endpoint:
                client_kwargs["base_url"] = endpoint
            if api_key:
                client_kwargs["api_key"] = api_key
            client = AsyncOpenAI(**client_kwargs)
            backend = OpenAIBackend(client=client, model=resolved_model, temperature=temperature, top_p=top_p)
            print(f"\033[1;34m[slash-agent] Model '{resolved_model}' via OpenAI-compatible endpoint.\033[0m")

        elif backend_type == "ollama":
            from ollama import AsyncClient
            from py_agent_core.backends.ollama import OllamaBackend
            resolved_endpoint = endpoint or "http://127.0.0.1:11434"
            resolved_model = model or "gemma4:latest"
            backend = OllamaBackend(client=AsyncClient(host=resolved_endpoint), model=resolved_model, temperature=temperature, top_p=top_p)
            print(f"\033[1;34m[slash-agent] Model '{resolved_model}' at '{resolved_endpoint}' via Ollama.\033[0m")

        elif backend_type == "azure_openai":
            from openai import AsyncAzureOpenAI
            from py_agent_core.backends.azure_openai import AzureOpenAIBackend
            azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY", api_key)
            azure_api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
            resolved_model = model or "gpt-5.4-nano"
            client = AsyncAzureOpenAI(
                api_key=azure_api_key,
                api_version=azure_api_version,
                azure_endpoint=endpoint,
            )
            backend = AzureOpenAIBackend(client=client, model=resolved_model, temperature=temperature, top_p=top_p)
            print(f"\033[1;34m[slash-agent] Model '{resolved_model}' via Azure OpenAI.\033[0m")

        elif backend_type == "dummy":
            from py_agent_core.backends.dummy import DummyBackend
            backend = DummyBackend()
            print(f"\033[1;34m[slash-agent] Running in offline dummy mode.\033[0m")

        else:
            print(f"\033[1;31m[Error] Unknown backend '{backend_type}'. Valid options: openai, ollama, azure_openai, dummy.\033[0m")
            sys.exit(1)

    except Exception as e:
        print(f"\033[1;31m[Error] Failed to initialize backend '{backend_type}':\033[0m {e}")
        sys.exit(1)
        
    system_prompt = (
        "# Role & Identity\n"
        "You are an expert software engineer and shell automation agent helping users directly in their terminal shell.\n"
        "\n"
        "# Operational Guidelines\n"
        "1. **Command Execution**:\n"
        "   - Prefer non-interactive flags (e.g., `-y`, `-m`) to avoid blocking standard input.\n"
        "   - Do NOT run interactive text editors (e.g., `nano`, `vim`).\n"
        "   - Do NOT run endless commands without limits/timeouts (e.g., use `ping -c 4`, not raw `ping`; avoid `tail -f`).\n"
        "2. **Error Recovery**:\n"
        "   - Inspect exit codes and stderr of execution outputs. If a command fails, explore the workspace, view relevant files, and resolve the issue with an alternative command.\n"
        "3. **Completion Format**:\n"
        "   - Upon finishing, output a concise markdown summary explaining your actions and outcomes.\n"
        "4. **File Operations**:\n"
        "   - You MUST use the native file tools (`read_file`, `write_file`, `edit_file`) instead of shell commands (like `cat`, `tee`, `echo >>`, `sed`, etc.) for reading, writing, and editing files.\n"
        "   - All file paths supplied to file tools MUST be absolute paths.\n"
        "   - Prefer using `edit_file` over `write_file` when making targeted modifications to existing files to minimize overwrite risk.\n"
        "5. **Interacting with the User**:\n"
        "   - If you need to ask the user a question, clarify a task, or request additional input, you MUST use the `request_user_input` tool. Do NOT simply output a question in your text response, as this will cause the execution session to terminate immediately without prompting the user."
    )
    
    # Scan and append agent skills context
    skills = discover_skills()
    skills_prompt = build_skills_prompt(skills)
    system_prompt += skills_prompt
    
    agent = Agent(
        backend=backend,
        initial_state={
            "systemPrompt": system_prompt,
            "tools": [execute_command, request_user_input, read_skill_instructions, read_file, write_file, edit_file],
            "thinkingLevel": thinking_level
        }
    )
    
    # Run agent streaming prompt
    try:
        print(f"\033[1;32m[Agent Started Task]\033[0m")
        is_thinking = False
        async for event in agent.prompt_stream(full_prompt):
            if event.type == "message_update":
                ev = getattr(event, "assistant_message_event", {})
                if ev.get("type") == "thinking_delta":
                    if not is_thinking:
                        print("\n\033[1;30m[Thinking...]\033[0m\n\033[3;90m", end="", flush=True)
                        is_thinking = True
                    print(ev["delta"], end="", flush=True)
                elif ev.get("type") == "text_delta":
                    if is_thinking:
                        print("\033[0m\n\n\033[1;32m[Agent Response]\033[0m\n", end="", flush=True)
                        is_thinking = False
                    print(ev["delta"], end="", flush=True)
            elif event.type == "agent_end":
                if is_thinking:
                    print("\033[0m")
                print()
            elif event.type == "error":
                if is_thinking:
                    print("\033[0m")
                print(f"\n\033[1;31m[Agent Error]:\033[0m {getattr(event, 'content', 'Unknown error occurred')}")
    except KeyboardInterrupt:
        print("\n\033[1;31m[Agent Interrupted]\033[0m")
    except Exception as e:
        print(f"\n\033[1;31m[Agent Crash]:\033[0m {e}")
    finally:
        # Write state sync commands back to the parent shell
        if args.sync_file:
            try:
                sync_cmds = []
                # Directory sync
                if session_state.cwd != os.getcwd():
                    sync_cmds.append(f'cd "{session_state.cwd}"')
                
                # Env diff sync
                env_diff = get_env_diff(args.shell)
                if env_diff:
                    sync_cmds.append(env_diff)
                    
                if sync_cmds:
                    with open(args.sync_file, "w") as f:
                        f.write("\n".join(sync_cmds) + "\n")
            except Exception as e:
                # Silently fail or warn
                pass

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
