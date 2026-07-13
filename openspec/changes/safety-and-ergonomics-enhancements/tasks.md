## 1. Native Safety & File Tools Updates

- [ ] 1.1 Augment risk descriptions in `execute_command`, `read_file`, `write_file`, and `edit_file` inside `slash_agent/tools.py` instead of overwriting them.
- [ ] 1.2 Add `start_line` and `end_line` optional arguments to `read_file` inside `slash_agent/tools.py`.
- [ ] 1.3 Add default 800-line limit truncation logic to `read_file` with detailed metadata notices containing total line count and paging instructions.
- [ ] 1.4 Update model system prompts in `slash_agent/main.py` with rules to use target-specific parameters and line ranges.

## 2. Command Execution & Logging Updates

- [ ] 2.1 Integrate unified transient logging to `tempfile.gettempdir()` for all PTY subprocess executions, enforcing owner-only (0o600 or equivalent) file permissions on log directories and files.
- [ ] 2.2 Add selective output streaming logic in `tools.py` that collapses verbose PTY displays to status indicators and logs previews to the agent.
- [ ] 2.3 Add `--silent` parameter support in `slash_agent/main.py` and pass it to tools to suppress terminal outputs.
- [ ] 2.4 Add auto-dump logic for silent/selective runs on execution failure (non-zero exit code).

## 3. Documentation Updates

- [ ] 3.1 Create `docs/security_model.md` detailing the security architecture, risk tiers, and sandbox controls.
- [ ] 3.2 Update `SECURITY.md` supported versions to reflect `v0.2.x` and link to `docs/security_model.md`.
- [ ] 3.3 Add links to `docs/security_model.md` from `README.md`.

## 4. Verification

- [ ] 4.1 Write unit tests for line-bounded reads and truncation alerts.
- [ ] 4.2 Validate cross-platform transient logs, process bindings, and log file permission masks (0o600) manually in terminal.
