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
from typing import Dict, Any, Tuple
from py_agent_core.tool import tool

# Regex to strip ANSI color and formatting codes
ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

class ShellState:
    """State tracker for the active agent shell session."""
    def __init__(self):
        self.cwd = os.getcwd()
        self.env_vars = os.environ.copy()
        self.dry_run = False
        self.auto_confirm = False

# Global session state singleton
session_state = ShellState()

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

def prompt_user_confirmation(command: str) -> Tuple[str, str]:
    """Prompts the user to confirm, edit, or comment on a proposed command.
    
    Returns:
        A tuple of (action, payload) where action is 'yes', 'no', 'edit', or 'comment'.
    """
    print(f"\n\033[1;33m[Agent] Proposed Command:\033[0m")
    print(f"  $ {command}\n")
    print("\033[1;36mConfirm action: [y]es / [n]o / [e]dit / [c]omment ? \033[0m", end="", flush=True)
    
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

def run_command_in_pty(command: str) -> Tuple[int, str]:
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

@tool
async def execute_command(command: str) -> str:
    """Executes a shell command on the user's system, preserving directory context.
    
    Args:
        command: The command line string to run in bash (e.g. 'npm run build').
    """
    if session_state.dry_run:
        print(f"\n\033[1;34m[Dry-run] Would execute:\033[0m {command}")
        return f"Command execution simulated. Result: Exit code 0, Output: (Dry-run simulated)"
        
    if session_state.auto_confirm:
        print(f"\n\033[1;32m[Agent Running]:\033[0m {command}")
        exit_code, output = run_command_in_pty(command)
        return f"Exit code: {exit_code}\nOutput:\n{output}"
        
    # Prompt the user for confirmation
    action, cmd_to_run = prompt_user_confirmation(command)
    
    if action == "no":
        return "Command rejected by user: User refused execution."
    elif action == "comment":
        return f"Command rejected by user. Feedback: {cmd_to_run}"
    
    # Run the accepted or edited command
    if action == "edit":
        print(f"\033[1;32m[Agent Running Edited Command]:\033[0m {cmd_to_run}")
    else:
        print(f"\033[1;32m[Agent Running]:\033[0m {cmd_to_run}")
        
    exit_code, output = run_command_in_pty(cmd_to_run)
    return f"Exit code: {exit_code}\nOutput:\n{output}"

@tool
async def request_user_input(prompt: str) -> str:
    """Prompts the user directly in the terminal to ask a clarifying question or request input.
    
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

