import os
import sys
import re
import asyncio
import select
import pty
import termios
import tty
import signal
import fcntl
import struct
import time
import difflib
import subprocess
import ctypes
import atexit
from typing import Dict, Any, Tuple
from py_agent_core.tool import tool

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
        self.silent = False
        self.session_logs = []
        self.active_tasks = {}
        self.task_counter = 0

# Global session state singleton
session_state = ShellState()

# Windows Job Object initialization (conditional)
_win32_job_handle = None
if sys.platform == "win32":
    try:
        import win32job
        import win32process
        import win32con
        # Create a Job Object for the entire session
        _win32_job_handle = win32job.CreateJobObject(None, "")
        # Set the job to terminate all processes on close
        info = win32job.QueryInformationJobObject(_win32_job_handle, win32job.JobObjectExtendedLimitInformation)
        info['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        win32job.SetInformationJobObject(_win32_job_handle, win32job.JobObjectExtendedLimitInformation, info)
    except Exception:
        pass

def linux_preexec_fn():
    # Establish new process group
    os.setpgrp()
    # Request SIGTERM when parent terminates
    try:
        import ctypes
        libc = ctypes.CDLL(None)
        PR_SET_PDEATHSIG = 1
        SIGTERM = 15
        libc.prctl(PR_SET_PDEATHSIG, SIGTERM)
    except Exception:
        pass

def teardown_tasks():
    # Kill POSIX process groups or standard processes
    alive_procs = []
    for task_id, task_meta in list(session_state.active_tasks.items()):
        proc = task_meta.get("proc")
        if proc and proc.poll() is None:
            alive_procs.append((task_id, proc))
            try:
                if sys.platform != "win32":
                    pgid = os.getpgid(proc.pid)
                    os.killpg(pgid, signal.SIGTERM)
                else:
                    proc.terminate()
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass
                    
    if alive_procs:
        time.sleep(0.5)
        # Check again and kill forcefully if still alive
        for task_id, proc in alive_procs:
            if proc.poll() is None:
                try:
                    if sys.platform != "win32":
                        pgid = os.getpgid(proc.pid)
                        os.killpg(pgid, signal.SIGKILL)
                    else:
                        proc.kill()
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            # Mark finished
            session_state.active_tasks.pop(task_id, None)

# Register atexit handler
atexit.register(teardown_tasks)

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

def is_outside_workspace(resolved_path: str) -> bool:
    """Check if resolved path falls outside session_state.initial_cwd."""
    initial_clean = os.path.realpath(session_state.initial_cwd).rstrip("/")
    res_clean = os.path.realpath(resolved_path)
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
        
    is_sensitive = False
    for entry in sensitive_list:
        if entry.startswith("/."):
            # Home-relative or user-relative path substring check (e.g. "/.ssh/")
            if entry in resolved_path:
                is_sensitive = True
                break
        else:
            # Absolute path check: must match exactly or be a subdirectory of the entry
            entry_clean = entry.rstrip("/")
            if resolved_path == entry_clean or resolved_path.startswith(entry_clean + "/"):
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

def prompt_file_confirmation(operation: str, path: str, risk_level: str = "low", risk_description: str = "", preview: str = None, start_line: int = None, end_line: int = None) -> Tuple[str, str]:
    """Prompts the user to confirm or comment on a proposed file operation."""
    print(f"\n\033[1;33m[Agent] Proposed {operation.upper()}:\033[0m")
    if start_line is not None or end_line is not None:
        s_val = start_line
        e_val = end_line
        range_str = f"Lines {s_val if s_val is not None else 1}-{e_val if e_val is not None else 'EOF'}"
        print(f"  {path} ({range_str})\n")
    else:
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

def run_command_in_pty(command: str) -> Tuple[int, str, str]:
    """Executes a command inside a pseudo-terminal PTY.
    
    Bridges stdin/stdout/stderr, updates PTY size, traps SIGWINCH, and cleans output.
    """
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
    
    # Setup temporary logging file
    import tempfile
    log_dir = os.path.join(tempfile.gettempdir(), "slash-agent")
    try:
        os.makedirs(log_dir, mode=0o700, exist_ok=True)
        os.chmod(log_dir, 0o700)
    except Exception:
        pass
        
    run_id = str(int(time.time() * 1000))
    log_path = os.path.join(log_dir, f"cmd_{run_id}.log")
    session_state.session_logs.append(log_path)
    
    try:
        log_fd = os.open(log_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
        log_file = os.fdopen(log_fd, "wb")
    except Exception:
        log_file = open(log_path, "wb")
    
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
            combined_output = res.stdout + res.stderr
            try:
                log_file.write(combined_output)
                log_file.close()
            except Exception:
                pass
            exit_code, cleaned_output = parse_pty_result(combined_output)
            return exit_code, cleaned_output, log_path
        except Exception as e:
            try:
                log_file.close()
            except Exception:
                pass
            return 1, f"Execution failed: {str(e)}", log_path

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
    is_collapsed = False
    spinner_idx = 0
    
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
                        before_token = temp[len(accumulated_output):idx]
                        
                        # Log before token output
                        log_file.write(before_token)
                        
                        # Collapse check
                        if not is_collapsed and (len(accumulated_output) + len(before_token) > 50000 or (accumulated_output + before_token).count(b"\n") > 500):
                            is_collapsed = True
                            if not session_state.silent:
                                sys.stdout.write("\n\033[1;33m[Warning: Output exceeds 500 lines/50KB. Collapsing stdout display to spinner...]\033[0m\n")
                                sys.stdout.flush()
                                
                        if not session_state.silent and not is_collapsed:
                            sys.stdout.buffer.write(before_token)
                            sys.stdout.buffer.flush()
                        elif is_collapsed and not session_state.silent:
                            spinner_chars = ["|", "/", "-", "\\"]
                            spinner_idx = (spinner_idx + 1) % 4
                            sys.stdout.write(f"\rStreaming output... {spinner_chars[spinner_idx]}")
                            sys.stdout.flush()
                            
                        accumulated_output = temp[:idx]
                        state_buffer = temp[idx:]
                    else:
                        log_file.write(data)
                        
                        # Collapse check
                        if not is_collapsed and (len(accumulated_output) + len(data) > 50000 or (accumulated_output + data).count(b"\n") > 500):
                            is_collapsed = True
                            if not session_state.silent:
                                sys.stdout.write("\n\033[1;33m[Warning: Output exceeds 500 lines/50KB. Collapsing stdout display to spinner...]\033[0m\n")
                                sys.stdout.flush()
                                
                        if not session_state.silent and not is_collapsed:
                            sys.stdout.buffer.write(data)
                            sys.stdout.buffer.flush()
                        elif is_collapsed and not session_state.silent:
                            spinner_chars = ["|", "/", "-", "\\"]
                            spinner_idx = (spinner_idx + 1) % 4
                            sys.stdout.write(f"\rStreaming output... {spinner_chars[spinner_idx]}")
                            sys.stdout.flush()
                            
                        accumulated_output += data
                else:
                    state_buffer += data
    finally:
        # Close log file
        try:
            log_file.close()
        except Exception:
            pass
        # Clear spinner line if collapsed
        if is_collapsed and not session_state.silent:
            sys.stdout.write("\r" + " " * 45 + "\r")
            sys.stdout.flush()
        # Restore terminal settings and clear SIGWINCH signal handler
        termios.tcsetattr(fd_in, termios.TCSADRAIN, old_tty_settings)
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)
        
    # Parse exit status
    exit_code, cleaned_output = parse_pty_result(accumulated_output, state_buffer)
    return exit_code, cleaned_output, log_path

def parse_pty_result(command_output: bytes, state_buffer: bytes = b"") -> Tuple[int, str]:
    """Parses PTY output buffers, updating working dir/env and returning command logs."""
    exit_code = 0
    pwd = session_state.cwd
    env_updates = {}
    
    # Split the state buffer to separate exit_code, pwd, and env variables
    # Slicing at the third newline gets our elements
    parts = state_buffer.split(b"\n", 3)
    
    if len(parts) >= 3:
        exit_line = parts[1]
        pwd_line = parts[2]
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

def format_execution_result(exit_code: int, output: str, log_path: str) -> str:
    if session_state.silent and exit_code != 0:
        sys.stdout.write(f"\n\033[1;31m[Error] Command failed with exit code {exit_code}. Dumping full logs:\033[0m\n")
        sys.stdout.write(output)
        if not output.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.flush()
        
    output_lines = output.splitlines()
    limit_bytes = 20000
    limit_lines = 200
    
    if len(output) >= limit_bytes or len(output_lines) >= limit_lines:
        first_50 = output_lines[:50]
        last_100 = output_lines[-100:]
        truncated_preview = "\n".join(first_50) + "\n\n... [LINES OMITTED] ...\n\n" + "\n".join(last_100)
        
        result_msg = (
            f"Exit code: {exit_code}\n"
            f"[Output Truncated: Size {len(output) // 1024}KB, {len(output_lines)} lines. "
            f"Full logs written to '{log_path}'.]\n"
            f"--- LOG PREVIEW (First 50 and last 100 lines) ---\n"
            f"{truncated_preview}\n"
            f"--- END LOG PREVIEW ---\n"
            f"[Use the read_file tool with start_line/end_line to inspect specific segments of the log file '{log_path}' if needed.]"
        )
        return result_msg
    else:
        return f"Exit code: {exit_code}\nOutput:\n{output}"

def run_command_in_background(command: str) -> str:
    import tempfile
    tasks_log_dir = os.path.join(tempfile.gettempdir(), "slash-agent", "tasks")
    try:
        os.makedirs(tasks_log_dir, mode=0o700, exist_ok=True)
        os.chmod(tasks_log_dir, 0o700)
    except Exception:
        pass
        
    session_state.task_counter += 1
    task_id = f"task_{session_state.task_counter}"
    log_path = os.path.join(tasks_log_dir, f"{task_id}.log")
    
    session_state.session_logs.append(log_path)
    
    try:
        log_fd = os.open(log_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
        log_file = os.fdopen(log_fd, "wb")
    except Exception:
        log_file = open(log_path, "wb")
        
    env_to_pass = session_state.env_vars.copy()
    shell_cmd = f"cd {session_state.cwd} && {command}"
    
    popen_args = {
        "args": ["/bin/bash", "-c", shell_cmd],
        "env": env_to_pass,
        "stdout": log_file,
        "stderr": log_file,
    }
    
    if sys.platform != "win32":
        popen_args["preexec_fn"] = linux_preexec_fn
    else:
        try:
            import win32con
            popen_args["creationflags"] = win32con.CREATE_BREAKAWAY_FROM_JOB
        except Exception:
            pass
            
    try:
        proc = subprocess.Popen(**popen_args)
        log_file.close()
        
        if sys.platform == "win32" and _win32_job_handle is not None:
            try:
                import win32process
                import win32api
                proc_handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc.pid)
                win32job.AssignProcessToJobObject(_win32_job_handle, proc_handle.handle)
            except Exception:
                pass
                
        session_state.active_tasks[task_id] = {
            "task_id": task_id,
            "command": command,
            "proc": proc,
            "log_path": log_path,
            "start_time": time.time(),
        }
        
        print(f"\n\033[1;32m✓ Background task {task_id} spawned successfully.\033[0m")
        return f"Success: Command spawned in the background. Task ID: {task_id}"
    except Exception as e:
        return f"Error: Failed to spawn background process. Details: {str(e)}"

@tool
async def execute_command(command: str, background: bool = False, risk_level: str = "low", risk_description: str = "") -> str:
    """Executes a shell command on the user's system, preserving directory context.
    
    Note: The working directory (CWD) and environment variables are preserved statefully between tool executions.
    For long-running tasks, watchers, or concurrent execution (e.g. client/server), set background=True to run asynchronously.
    
    Args:
        command: The command line string to run in bash (e.g. 'npm run build').
        background: Set to True to execute the command asynchronously in the background. Returns a task_id immediately.
        risk_level: The security risk level of the command. MUST be one of: 'safe', 'low', 'moderate', or 'critical'.
        risk_description: A brief explanation of the risk. Must be provided if risk_level is 'moderate' or 'critical'; should be empty for 'safe' or 'low' unless a specific caution applies.
    """
    # Normalize risk level and description
    level = risk_level.lower().strip()
    desc = risk_description.strip()
    
    # Python-level Safety Guardrail overrides for dangerous commands
    cmd_lower = command.lower()
    critical_patterns = ["rm -rf", "sudo ", "mkfs", "dd ", "chmod -r", "chown -r", "/dev/sd"]
    if any(pat in cmd_lower for pat in critical_patterns):
        level = "critical"
        warning = "Command contains administrative or destructive file-system operations (e.g., rm, sudo, chown)."
        desc = f"[System Warning] {warning} | [Model Reason] {desc}" if desc else f"[System Warning] {warning}"
    
    # Elevate risk to moderate for script executions/other shells if not already higher
    script_patterns = ["./", "sh ", "bash ", "python ", "make ", "npx ", "npm run "]
    if level in ("safe", "low") and any(pat in cmd_lower for pat in script_patterns):
        level = "moderate"
        warning = "Command executes a local script, runner, or makefile."
        desc = f"[System Warning] {warning} | [Model Reason] {desc}" if desc else f"[System Warning] {warning}"
        
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
        if background:
            return run_command_in_background(command)
        exit_code, output, log_path = run_command_in_pty(command)
        return format_execution_result(exit_code, output, log_path)
        
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
        
    if background:
        return run_command_in_background(cmd_to_run)
    exit_code, output, log_path = run_command_in_pty(cmd_to_run)
    return format_execution_result(exit_code, output, log_path)

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
async def list_background_tasks() -> str:
    """Lists all active background tasks running in the current session and their statuses."""
    if not session_state.active_tasks:
        return "No background tasks currently running."
        
    lines = []
    lines.append("Active Background Tasks:")
    lines.append(f"{'Task ID':<10} | {'Status':<15} | {'Start Time':<20} | {'Command':<30}")
    lines.append("-" * 80)
    
    for task_id, task in list(session_state.active_tasks.items()):
        proc = task.get("proc")
        status = "running"
        if proc:
            exit_code = proc.poll()
            if exit_code is not None:
                status = f"finished ({exit_code})"
                
        start_t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(task.get("start_time", 0)))
        cmd = task.get("command", "")
        if len(cmd) > 30:
            cmd = cmd[:27] + "..."
            
        lines.append(f"{task_id:<10} | {status:<15} | {start_t:<20} | {cmd:<30}")
        
    return "\n".join(lines)

