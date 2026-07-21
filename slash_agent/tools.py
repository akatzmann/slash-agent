import os
import sys
import re
import asyncio
import signal
import struct
import time
import difflib
from typing import Dict, Any, Tuple
from py_agent_core.tool import tool

# Conditional POSIX-only imports
if sys.platform != 'win32':
    import select
    import pty
    import termios
    import tty
    import fcntl
else:
    # Placeholders/mocks for type hints or simple fallback checks if needed
    pass


# Regex to strip ANSI color and formatting codes
ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

class ShellState:
    """State tracker for the active agent shell session."""
    def __init__(self):
        self.cwd = os.getcwd()
        self.initial_cwd = os.getcwd()
        self.env_vars = os.environ.copy()
        self.dry_run = False
        self.auto_confirm = False
        self.unsafe_confirm = False

# Global session state singleton
session_state = ShellState()

SENSITIVE_READ_PATHS = [
    "/etc/shadow", "/etc/passwd", "/etc/sudoers", "/etc/sudoers.d/",
    "/etc/ssh/",          # host private keys
    "/.ssh/",             # user private keys (~/.ssh/ after realpath)
    "/.gnupg/",           # GPG keys
    "/proc/",             # kernel/process interfaces
    "/sys/",              # kernel sysfs
    "/dev/",              # raw devices
    "/.aws/credentials", "/.aws/config",
    "/.config/gcloud/",
    "/.kube/config",
]

SENSITIVE_WRITE_PATHS = [
    *SENSITIVE_READ_PATHS,
    "/etc/",              # any system config
    "/usr/",              # system binaries/libraries
    "/bin/", "/sbin/", "/lib/", "/lib64/",
    "/boot/",             # kernel images
]

# Dynamically append Windows-specific sensitive files/folders on Windows hosts
if sys.platform == 'win32':
    sys_root = os.environ.get('SystemRoot', 'C:\\Windows').replace('\\', '/').lower()
    SENSITIVE_READ_PATHS.extend([
        f"{sys_root}/system32/config/sam",
        f"{sys_root}/system32/config/security",
        f"{sys_root}/system32/config/system",
        f"{sys_root}/system32/config/software",
    ])
    SENSITIVE_WRITE_PATHS.extend([
        f"{sys_root}/system32",
    ])

def is_outside_workspace(resolved_path: str) -> bool:
    """Check if resolved path falls outside session_state.initial_cwd."""
    # Convert all path separators to forward slashes for robust cross-platform comparison
    initial_clean = os.path.realpath(session_state.initial_cwd).replace(os.path.sep, "/").rstrip("/")
    res_clean = os.path.realpath(resolved_path).replace(os.path.sep, "/").rstrip("/")
    return not (res_clean == initial_clean or res_clean.startswith(initial_clean + "/"))

def resolve_and_check_sensitivity(path: str, sensitive_list: list) -> Tuple[str, bool]:
    """Resolve path (auto-resolving relative paths against session_state.cwd) and check sensitivity."""
    if not os.path.isabs(path):
        path = os.path.join(session_state.cwd, path)

    if not os.path.exists(path):
        parent = os.path.dirname(path)
        resolved_parent = os.path.realpath(parent)
        resolved_path = os.path.join(resolved_parent, os.path.basename(path))
    else:
        resolved_path = os.path.realpath(path)
        
    # Convert path to lowercase (if Windows) and forward slashes for sensitivity check
    normalized_path = resolved_path.replace(os.path.sep, "/")
    if sys.platform == 'win32':
        normalized_path = normalized_path.lower()
        
    is_sensitive = False
    for entry in sensitive_list:
        entry_normalized = entry.lower() if sys.platform == 'win32' else entry
        if entry_normalized.startswith("/."):
            # Home-relative or user-relative path substring check (e.g. "/.ssh/")
            if entry_normalized in normalized_path:
                is_sensitive = True
                break
        else:
            # Absolute path check: must match exactly or be a subdirectory of the entry
            entry_clean = entry_normalized.rstrip("/")
            if normalized_path == entry_clean or normalized_path.startswith(entry_clean + "/"):
                is_sensitive = True
                break
                
    return resolved_path, is_sensitive

