## Context

`slash_agent/tools.py` currently provides three tools to the LLM: `execute_command`, `request_user_input`, and `read_skill_instructions`. The agent has no native file I/O — to read a file it runs `cat`, to write one it runs `tee` or `echo >>`. This means file operations bypass the file-specific safety model described in the proposal and are indistinguishable from any other shell command in terms of confirmation UX.

The existing `execute_command` implementation establishes the pattern we are extending: LLM-supplied `risk_level`/`risk_description` fields, a Python-level pattern-override safeguard layer, tiered auto-confirm behaviour keyed to session flags, and a shared `prompt_user_confirmation()` helper. File operations will follow the same pattern with calibrated differences reflecting the irreversibility asymmetry between reads and writes.

## Goals / Non-Goals

**Goals:**
- Add `read_file`, `write_file`, and `edit_file` as first-class `@tool` functions
- Enforce absolute paths on all three tools (reject relative paths with a descriptive error)
- Apply a Python-level sensitive-path safeguard layer that upgrades the LLM's risk assessment to `critical` for known-sensitive locations, using `os.path.realpath()` to resolve symlinks before matching
- Wire auto-confirm tiers: `-y` auto-confirms `low` and `moderate` risk operations (both shell commands and file tools); `--unsafe-yes` additionally auto-confirms `critical` risk operations
- Add a configurable countdown (default 5 s, env var `SLASH_AGENT_UNSAFE_DELAY`) + warning for any `critical`-classified operation (both shell commands and file reads/writes/edits) executed under `--unsafe-yes`
- Auto-confirmed reads print a one-liner `[Agent Reading] /path` (not silent)
- File confirmation prompt offers `[y]es / [n]o / [c]omment`; write/edit show content preview or diff respectively
- Suppress writes and edits (not reads) in `--dry-run` mode
- `edit_file` performs exact-match replacement with uniqueness validation and shows a unified diff at confirmation
- `write_file` auto-creates parent directories
- Extend system prompt to instruct the LLM to prefer native file tools over shell-based file I/O

**Non-Goals:**
- User-editable sensitive path blocklist (deferred — safe design requires additive-only extension, out of scope for this change)
- ACL or per-directory allow/block-list configuration
- Read size limits (deferred — left to LLM judgment for now)
- Sandboxing or containerisation
- Fuzzy or AST-aware matching in `edit_file`

## Decisions

### Decision 1: Absolute paths only — enforced in Python, not just instructed in system prompt

**Rationale:** Relative paths create two risks: (1) ambiguity about what the agent is actually accessing (LLM may think CWD is different from reality after `cd` commands), and (2) prompt-injection opportunity via path traversal (`../../.ssh/id_rsa`). Rejecting relative paths in the tool body with a clear error message forces the LLM to fully qualify all file arguments, making the confirmation dialog unambiguous.

**Alternative considered:** Resolve relative paths against `session_state.cwd` silently. Rejected — this hides the actual path from the user confirmation step if the agent is working in an unexpected directory.

### Decision 2: Symlink resolution before sensitive-path matching

**Rationale:** A malicious or confused prompt could craft `/home/user/myshadow → /etc/shadow` to bypass pattern matching on the raw path. Using `os.path.realpath()` before checking against the sensitive-path list ensures the actual file location determines the risk level. For paths that don't yet exist, the parent directory is resolved instead.

**Alternative considered:** Check only the raw path. Rejected — trivially bypassable via symlinks.

### Decision 3: Fully unified auto-confirm matrix across shell commands and file tools

```
                    SHELL / READ / WRITE / EDIT
low risk         → auto (-y or --unsafe-yes)
moderate risk    → auto (-y or --unsafe-yes)
critical risk    → prompt (no flags) or auto + countdown (--unsafe-yes)
```

**Rationale:** Users expect flags to have the same meaning across all capabilities. Aligning standard `-y` to auto-confirm both `low` and `moderate` risk operations, and `--unsafe-yes` to auto-confirm `critical` risk operations (subject to a countdown safety delay) ensures complete consistency.

**Alternative considered:** Keep different confirmation rules for file tools. Rejected — this introduces complexity, and since shell execution can read/write/edit files, any strictness in the file tools is easily bypassed by running shell commands.

### Decision 4: Countdown duration is configurable via `SLASH_AGENT_UNSAFE_DELAY`

**Rationale:** 5 seconds is the right default — long enough to catch a finger-slip, short enough not to be annoying. But scripted or CI use cases may want 0, and extra-cautious users may want 10. An env var costs one line of code and respects user preferences.