@tool
async def get_task_logs(task_id: str, tail_lines: int = 100) -> str:
    """Retrieves the recent log buffer (stdout/stderr) of a background task.
    
    Args:
        task_id: The ID of the task (e.g. 'task_1').
        tail_lines: Number of recent log lines to retrieve (default is 100).
    """
    if task_id not in session_state.active_tasks:
        return f"Error: Task ID '{task_id}' not found in active task registry."
        
    task = session_state.active_tasks[task_id]
    log_path = task.get("log_path")
    if not log_path or not os.path.exists(log_path):
        return f"Error: Log file not found for task '{task_id}'."
        
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        requested_lines = lines[-tail_lines:] if tail_lines > 0 else lines
        content = "".join(requested_lines)
        
        status = "running"
        proc = task.get("proc")
        if proc:
            exit_code = proc.poll()
            if exit_code is not None:
                status = f"finished ({exit_code})"
                
        prefix = f"--- Logs for Task '{task_id}' (Status: {status}, showing last {len(requested_lines)} of {total_lines} lines) ---\n"
        suffix = f"\n--- End Logs for Task '{task_id}' ---"
        return prefix + content + suffix
    except Exception as e:
        return f"Error: Failed to read logs for task '{task_id}'. Details: {str(e)}"

@tool
async def kill_background_task(task_id: str) -> str:
    """Forcefully terminates a background task by its ID.
    
    Args:
        task_id: The ID of the task to terminate (e.g. 'task_1').
    """
    if task_id not in session_state.active_tasks:
        return f"Error: Task ID '{task_id}' not found in active task registry."
        
    task = session_state.active_tasks[task_id]
    proc = task.get("proc")
    
    if not proc or proc.poll() is not None:
        session_state.active_tasks.pop(task_id, None)
        return f"Task '{task_id}' has already finished."
        
    try:
        if sys.platform != "win32":
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGTERM)
            time.sleep(0.2)
            if proc.poll() is None:
                os.killpg(pgid, signal.SIGKILL)
        else:
            proc.terminate()
            time.sleep(0.2)
            if proc.poll() is None:
                proc.kill()
                
        session_state.active_tasks.pop(task_id, None)
        print(f"\033[1;31m✓ Background task {task_id} terminated.\033[0m")
        return f"Success: Forcefully terminated background task '{task_id}'."
    except Exception as e:
        try:
            proc.kill()
            session_state.active_tasks.pop(task_id, None)
            return f"Success: Terminated background task '{task_id}' (fallback)."
        except Exception as fallback_err:
            return f"Error: Failed to terminate task '{task_id}'. Details: {str(e)} | Fallback details: {str(fallback_err)}"