def countdown_warning(path: str):
    """Executes a configurable warning countdown in the terminal before a critical operation."""
    delay_str = os.environ.get("SLASH_AGENT_UNSAFE_DELAY", "5")
    try:
        delay = int(delay_str)
        if delay < 0:
            delay = 5
    except ValueError:
        delay = 5
        
    print(f"\n\033[1;31m[⚠ UNSAFE-YES] Critical operation proceeding to run/modify:\033[0m")
    print(f"  {path}")
    
    # Count down one second at a time
    for i in range(delay, 0, -1):
        print(f"\033[1;33mExecuting in {i} seconds... Press Ctrl+C to abort\033[0m", end="\r", flush=True)
        time.sleep(1)
    print("\033[KProceeding.\n", end="", flush=True)

def prompt_file_confirmation(operation: str, path: str, risk_level: str = "low", risk_description: str = "", preview: str = None) -> Tuple[str, str]:
    """Prompts the user to confirm or comment on a proposed file operation."""
    print(f"\n\033[1;33m[Agent] Proposed {operation.upper()}:\033[0m")
    print(f"  {path}\n")
    
    if preview:
        print("\033[1;30m--- Preview ---\033[0m")
        print(preview)
        print("\033[1;30m---------------\033[0m\n")
        
    # ANSI color mapping for risk levels
    risk_colors = {
        "safe": "\033[1;32m",       # Bold Green
        "low": "\033[1;36m",        # Bold Cyan
        "moderate": "\033[1;33m",   # Bold Yellow
        "critical": "\033[1;31m",   # Bold Red
    }
    
    level = risk_level.lower().strip()
    if level not in risk_colors:
        level = "low"
    color = risk_colors[level]
    
    print(f"{color}[Risk: {level.capitalize()}]\033[0m", end="")
    if risk_description:
        print(f" {risk_description}")
    else:
        print()
    print()
    
    print("\033[1;36mConfirm action: [y]es / [n]o / [c]omment ? \033[0m", end="", flush=True)
    
    while True:
        ch = read_char_raw().lower()
        if ch in ('y', '\r', '\n'):
            print("yes")
            return "yes", ""
        elif ch == 'n':
            print("no")
            return "no", ""
        elif ch == 'c':
            print("comment")
            try:
                comment = input("\033[1;35mFeedback to agent: \033[0m").strip()
                return "comment", comment
            except (KeyboardInterrupt, EOFError):
                print("\nAborted.")
                return "no", ""
        elif ch == '\x03': # Ctrl+C
            print("\nAborted.")
            return "no", ""

def set_pty_size(fd: int, rows: int, cols: int):
    """Set the window size of a pseudo-terminal file descriptor."""
    size = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, size)

def strip_ansi(text: str) -> str:
    """Strip ANSI color codes and normalize carriage returns."""
    cleaned = ANSI_ESCAPE_RE.sub('', text)
    # Normalize carriage returns
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    return cleaned

def read_char_raw() -> str:
    """Read a single character from stdin under raw terminal settings."""
    if sys.platform == 'win32':
        import msvcrt
        try:
            ch = msvcrt.getwch()
            if ch in ('\r', '\n'):
                return '\n'
            return ch
        except Exception:
            return sys.stdin.read(1)

    fd = sys.stdin.fileno()
    if not os.isatty(fd):
        # Fallback if stdin is not a TTY
        return sys.stdin.read(1)
    
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def prompt_user_confirmation(command: str, risk_level: str = "low", risk_description: str = "") -> Tuple[str, str]:
    """Prompts the user to confirm, edit, or comment on a proposed command.
    
    Returns:
        A tuple of (action, payload) where action is 'yes', 'no', 'edit', or 'comment'.
    """
    print(f"\n\033[1;33m[Agent] Proposed Command:\033[0m")
    print(f"  $ {command}\n")
    
    # ANSI color mapping for risk levels
    risk_colors = {
        "safe": "\033[1;32m",       # Bold Green
        "low": "\033[1;36m",        # Bold Cyan
        "moderate": "\033[1;33m",   # Bold Yellow
        "critical": "\033[1;31m",   # Bold Red
    }
    
    level = risk_level.lower().strip()
    if level not in risk_colors:
        level = "low"
    color = risk_colors[level]
    
    print(f"{color}[Risk: {level.capitalize()}]\033[0m", end="")
    if risk_description:
        print(f" {risk_description}")
    else:
        print()
    print()
    
    print("\033[1;36mConfirm action: [y]es / [n]o / [e]edit / [c]omment ? \033[0m", end="", flush=True)
    
    while True:
        ch = read_char_raw().lower()
        if ch in ('y', '\r', '\n'):
            print("yes")
            return "yes", command
        elif ch == 'n':
            print("no")
            return "no", ""
        elif ch == 'e':
            print("edit")
            # Restore cursor and standard input for full line editing
            try:
                edited = input("\033[1;32mEdit command: \033[0m").strip()
                return "edit", edited
            except (KeyboardInterrupt, EOFError):
                print("\nAborted.")
                return "no", ""
        elif ch == 'c':
            print("comment")
            try:
                comment = input("\033[1;35mFeedback to agent: \033[0m").strip()
                return "comment", comment
            except (KeyboardInterrupt, EOFError):
                print("\nAborted.")
                return "no", ""
        elif ch == '\x03': # Ctrl+C
            print("\nAborted.")
            return "no", ""

