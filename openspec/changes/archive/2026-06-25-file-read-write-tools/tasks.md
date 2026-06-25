## 1. Shared Safety Infrastructure

- [x] 1.1 Define `SENSITIVE_READ_PATHS` list in `tools.py` covering `/etc/shadow`, `/etc/passwd`, `/etc/sudoers`, `/etc/sudoers.d/`, `/etc/ssh/`, `/.ssh/`, `/.gnupg/`, `/proc/`, `/sys/`, `/dev/`, `/.aws/credentials`, `/.aws/config`, `/.config/gcloud/`, `/.kube/config`
- [x] 1.2 Define `SENSITIVE_WRITE_PATHS` as superset of `SENSITIVE_READ_PATHS`, adding `/etc/`, `/usr/`, `/bin/`, `/sbin/`, `/lib/`, `/lib64/`, `/boot/`
- [x] 1.3 Implement `resolve_and_check_sensitivity(path, sensitive_list)` helper: resolve symlinks via `os.path.realpath()` (using parent dir if path doesn't exist), return `(resolved_path, is_sensitive: bool)`
- [x] 1.4 Implement `countdown_warning(path)` helper: read delay from `SLASH_AGENT_UNSAFE_DELAY` env var (default 5, fallback to 5 on invalid), print `[⚠ UNSAFE-YES]` warning, count down one second at a time, raise `KeyboardInterrupt` on Ctrl+C
- [x] 1.5 Implement `prompt_file_confirmation(operation, path, risk_level, risk_description, preview=None)` helper: display operation type (`READ`/`WRITE`/`EDIT`), resolved path, optional preview block, color-coded risk, and prompt `[y]es / [n]o / [c]omment`; return `("yes"|"no"|"comment", payload)`

## 2. read_file Tool

- [x] 2.1 Add `@tool async def read_file(path, risk_level, risk_description)` to `tools.py`
- [x] 2.2 Reject non-absolute paths with a descriptive error return (no file access)
- [x] 2.3 Resolve path with `resolve_and_check_sensitivity(path, SENSITIVE_READ_PATHS)`; override risk to `critical` if sensitive
- [x] 2.4 Apply tiered auto-confirm: `low`/`moderate` → auto with `-y` or `--unsafe-yes`; `critical` → auto with countdown under `--unsafe-yes`, prompt under `-y` (or no flags)
- [x] 2.5 On auto-confirm (excluding critical), print `[Agent Reading] /resolved/path` one-liner before returning content
- [x] 2.6 Call `prompt_file_confirmation("READ", ...)` when confirmation is required; handle `comment` response
- [x] 2.7 On confirm (or auto-confirm with countdown for critical under `--unsafe-yes`), read and return file content; on reject or comment, return appropriate message

## 3. write_file Tool

- [x] 3.1 Add `@tool async def write_file(path, content, risk_level, risk_description)` to `tools.py`
- [x] 3.2 Reject non-absolute paths with a descriptive error return (no file access)
- [x] 3.3 Resolve path with `resolve_and_check_sensitivity(path, SENSITIVE_WRITE_PATHS)`; override risk to `critical` if sensitive
- [x] 3.4 Apply tiered auto-confirm: `low`/`moderate` → auto with `-y` or `--unsafe-yes`; `critical` → auto with countdown under `--unsafe-yes`, prompt under `-y` (or no flags)
- [x] 3.5 If `--dry-run` is active, print simulation notice with path and return without writing
- [x] 3.6 Call `prompt_file_confirmation("WRITE", ..., preview=first_10_lines(content))` when confirmation is required; handle `comment` response
- [x] 3.7 On critical write: if `--unsafe-yes` is active, run `countdown_warning(path)`; if prompting is required, wait for confirm and then run countdown if `--unsafe-yes` is active; catch `KeyboardInterrupt` to abort cleanly
- [x] 3.8 On confirm/auto-confirm, create parent directories with `os.makedirs(exist_ok=True)`, write content, return success message
- [x] 3.9 Catch `PermissionError` and return descriptive error message to LLM; do not propagate raw exception
- [x] 3.10 On reject or comment, return appropriate message

## 4. edit_file Tool

- [x] 4.1 Add `@tool async def edit_file(path, old_str, new_str, risk_level, risk_description)` to `tools.py`
- [x] 4.2 Reject non-absolute paths with a descriptive error return
- [x] 4.3 Return error if file does not exist
- [x] 4.4 Read file content; count occurrences of `old_str` (exact literal match)
  - [x] 4.4a If count == 0: return "string not found" error
  - [x] 4.4b If count > 1: return "ambiguous match" error with instruction to add more context
- [x] 4.5 Resolve path with `resolve_and_check_sensitivity(path, SENSITIVE_WRITE_PATHS)`; override risk to `critical` if sensitive
- [x] 4.6 Apply same tiered auto-confirm as `write_file`
- [x] 4.7 If `--dry-run` is active, print simulation notice with diff and return without writing
- [x] 4.8 Build unified diff of old content → new content using `difflib.unified_diff`; call `prompt_file_confirmation("EDIT", ..., preview=unified_diff_str)` when confirmation required; handle `comment` response
- [x] 4.9 On critical edit: if `--unsafe-yes` is active, run `countdown_warning(path)`; if prompting is required, wait for confirm and then run countdown if `--unsafe-yes` is active; catch `KeyboardInterrupt` to abort cleanly
- [x] 4.10 On confirm/auto-confirm, apply `content.replace(old_str, new_str, 1)`, write back to file, return success message with path
- [x] 4.11 Catch `PermissionError` and return descriptive error message to LLM

## 5. Agent Registration & System Prompt

- [x] 5.0 Update `execute_command` in `tools.py` to run the countdown warning when executing a `critical` command under `--unsafe-yes`
- [x] 5.1 Import `read_file`, `write_file`, and `edit_file` in `main.py`
- [x] 5.2 Add all three tools to the `tools` list in the `Agent` initialisation
- [x] 5.3 Extend system prompt with a directive to use native file tools (`read_file`, `write_file`, `edit_file`) instead of shell commands (`cat`, `tee`, `echo >>`)
- [x] 5.4 Add guidance in system prompt that all file paths MUST be absolute
- [x] 5.5 Add guidance that `edit_file` is preferred over `write_file` when modifying existing files

## 6. Verification

- [x] 6.1 Manual test: `read_file` with relative path → error returned, no file read
- [x] 6.2 Manual test: `read_file("/etc/shadow", risk_level="low")` with `-y` → risk overridden to `critical`, prompt shown (since `-y` prompts for critical)
- [x] 6.3 Manual test: `read_file` on project file with `-y` → one-liner printed, content returned, no prompt
- [x] 6.4 Manual test: `write_file` on project file with `-y` → auto-confirmed for `low` risk
- [x] 6.5 Manual test: `write_file` on project file with `risk_level="moderate"` and `-y` → auto-confirmed, no prompt
- [x] 6.6 Manual test: `write_file` on project file with `risk_level="moderate"` and `--unsafe-yes` → auto-confirmed, no prompt
- [x] 6.7 Manual test: `write_file("/etc/hosts", ...)` with `--unsafe-yes` → auto-confirmed with countdown warning, Ctrl+C during countdown aborts write
- [x] 6.8 Manual test: `SLASH_AGENT_UNSAFE_DELAY=2 write_file("/etc/hosts", ...)` with `--unsafe-yes` → countdown is 2 seconds
- [x] 6.9 Manual test: `write_file` on project file with `--dry-run` → no file written
- [x] 6.10 Manual test: `edit_file` with `old_str` not in file → "string not found" error
- [x] 6.11 Manual test: `edit_file` with `old_str` appearing twice → "ambiguous match" error
- [x] 6.12 Manual test: `edit_file` with unique `old_str` → diff shown at confirmation, edit applied on yes
- [x] 6.13 Verify agent uses `read_file` instead of `cat` when asked to inspect a file
- [x] 6.14 Verify agent uses `edit_file` instead of `write_file` for partial modifications to existing files
- [x] 6.15 Manual test: `execute_command` with a critical command (e.g. `rm -rf`) under `--unsafe-yes` → executes with countdown warning