@tool
async def wait_seconds(seconds: int) -> str:
    """Pauses agent execution for a specified number of seconds.
    
    Use this tool to wait for background tasks, slow servers, or compilations to progress.
    You should specify the lowest reasonable duration to minimize wait latency.
    
    Args:
        seconds: The number of seconds to pause (maximum 300).
    """
    duration = max(1, min(seconds, 300))
    print(f"\033[1;30m[Agent waiting for {duration} seconds...]\033[0m", flush=True)
    await asyncio.sleep(duration)
    return f"Success: Waited for {duration} seconds."

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


def read_file_content(resolved_path: str, start_line: int = None, end_line: int = None) -> str:
    with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    total_lines = len(lines)
    
    try:
        limit_str = os.environ.get("AGENT_READ_LINE_LIMIT", "800")
        limit = int(limit_str)
        if limit <= 0:
            limit = 800
    except ValueError:
        limit = 800
        
    if start_line is not None or end_line is not None:
        s = 1 if start_line is None else int(start_line)
        e = total_lines if end_line is None else int(end_line)
        
        s = max(1, min(s, total_lines)) if total_lines > 0 else 1
        e = max(s, min(e, total_lines)) if total_lines > 0 else 1
        
        requested_count = e - s + 1
        if requested_count > 1000:
            e = s + 1000 - 1
            truncated_lines = lines[s-1:e]
            content = "".join(truncated_lines)
            content += f"\n\n[File Truncated: Read range lines {s}-{e} of {total_lines} total lines. Requested range exceeded the maximum limit of 1000 lines.]"
            return content
        else:
            truncated_lines = lines[s-1:e]
            return "".join(truncated_lines)
    else:
        if total_lines > limit:
            truncated_lines = lines[:limit]
            content = "".join(truncated_lines)
            content += f"\n\n[File Truncated: Read lines 1-{limit} of {total_lines} total lines. Use read_file with start_line and end_line parameters to read remaining segments, e.g. start_line={limit+1}, end_line={min(limit * 2, total_lines)}.]"
            return content
        else:
            return "".join(lines)


