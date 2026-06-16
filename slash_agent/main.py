import asyncio
import argparse
import sys
import os
from ollama import AsyncClient
from py_agent_core.agent import Agent
from py_agent_core.backends.ollama import OllamaBackend
from slash_agent.tools import execute_command, session_state

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

# Load local .env config if present
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(repo_root, ".env"))

# Save starting environment for diff sync on exit (after loading .env)
STARTING_ENV = os.environ.copy()

def get_env_diff() -> str:
    """Computes the difference between starting env and current session state env,
    returning bash export statements.
    """
    diff_cmds = []
    
    # Check for changes or additions
    for k, v in session_state.env_vars.items():
        # Skip standard read-only or session-specific terminal vars
        if k in ('_', 'SHLVL', 'PWD', 'OLDPWD', 'HISTSIZE', 'HISTFILE'):
            continue
        if k not in STARTING_ENV or STARTING_ENV[k] != v:
            import shlex
            diff_cmds.append(f'export {k}={shlex.quote(v)}')
            
    # Check for removals
    for k in STARTING_ENV:
        if k not in session_state.env_vars:
            diff_cmds.append(f'unset {k}')
            
    return "\n".join(diff_cmds)

async def main_async():
    parser = argparse.ArgumentParser(description="Native LLM Agent Shell Integration")
    parser.add_argument("--context-file", type=str, help="File containing captured terminal history/context")
    parser.add_argument("--sync-file", type=str, help="Temp file to write environment sync commands for parent shell")
    parser.add_argument("-y", "--yes", action="store_true", help="Auto-confirm all commands")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Dry run simulation mode")
    parser.add_argument("prompt", nargs="*", help="The user prompt or task")
    
    args = parser.parse_args()
    
    # Configure session flags
    session_state.auto_confirm = args.yes
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
    if captured_context:
        full_prompt = (
            f"=== PRIMARY DIRECTIVE ===\n"
            f"You MUST accomplish the following task: {user_prompt}\n\n"
            f"=== CONTEXT INSTRUCTIONS ===\n"
            f"The terminal outputs and history below are provided strictly for background reference. "
            f"Do NOT try to fix errors found in this history unless the task above explicitly asks you to fix or diagnose them.\n\n"
            f"--- TERMINAL CONTEXT BACKGROUND ---\n"
            f"{captured_context}\n"
            f"-----------------------------------"
        )
    else:
        full_prompt = user_prompt
        
    # Retrieve model and endpoint configurations from environment variables
    endpoint = os.environ.get("AGENT_ENDPOINT", "http://127.0.0.1:11434")
    model = os.environ.get("AGENT_MODEL", "gemma4:e4b-it-qat")
    
    print(f"\033[1;30m[slash-agent] Initializing with model '{model}' at '{endpoint}'...\033[0m")
    
    try:
        backend = OllamaBackend(client=AsyncClient(host=endpoint), model=model)
    except Exception as e:
        print(f"\033[1;31m[Error] Failed to initialize Ollama backend:\033[0m {e}")
        sys.exit(1)
        
    system_prompt = (
        "You are an expert software engineer and shell automation agent.\n"
        "You help users directly in their terminal shell.\n"
        "To accomplish the user's task, you can execute shell commands using the `execute_command` tool.\n"
        "IMPORTANT RULES:\n"
        "1. Prefer non-interactive flags (e.g. `apt install -y` or `npx -y`) to avoid blocking. Do not run text editors like `nano` or `vim`.\n"
        "2. Do not attempt commands that are endless unless they have a timeout (e.g. do not run `tail -f` or raw `ping` without counts).\n"
        "3. Always check exit codes and stderr of your commands. If a command fails, debug it, explore the directories, read the files, and try an alternative approach.\n"
        "4. Your working directory and env variables are preserved statefully between tool executions.\n"
        "5. When you have finished the task, output a concise explanation detailing what you did and the outcomes."
    )
    
    agent = Agent(
        backend=backend,
        initial_state={
            "systemPrompt": system_prompt,
            "tools": [execute_command]
        }
    )
    
    # Run agent streaming prompt
    try:
        print(f"\033[1;32m[Agent Started Task]\033[0m")
        async for event in agent.prompt_stream(full_prompt):
            if event.type == "message_update":
                ev = getattr(event, "assistant_message_event", {})
                if ev.get("type") == "text_delta":
                    print(ev["delta"], end="", flush=True)
            elif event.type == "agent_end":
                print()
            elif event.type == "error":
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
                env_diff = get_env_diff()
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