def run_command_windows(command: str) -> Tuple[int, str]:
    """Executes a command inside a standard subprocess Popen on Windows,
    capturing and streaming output in real-time.
    """
    import subprocess
    import shutil
    
    # Determine the host PowerShell executable
    shell_executable = "powershell.exe"
    if shutil.which("pwsh"):
        shell_executable = "pwsh"
        
    state_token = "___AGENT_SHELL_STATE___"
    env_block_cmd = '[string]::Join("`0", (Get-ChildItem Env: | ForEach-Object { "$($_.Name)=$($_.Value)" }))'
    
    full_cmd = (
        f"$ErrorActionPreference = 'Continue'; "
        f"Set-Location -LiteralPath '{session_state.cwd}'; "
        f"{command}; "
        f"$last_exit = $LASTEXITCODE; "
        f"if ($last_exit -eq $null) {{ $last_exit = if ($?) {{ 0 }} else {{ 1 }} }}; "
        f"Write-Output ''; "
        f"Write-Output '{state_token}'; "
        f"Write-Output 'exit_code=$last_exit'; "
        f"Write-Output 'pwd=$((Get-Location).Path)'; "
        f"Write-Output {env_block_cmd}"
    )
    
    env_to_pass = session_state.env_vars.copy()
    
    proc = subprocess.Popen(
        [shell_executable, "-NoProfile", "-NonInteractive", "-Command", full_cmd],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env_to_pass,
        bufsize=0
    )
    
    accumulated_output = b""
    state_buffer = b""
    token_found = False
    token_bytes = state_token.encode("utf-8")
    
    try:
        while True:
            data = proc.stdout.read(1024)
            if not data:
                break
                
            if not token_found:
                temp = accumulated_output + data
                idx = temp.find(token_bytes)
                if idx != -1:
                    token_found = True
                    before_token = temp[len(accumulated_output):idx]
                    sys.stdout.buffer.write(before_token)
                    sys.stdout.buffer.flush()
                    accumulated_output = temp[:idx]
                    state_buffer = temp[idx:]
                else:
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
                    accumulated_output += data
            else:
                state_buffer += data
                
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
        raise KeyboardInterrupt
        
    return parse_pty_result(accumulated_output, state_buffer)

