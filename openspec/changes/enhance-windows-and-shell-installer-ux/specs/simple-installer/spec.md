## ADDED Requirements

### Requirement: Automated Windows Prerequisite Resolution
The PowerShell installer (`installer.ps1`) SHALL functionally verify Python 3 and Git binaries, automatically prompting to install missing prerequisites via `winget` when available, and dynamically refreshing the process environment `$env:Path` to allow immediate use without restarting the shell.

#### Scenario: User runs installer on fresh Windows without Git or Python
- **WHEN** the user executes `installer.ps1` on a Windows system lacking Git or valid Python 3
- **THEN** the script offers to install missing components via `winget`, updates `$env:Path` in the current session, and proceeds with repository cloning and virtualenv setup.

### Requirement: Anti-AMSI Windows Quickstart Guidelines
The system documentation (`README.md` and `docs/documentation.md`) SHALL supply disk-backed Download-and-Run execution commands (`iwr ... -OutFile $env:TEMP\installer.ps1; & ...`) and `git clone` snippets for Windows installation to prevent Windows Defender AMSI memory-pipe false positives (`irm | iex`).

#### Scenario: User follows README Quickstart on Windows Defender
- **WHEN** a user copies and executes the Windows quickstart snippet from `README.md`
- **THEN** the script downloads to a temporary file, executes cleanly without triggering AMSI memory dropper alerts, and cleans up the temporary installer file.

### Requirement: ExecutionPolicy and NTFS Zone Unblocking
The PowerShell installer (`installer.ps1`) SHALL call `Unblock-File` on `slash-agent.ps1` upon installation and SHALL offer to configure `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` if script execution is restricted.

#### Scenario: Installer runs under Restricted ExecutionPolicy
- **WHEN** `installer.ps1` runs on a machine where script execution is restricted
- **THEN** it unblocks the script file, prompts/configures `RemoteSigned` for `CurrentUser`, and outputs instructions for activating `slash-agent` in the current session.