@tool
async def read_file(path: str, start_line: int = None, end_line: int = None, risk_level: str = "low", risk_description: str = "") -> str:
    """Reads the contents of a file on the user's system.
    
    Paths can be absolute or relative to the working directory. For large files, specify start_line and end_line (1-indexed, inclusive) to avoid context bloat.
    
    Args:
        path: The filesystem path to read.
        start_line: Optional starting line number (1-indexed, inclusive).
        end_line: Optional ending line number (1-indexed, inclusive).
        risk_level: The security risk level of the read. MUST be one of: 'safe', 'low', 'moderate', or 'critical'.
        risk_description: A brief explanation of the risk. Must be provided if risk_level is 'moderate' or 'critical'.
    """
    # Resolve path & check sensitivity
    resolved_path, is_sensitive = resolve_and_check_sensitivity(path, SENSITIVE_READ_PATHS)
    
    level = risk_level.lower().strip()
    desc = risk_description.strip()
    if is_sensitive:
        level = "critical"
        warning = f"Accessing sensitive system path: {resolved_path}"
        desc = f"[System Warning] {warning} | [Model Reason] {desc}" if desc else f"[System Warning] {warning}"
        
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
            return read_file_content(resolved_path, start_line, end_line)
        except PermissionError as e:
            return f"Error: Permission denied reading file '{resolved_path}'. Details: {str(e)}"
        except Exception as e:
            return f"Error: Failed to read file '{resolved_path}'. Details: {str(e)}"

    # Prompt user for confirmation
    action, comment = prompt_file_confirmation("READ", resolved_path, risk_level=level, risk_description=desc, start_line=start_line, end_line=end_line)
    
    if action == "no":
        return "Error: Read operation rejected by user."
    elif action == "comment":
        return f"Error: Read operation rejected by user. Feedback: {comment}"
        
    try:
        return read_file_content(resolved_path, start_line, end_line)
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
        warning = f"Writing to sensitive system path: {resolved_path}"
        desc = f"[System Warning] {warning} | [Model Reason] {desc}" if desc else f"[System Warning] {warning}"
    elif is_outside_workspace(resolved_path):
        level = "critical"
        warning = f"Writing to path outside launching workspace directory ({session_state.initial_cwd}): {resolved_path}"
        desc = f"[System Warning] {warning} | [Model Reason] {desc}" if desc else f"[System Warning] {warning}"
        
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
        warning = f"Editing sensitive system file: {resolved_path}"
        desc = f"[System Warning] {warning} | [Model Reason] {desc}" if desc else f"[System Warning] {warning}"
    elif is_outside_workspace(resolved_path):
        level = "critical"
        warning = f"Editing file outside launching workspace directory ({session_state.initial_cwd}): {resolved_path}"
        desc = f"[System Warning] {warning} | [Model Reason] {desc}" if desc else f"[System Warning] {warning}"
        
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


