## Context

The slash-agent is currently designed for POSIX-compliant environments, using pseudo-terminals (PTYs) and shell wrapper sourcing. To run natively under Windows and cross-platform PowerShell (without WSL2), we must introduce non-POSIX execution logic, PowerShell state-capture wrapper scripts, and profile integration.

## Goals / Non-Goals

**Goals:**
- Enable native installation and execution of slash-agent on Windows hosts via Windows PowerShell (5.1) and PowerShell Core (7+).
- Support cross-platform PowerShell Core installations on Linux/macOS (edge case).
- Ensure zero regression on existing Unix-like environments (Bash, Zsh, Ksh, Fish).
- Synchronize directory context and environment variables bidirectionally.

**Non-Goals:**
- Supporting Windows CMD (`cmd.exe`).
- Emulating full interactive CLI applications (e.g. `vim`, `nano`) on Windows, as doing so requires complex Windows pseudo-console (ConPTY) native library integrations. Standard CLI tools (git, npm, python, etc.) will run natively.

## Decisions

### 1. Sourcing and Shell Wrapper Integration
- **Decision**: Create `bin/slash-agent.ps1` for PowerShell integration, using `. $SyncFile` for environment/working directory syncing.
- **Alternatives Considered**: Using a Python wrapper launcher. Rejected because Python processes cannot directly modify the environment or working directory of their parent shell session.

### 2. Cross-Platform Executions (Bypassing POSIX `pty`)
- **Decision**: On Windows (`sys.platform == 'win32'`), execution falls back to a non-interactive `subprocess.Popen` bridge that runs standard PowerShell. The output is streamed from stdout in real-time, and exit codes and path/environment shifts are returned.
- **Alternatives Considered**:
  - Requiring `pywinpty` binary dependency. Rejected to keep the installer lightweight and avoid compiling native binaries during install.
  - Running WSL2 only. Rejected since native execution is the primary request.

### 3. Model Environment Awareness (Prompt Formatting)
- **Decision**: Dynamically prepend host metadata (Operating System, Active Shell, Path Separator, CWD) to the system prompt in `main.py` using a tight, constraint-based template to prevent command-generation and path-formatting failures on Windows.

### 4. PowerShell Environment Sync Syntax
- **Decision**: Write `$env:KEY = 'value'` and `Remove-Item Env:\KEY` to the sync file, utilizing a single-quote escaping function `pwsh_quote(val)`.

## Risks / Trade-offs

- **[Risk] Execution Policy Restrictions** → Mitigation: Instruct the user to run the installer using `-ExecutionPolicy Bypass`.
- **[Risk] Interactive commands blocking standard input** → Mitigation: Run PowerShell subprocesses with `-NonInteractive`. Interactive commands will error cleanly rather than hanging the agent shell session.
- **[Risk] Windows vs Unix Path Mismatch** → Mitigation: Prepend path separator constraints to the system prompt and normalize path strings to `/` in python security guardrails.