**Default:** `SLASH_AGENT_UNSAFE_DELAY=5` (seconds). Must be a non-negative integer; invalid values fall back to default.

### Decision 5: Countdown fires on critical operations only (not moderate)

**Rationale:** Moderate operations auto-confirm silently under standard `-y` and `--unsafe-yes`. Adding a countdown for moderate operations would make standard operations feel sluggish and frustrate automated use cases. The countdown is reserved strictly for `critical`-classified operations (dangerous shell commands, critical files, boot configurations, credentials) where a 5-second abort window is appropriate and expected.

### Decision 6: Auto-confirmed reads print a one-liner

**Rationale:** Fully silent reads (like `read_skill_instructions`) make sense for internal tool infrastructure. For user-facing `read_file`, silent auto-confirm would mean the agent could be reading arbitrary files with no terminal evidence. A one-liner `[Agent Reading] /path/to/file` provides a lightweight audit trace without interrupting flow.

### Decision 7: File confirmation prompt offers `[y]es / [n]o / [c]omment`

**Rationale:** The shell `execute_command` prompt also offers `[e]dit`, but editing a file path mid-prompt doesn't have a useful analogy for file ops (the agent would need to re-call the tool with the corrected path). `[c]omment` is retained because it gives the user a channel to redirect the agent ("use a different file" or "wrong content") without having to wait for the tool to finish. `[e]dit` is omitted.

### Decision 8: `edit_file` uses exact-match + uniqueness check

**Rationale:** The `old_str` must appear exactly once in the file. If 0 occurrences → error "string not found". If >1 occurrences → error "ambiguous match, provide a more specific snippet". This avoids silent wrong-edit bugs without requiring fuzzy matching. The LLM is responsible for including enough surrounding context to make the match unique. Confirmation shows a `difflib.unified_diff` so the user sees the precise change.

**Alternative considered:** Line-number ranges (`start_line`, `end_line`). Rejected — line numbers are fragile and require the LLM to track them accurately, which it often doesn't across multi-step edits.

**Alternative considered:** Fuzzy/semantic matching. Rejected — out of scope, adds external dependencies, harder to audit.

### Decision 9: Sensitive path lists live in `tools.py` only (hardcoded, not user-editable in this change)

**Rationale:** The lists cover universally dangerous UNIX paths. User-editable extension would need to be strictly additive (users can never remove `/etc/shadow` from the critical list), which requires a more careful design. Deferred to a follow-up change.

**Lists:**

```python
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
```

### Decision 10: Shared `prompt_file_confirmation()` helper — separate from shell confirmation

**Rationale:** `execute_command`'s `prompt_user_confirmation()` renders the command string and offers `[e]dit`. File operations need a different display: operation type (`READ`/`WRITE`/`EDIT`), path, risk, and a content preview or diff. A separate helper keeps each confirmation dialog tailored without complicating the existing shell confirmation path.

Write/edit confirmation includes a content preview (first 10 lines of new content for writes; unified diff for edits). Read confirmation shows path and risk only.

### Decision 11: `write_file` auto-creates parent directories

**Rationale:** This matches the expectation of every editor and `tee`. The confirmation prompt already shows the full resolved path, so the user can abort if the directory structure looks wrong. Failing on missing parent dirs would be unnecessary friction.

### Decision 12: Permission errors return a clear error message to the LLM

**Rationale:** If `write_file` or `edit_file` hits a permission error (file owned by root, read-only filesystem), the tool returns a descriptive error string to the LLM so it can report the problem to the user or suggest `sudo`-based alternatives via shell exec. Propagating raw OS exceptions would produce confusing output.

## Risks / Trade-offs

- **LLM under-classifies risk** → Mitigated by Python safeguard layer that overrides to `critical` for known-sensitive paths regardless of LLM input
- **Context window explosion from large files** → Not mitigated in this change; deferred. LLM instructed to be sensible about file sizes
- **TOCTOU window between realpath check and actual read/write** → Acceptable risk for a CLI tool; full mitigation requires kernel-level file descriptor locking, which is out of scope
- **Agent falls back to shell writes to avoid confirmation friction** → Mitigated by system prompt instruction; cannot be fully prevented but is the same baseline risk as today
- **`edit_file` old_str ambiguity in large files** → Mitigated by uniqueness check with a clear error directing the LLM to supply a more specific snippet

## Open Questions

- Should there be a follow-up change adding a user-editable additive sensitive-path blocklist (global `~/.config/slash-agent/sensitive-paths` + project-local `.agent/sensitive-paths`)?