def run_command_in_pty(command: str) -> Tuple[int, str]:
    """Executes a command inside a pseudo-terminal PTY or delegates to Windows runner.
    
    Bridges stdin/stdout/stderr, updates PTY size, traps SIGWINCH, and cleans output.
    """
    if sys.platform == 'win32':
        return run_command_windows(command)
        
    fd_in = sys.stdin.fileno()
    is_tty = os.isatty(fd_in)
    
    # Setup command execution block with PWD and env variable dump
    # We output environment variables separated by null bytes (\x00) for clean parsing
    state_token = "___AGENT_SHELL_STATE___"
    full_cmd = (
        f"cd {session_state.cwd} && {command}; "
        f"_exit_code=$?; "
        f"echo \"\"; "
        f"echo \"{state_token}\"; "
        f"echo \"exit_code=$_exit_code\"; "
        f"echo \"pwd=$(pwd)\"; "
        f"env -0"
    )
    
    # Save active env dictionary into environment variables
    env_to_pass = session_state.env_vars.copy()
    
    if not is_tty:
        # Fallback: stateless execution using standard subprocess if not a TTY
        import subprocess
        try:
            res = subprocess.run(
                ["/bin/bash", "-c", full_cmd],
                env=env_to_pass,
                capture_output=True,
                text=False
            )
            # Standard subprocess run doesn't output to stdout in real-time, but we can capture it.
            # We separate the output buffer
            combined_output = res.stdout + res.stderr
            return parse_pty_result(combined_output)
        except Exception as e:
            return 1, f"Execution failed: {str(e)}"

    # If it is a TTY, use the pseudo-terminal bridge
    old_tty_settings = termios.tcgetattr(fd_in)
    pid, master_fd = pty.fork()
    
    if pid == 0:
        # Child process: execute bash subshell
        # The child process naturally inherits PTY stdin/stdout/stderr
        os.execve("/bin/bash", ["/bin/bash", "-c", full_cmd], env_to_pass)
        sys.exit(127)
        
    # Parent process: bridge terminal
    # Set the initial columns and rows on the child PTY
    try:
        cols, rows = os.get_terminal_size(sys.stdout.fileno())
        set_pty_size(master_fd, rows, cols)
    except Exception:
        pass

    # Setup terminal size resize handler (SIGWINCH)
    def resize_handler(signum, frame):
        try:
            c, r = os.get_terminal_size(sys.stdout.fileno())
            set_pty_size(master_fd, r, c)
        except Exception:
            pass
            
    signal.signal(signal.SIGWINCH, resize_handler)
    
    # Put terminal stdin into raw mode
    tty.setraw(fd_in)
    
    accumulated_output = b""
    state_buffer = b""
    token_found = False
    token_bytes = state_token.encode("utf-8")
    
    try:
        while True:
            # Wait for read capability on stdin or PTY master
            r, w, x = select.select([fd_in, master_fd], [], [])
            
            if fd_in in r:
                # Read raw input from user keyboard and write to child PTY
                data = os.read(fd_in, 1024)
                if not data:
                    break
                os.write(master_fd, data)
                
            if master_fd in r:
                # Read stdout/stderr from child PTY
                try:
                    data = os.read(master_fd, 4096)
                except OSError:
                    # Occurs when the PTY closes on child exit
                    break
                if not data:
                    break
                    
                if not token_found:
                    temp = accumulated_output + data
                    idx = temp.find(token_bytes)
                    if idx != -1:
                        token_found = True
                        # Write the part of output before the token to stdout
                        before_token = temp[len(accumulated_output):idx]
                        sys.stdout.buffer.write(before_token)
                        sys.stdout.buffer.flush()
                        
                        accumulated_output = temp[:idx]
                        state_buffer = temp[idx:]
                    else:
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()
                        accumulated_output += data
                else:
                    state_buffer += data
    finally:
        # Restore terminal settings and clear SIGWINCH signal handler
        termios.tcsetattr(fd_in, termios.TCSADRAIN, old_tty_settings)
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)
        
    # Parse exit status
    return parse_pty_result(accumulated_output, state_buffer)

