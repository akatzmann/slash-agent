# Security Model & Architecture

This document describes the security architecture, sandbox boundaries, and user consent gates implemented in `slash-agent`.

## Core Security Philosophy
`slash-agent` operates on the host system as the executing user. It does not run with elevated privileges unless run under `sudo`. Because it runs locally, protecting sensitive system files and user credentials is a high priority.

The agent enforces security via a hybrid model of **static path blocklists**, **dynamic command inspection**, and **user-in-the-loop confirmation gates**.

---

## 1. Safety Gating and Risk Levels
All tool executions are classified into one of four Risk Levels:

| Risk Level | Description | Consent Requirement |
|:---|:---|:---|
| `safe` | Read-only operations on non-sensitive paths or lightweight commands. | Executed immediately without prompt if auto-confirm is enabled. |
| `low` | Standard file reads/writes inside the workspace. | Executed immediately without prompt if auto-confirm is enabled. |
| `moderate` | Script execution, execution of external CLI runners (e.g. `npx`, `npm run`), or targeted code edits. | Requires confirmation (or countdown warning if unsafe auto-confirm is active). |
| `critical` | Deleting files, modifying files outside the workspace, administrative commands (`sudo`), or accessing sensitive paths. | Always requires user confirmation (countdown warning only if explicitly overridden by `--unsafe-yes`). |

---

## 2. Sensitive Path Restrictions
`slash-agent` maintains explicit list of sensitive read and write paths. These checks are resolved to real paths (resolving symlinks and relative references) before evaluation to prevent traversal attacks.

### Sensitive Read Paths:
- `/etc/shadow`, `/etc/passwd`, `/etc/sudoers`, `/etc/sudoers.d/`
- Private keys (`~/.ssh/*`)
- Private configuration directories (`~/.aws/`, `~/.config/gcloud/`, `~/.kube/`)
- System interface directories (`/proc/`, `/sys/`, `/dev/`)

### Sensitive Write Paths:
- All sensitive read paths.
- System binary directories (`/etc/`, `/usr/`, `/bin/`, `/sbin/`, `/lib/`, `/lib64/`).

If the model attempts to read, write, or edit files in these directories, the operation is automatically escalated to the `critical` risk level, prompting the user with a red warning before execution.

---

## 3. Transient Logs Security
During execution, the stdout and stderr streams of commands are logged to files inside `tempfile.gettempdir() + "/slash-agent"`. 
- **Owner-Only Permissions:** All generated log files and directories are created with strict permissions (`0o700` for the directory, `0o600` for files). Other users on the system cannot read or write to these logs.
- **Log Collapsing:** Large command outputs (>50KB or 500 lines) are collapsed in the terminal window to prevent terminal lockup and save screen space. The full log files remain accessible inside the temporary directory.

---

## 4. Environment and PTY Execution
Command execution occurs inside a pseudo-terminal (PTY) subshell:
- Working directory (`cwd`) and environment variables are synchronized back to the main python orchestration context after each execution.
- Command execution is bound to the parent terminal window's size (handling `SIGWINCH` dynamically).
- Destructive commands are inspected statically by a regex scanner and elevated to critical risk if matched (e.g., `rm -rf`, `sudo`, `mkfs`, `dd`).