def parse_pty_result(command_output: bytes, state_buffer: bytes = b"") -> Tuple[int, str]:
    """Parses PTY output buffers, updating working dir/env and returning command logs."""
    exit_code = 0
    pwd = session_state.cwd
    env_updates = {}
    
    # Split the state buffer to separate exit_code, pwd, and env variables
    # Slicing at the third newline gets our elements
    parts = state_buffer.split(b"\n", 3)
    
    if len(parts) >= 3:
        exit_line = parts[1].replace(b"\r", b"")
        pwd_line = parts[2].replace(b"\r", b"")
        if exit_line.startswith(b"exit_code="):
            try:
                exit_code = int(exit_line.split(b"=", 1)[1])
            except ValueError:
                pass
        if pwd_line.startswith(b"pwd="):
            pwd = pwd_line.split(b"=", 1)[1].decode("utf-8", errors="ignore").strip()
            
    if len(parts) >= 4:
        env_part = parts[3]
        # env -0 outputs variables separated by null bytes
        for item in env_part.split(b"\x00"):
            if b"=" in item:
                k, v = item.split(b"=", 1)
                k_str = k.decode("utf-8", errors="ignore")
                v_str = v.decode("utf-8", errors="ignore")
                env_updates[k_str] = v_str
                
    # Update global session state
    if os.path.isdir(pwd):
        session_state.cwd = pwd
        
    if env_updates:
        # Update or delete environment variables to match subprocess final state
        # In a real shell, some env variables like PWD or OLDPWD should match session_state.cwd
        session_state.env_vars.update(env_updates)
        
    # Clean the captured output for the LLM
    cleaned_output = strip_ansi(command_output.decode("utf-8", errors="ignore"))
    return exit_code, cleaned_output

@tool
async def execute_command(command: str, risk_level: str = "low", risk_description: str = "") -> str:
    """Executes a shell command on the user's system, preserving directory context.
    
    Note: The working directory (CWD) and environment variables are preserved statefully between tool executions.
    
    Args:
        command: The command line string to run in bash (e.g. 'npm run build').
        risk_level: The security risk level of the command. MUST be one of: 'safe', 'low', 'moderate', or 'critical'.
        risk_description: A brief explanation of the risk. Must be provided if risk_level is 'moderate' or 'critical'; should be empty for 'safe' or 'low' unless a specific caution applies.
    """
    # Normalize risk level and description
    level = risk_level.lower().strip()
    desc = risk_description.strip()
    
    # Python-level Safety Guardrail overrides for dangerous commands
    cmd_lower = command.lower()
    critical_patterns = [
        "rm -rf", "sudo ", "mkfs", "dd ", "chmod -r", "chown -r", "/dev/sd",
        "remove-item -recurse", "remove-item -r", "del /s", "format ", "takeown", "icacls", "runas"
    ]
    if any(pat in cmd_lower for pat in critical_patterns):
        level = "critical"
        desc = "Command contains administrative or destructive file-system operations (e.g., rm, sudo, chown, remove-item, runas)."
    
    # Elevate risk to moderate for script executions/other shells if not already higher
    script_patterns = ["./", ".\\", "sh ", "bash ", "python ", "make ", "npx ", "npm run ", "powershell ", "pwsh ", "cmd "]
    if level in ("safe", "low") and any(pat in cmd_lower for pat in script_patterns):
        level = "moderate"
        desc = "Command executes a local script, runner, or makefile."
        
    if session_state.dry_run:
        print(f"\n\033[1;34m[Dry-run] Would execute:\033[0m {command}")
        return f"Command execution simulated. Result: Exit code 0, Output: (Dry-run simulated)"
        
    # Check if we can auto-confirm
    can_auto_confirm = session_state.auto_confirm
    if level == "critical" and not session_state.unsafe_confirm:
        # Standard auto-confirm does not bypass critical prompts
        can_auto_confirm = False
        
    if can_auto_confirm:
        if level == "critical" and session_state.unsafe_confirm:
            try:
                countdown_warning(command)
            except KeyboardInterrupt:
                print("\n\033[1;31m[Aborted] Command execution cancelled by user.\033[0m")
                return "Error: Command execution aborted by user during safety countdown."
        print(f"\n\033[1;32m[Agent Running]:\033[0m {command}")
        exit_code, output = run_command_in_pty(command)
        return f"Exit code: {exit_code}\nOutput:\n{output}"
        
    # Prompt the user for confirmation
    action, cmd_to_run = prompt_user_confirmation(command, risk_level=level, risk_description=desc)
    
    if action == "no":
        return "Command rejected by user: User refused execution."
    elif action == "comment":
        return f"Command rejected by user. Feedback: {cmd_to_run}"
    
    # Run the accepted or edited command
    if level == "critical" and session_state.unsafe_confirm:
        try:
            countdown_warning(cmd_to_run)
        except KeyboardInterrupt:
            print("\n\033[1;31m[Aborted] Command execution cancelled by user.\033[0m")
            return "Error: Command execution aborted by user during safety countdown."

    if action == "edit":
        print(f"\033[1;32m[Agent Running Edited Command]:\033[0m {cmd_to_run}")
    else:
        print(f"\033[1;32m[Agent Running]:\033[0m {cmd_to_run}")
        
    exit_code, output = run_command_in_pty(cmd_to_run)
    return f"Exit code: {exit_code}\nOutput:\n{output}"

@tool
async def request_user_input(prompt: str) -> str:
    """Prompts the user directly in the terminal to ask a clarifying question or request input.
    
    Use this tool ONLY if the task is ambiguous or unclear. Do NOT use it to ask for permission to run commands or confirm individual steps, as the parent shell's prompt automatically prompts the user to confirm all proposed command executions.
    
    Args:
        prompt: The question or request prompt to show the user (e.g. 'What is the target branch?').
    """
    print(f"\n\033[1;36m[Agent Question] {prompt}\033[0m")
    loop = asyncio.get_event_loop()
    try:
        # Run the synchronous input() in a separate executor thread to prevent blocking the asyncio loop.
        response = await loop.run_in_executor(None, lambda: input("\033[1;32m> \033[0m").strip())
        return response
    except (KeyboardInterrupt, EOFError):
        print("\n\033[1;31m[Agent Question Aborted]\033[0m")
        # Propagate KeyboardInterrupt to cleanly abort agent execution
        raise KeyboardInterrupt

@tool
async def read_skill_instructions(skill_path: str) -> str:
    """Reads the detailed instructions for a specific agent skill from the provided path.
    
    This is a read-only tool and executes silently without prompting the user for confirmation.
    
    Args:
        skill_path: The absolute filesystem path to the SKILL.md file.
    """
    try:
        # Check that path exists and is a file
        if not os.path.isfile(skill_path):
            return f"Error: Skill file not found at '{skill_path}'."
            
        # Ensure it is a SKILL.md file for safety/security
        if not os.path.basename(skill_path) == "SKILL.md":
            return "Error: Access denied. Only SKILL.md files can be read using this tool."
            
        with open(skill_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        return content
    except Exception as e:
        return f"Error reading skill file: {str(e)}"


@tool
async def read_file(path: str, risk_level: str = "low", risk_description: str = "") -> str:
    """Reads the complete contents of a file on the user's system.
    
    Paths can be absolute or relative to the working directory.
    
    Args:
        path: The filesystem path to read.
        risk_level: The security risk level of the read. MUST be one of: 'safe', 'low', 'moderate', or 'critical'.
        risk_description: A brief explanation of the risk. Must be provided if risk_level is 'moderate' or 'critical'.
    """
    # Resolve path & check sensitivity
    resolved_path, is_sensitive = resolve_and_check_sensitivity(path, SENSITIVE_READ_PATHS)
    
    level = risk_level.lower().strip()
    desc = risk_description.strip()
    if is_sensitive:
        level = "critical"
        desc = f"Accessing sensitive system path: {resolved_path}"
        
    # Apply tiered auto-confirm
    can_auto_confirm = session_state.auto_confirm
    if level == "critical" and not session_state.unsafe_confirm:
        can_auto_confirm = False
        
    if can_auto_confirm:
        if level == "critical":
            try:
                countdown_warning(resolved_path)
            except KeyboardInterrupt:
                print("\n\033[1;31m[Aborted] Read operation cancelled by user.\033[0m")
                return "Error: Read operation aborted by user during countdown."
            
        try:
            with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except PermissionError as e:
            return f"Error: Permission denied reading file '{resolved_path}'. Details: {str(e)}"
        except Exception as e:
            return f"Error: Failed to read file '{resolved_path}'. Details: {str(e)}"

    # Prompt user for confirmation
    action, comment = prompt_file_confirmation("READ", resolved_path, risk_level=level, risk_description=desc)
    
    if action == "no":
        return "Error: Read operation rejected by user."
    elif action == "comment":
        return f"Error: Read operation rejected by user. Feedback: {comment}"
        
    try:
        with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except PermissionError as e:
        return f"Error: Permission denied reading file '{resolved_path}'. Details: {str(e)}"
    except Exception as e:
        return f"Error: Failed to read file '{resolved_path}'. Details: {str(e)}"


@tool
async def write_file(path: str, content: str, risk_level: str = "low", risk_description: str = "") -> str:
    """Writes content to a file (creates or overwrites it).
    
    Paths can be absolute or relative to the working directory. Parent directories will be auto-created.
    
    Args:
        path: The filesystem path to write.
        content: The text content to write to the file.
        risk_level: The security risk level of the write. MUST be one of: 'safe', 'low', 'moderate', or 'critical'.
        risk_description: A brief explanation of the risk. Must be provided if risk_level is 'moderate' or 'critical'.
    """
    # Resolve path & check sensitivity
    resolved_path, is_sensitive = resolve_and_check_sensitivity(path, SENSITIVE_WRITE_PATHS)
    
    level = risk_level.lower().strip()
    desc = risk_description.strip()
    if is_sensitive:
        level = "critical"
        desc = f"Writing to sensitive system path: {resolved_path}"
    elif is_outside_workspace(resolved_path):
        level = "critical"
        desc = f"Writing to path outside launching workspace directory ({session_state.initial_cwd}): {resolved_path}"
        
    # Apply tiered auto-confirm
    can_auto_confirm = session_state.auto_confirm
    if level == "critical" and not session_state.unsafe_confirm:
        can_auto_confirm = False
        
    lines_count = len(content.splitlines())
    summary = f"Wrote {lines_count} lines to '{resolved_path}'."
    
    if can_auto_confirm:
        # Check dry-run
        if session_state.dry_run:
            print(f"\n\033[1;34m[Dry-run] Would write file:\033[0m {resolved_path}")
            return f"File write simulated for: {resolved_path}"
            
        if level == "critical":
            try:
                countdown_warning(resolved_path)
            except KeyboardInterrupt:
                print("\n\033[1;31m[Aborted] Write operation cancelled by user.\033[0m")
                return "Error: Write operation aborted by user during countdown."
            
        try:
            parent_dir = os.path.dirname(resolved_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(resolved_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Success: {summary}"
        except PermissionError as e:
            return f"Error: Permission denied writing to file '{resolved_path}'. Details: {str(e)}"
        except Exception as e:
            return f"Error: Failed to write to file '{resolved_path}'. Details: {str(e)}"

    # Prompt user for confirmation
    # Preview up to first 10 lines
    content_lines = content.splitlines()
    preview_lines = content_lines[:10]
    preview = "\n".join(preview_lines)
    if len(content_lines) > 10:
        preview += "\n..."
        
    action, comment = prompt_file_confirmation("WRITE", resolved_path, risk_level=level, risk_description=desc, preview=preview)
    
    if action == "no":
        return "Error: Write operation rejected by user."
    elif action == "comment":
        return f"Error: Write operation rejected by user. Feedback: {comment}"
        
    # User confirmed "yes"
    # Check dry-run
    if session_state.dry_run:
        print(f"\n\033[1;34m[Dry-run] Would write file:\033[0m {resolved_path}")
        return f"File write simulated for: {resolved_path}"
        
    # If confirmed + unsafe-yes is active + critical: run countdown
    if level == "critical" and session_state.unsafe_confirm:
        try:
            countdown_warning(resolved_path)
        except KeyboardInterrupt:
            print("\n\033[1;31m[Aborted] Write operation cancelled by user.\033[0m")
            return "Error: Write operation aborted by user during countdown."
            
    try:
        parent_dir = os.path.dirname(resolved_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: {summary}"
    except PermissionError as e:
        return f"Error: Permission denied writing to file '{resolved_path}'. Details: {str(e)}"
    except Exception as e:
        return f"Error: Failed to write to file '{resolved_path}'. Details: {str(e)}"


@tool
async def edit_file(path: str, old_str: str, new_str: str, risk_level: str = "low", risk_description: str = "") -> str:
    """Makes a targeted replacement within an existing file.
    
    Paths can be absolute or relative to the working directory. The old_str must be unique in the file.
    
    Args:
        path: The filesystem path of the file to edit.
        old_str: The exact literal string to be replaced.
        new_str: The replacement string.
        risk_level: The security risk level of the edit. MUST be one of: 'safe', 'low', 'moderate', or 'critical'.
        risk_description: A brief explanation of the risk. Must be provided if risk_level is 'moderate' or 'critical'.
    """
    # Resolve path & check sensitivity
    resolved_path, is_sensitive = resolve_and_check_sensitivity(path, SENSITIVE_WRITE_PATHS)
    
    # Check if file exists
    if not os.path.exists(resolved_path) or not os.path.isfile(resolved_path):
        return f"Error: Target file '{resolved_path}' does not exist."
        
    level = risk_level.lower().strip()
    desc = risk_description.strip()
    if is_sensitive:
        level = "critical"
        desc = f"Editing sensitive system file: {resolved_path}"
    elif is_outside_workspace(resolved_path):
        level = "critical"
        desc = f"Editing file outside launching workspace directory ({session_state.initial_cwd}): {resolved_path}"
        
    # Read current content and validate uniqueness of old_str
    try:
        with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
            old_content = f.read()
    except PermissionError as e:
        return f"Error: Permission denied reading file '{resolved_path}'. Details: {str(e)}"
    except Exception as e:
        return f"Error: Failed to read file '{resolved_path}'. Details: {str(e)}"
        
    count = old_content.count(old_str)
    if count == 0:
        return "Error: The string to replace ('old_str') was not found in the file."
    elif count > 1:
        return f"Error: The string to replace ('old_str') is ambiguous (found {count} occurrences). Please include more surrounding context to make it unique."
        
    # Compute new content
    new_content = old_content.replace(old_str, new_str, 1)
    
    # Generate unified diff
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=resolved_path,
        tofile=resolved_path,
        lineterm=""
    ))
    diff_str = "\n".join(diff)
    
    # Apply tiered auto-confirm
    can_auto_confirm = session_state.auto_confirm
    if level == "critical" and not session_state.unsafe_confirm:
        can_auto_confirm = False
        
    success_output = f"Success: File edited at '{resolved_path}'.\nDiff:\n{diff_str}" if diff_str else f"Success: File edited at '{resolved_path}'."
    
    if can_auto_confirm:
        # Check dry-run
        if session_state.dry_run:
            print(f"\n\033[1;34m[Dry-run] Would edit file:\033[0m {resolved_path}")
            if diff_str:
                print(diff_str)
            return f"File edit simulated for: {resolved_path}"
            
        if level == "critical":
            try:
                countdown_warning(resolved_path)
            except KeyboardInterrupt:
                print("\n\033[1;31m[Aborted] Edit operation cancelled by user.\033[0m")
                return "Error: Edit operation aborted by user during countdown."
            
        try:
            with open(resolved_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return success_output
        except PermissionError as e:
            return f"Error: Permission denied writing to file '{resolved_path}'. Details: {str(e)}"
        except Exception as e:
            return f"Error: Failed to write to file '{resolved_path}'. Details: {str(e)}"

    # Prompt user for confirmation with diff
    action, comment = prompt_file_confirmation("EDIT", resolved_path, risk_level=level, risk_description=desc, preview=diff_str)
    
    if action == "no":
        return "Error: Edit operation rejected by user."
    elif action == "comment":
        return f"Error: Edit operation rejected by user. Feedback: {comment}"
        
    # User confirmed "yes"
    # Check dry-run
    if session_state.dry_run:
        print(f"\n\033[1;34m[Dry-run] Would edit file:\033[0m {resolved_path}")
        if diff_str:
            print(diff_str)
        return f"File edit simulated for: {resolved_path}"
        
    # If confirmed + unsafe-yes is active + critical: run countdown
    if level == "critical" and session_state.unsafe_confirm:
        try:
            countdown_warning(resolved_path)
        except KeyboardInterrupt:
            print("\n\033[1;31m[Aborted] Edit operation cancelled by user.\033[0m")
            return "Error: Edit operation aborted by user during countdown."
            
    try:
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return success_output
    except PermissionError as e:
        return f"Error: Permission denied writing to file '{resolved_path}'. Details: {str(e)}"
    except Exception as e:
        return f"Error: Failed to write to file '{resolved_path}'. Details: {str(e)}"


