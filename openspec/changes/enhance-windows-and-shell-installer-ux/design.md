## Context

Installing `slash-agent` on plain Windows environments encountered friction due to strict Windows security controls (AMSI memory scanning, default `ExecutionPolicy Restricted`), zero-byte Microsoft Store Python app execution aliases, and immediate exit on missing prerequisites.

## Goals / Non-Goals

**Goals:**
* Automate `winget` installation of missing `git` and `Python.Python.3` in `installer.ps1` with in-memory `$env:Path` environment refresh.
* Detect Microsoft Store App Execution Alias false-positives by running functional execution test `python -c "import sys"`.
* Update README.md quickstart snippets to use disk-backed Download-and-Run (`iwr ... -OutFile $env:TEMP\installer.ps1; & $env:TEMP\installer.ps1`) or `git clone` to bypass Defender AMSI `irm | iex` heuristics.
* Automatically call `Unblock-File` on `slash-agent.ps1` and prompt/auto-set `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` when script execution is disabled.
* Provide current-session dot-sourcing activation notices at the end of installation.
* Ensure documentation, installer scripts (`installer.ps1`, `installer.sh`), and raw branch URLs (`main`) remain in total sync across PowerShell, Bash, Zsh, Ksh, and Fish environments.

**Non-Goals:**
* Modifying core Python agent orchestration logic in `slash_agent/main.py`.

## Technical Approach & Architecture

### 1. Functional Python Validation & `winget` Auto-Installer (`bin/installer.ps1`)
```powershell
# Functional Python test helper
function Test-PythonFunctionality($cmd) {
    if (!(Get-Command $cmd -ErrorAction SilentlyContinue)) { return $false }
    $val = & $cmd -c "import sys; print(sys.version_info[0])" 2>$null
    return ($LASTEXITCODE -eq 0 -and $val.Trim() -eq "3")
}

# Live PATH refresh helper
function Refresh-ProcessPath {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}
```

### 2. Execution Policy & NTFS Zone Unblocking (`bin/installer.ps1`)
```powershell
# Unblock NTFS Zone.Identifier stream
if (Test-Path "$InstallDir\bin\slash-agent.ps1") {
    Unblock-File -Path "$InstallDir\bin\slash-agent.ps1" -ErrorAction SilentlyContinue
}

# ExecutionPolicy check & CurrentUser fallback
$CurrentEP = Get-ExecutionPolicy -Scope CurrentUser
if ($CurrentEP -in @("Restricted", "Undefined")) {
    $SysEP = Get-ExecutionPolicy
    if ($SysEP -in @("Restricted", "AllSigned")) {
        if ($IsInteractive) {
            $choice = Read-Host "PowerShell script execution is restricted. Enable RemoteSigned for CurrentUser? [Y/n]"
            if ($choice -ne "n") {
                Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
            }
        }
    }
}
```

### 3. AMSI Defender Anti-False-Positive Strategy (`README.md` & `docs/documentation.md`)
* Replace `powershell -ExecutionPolicy Bypass -Command "irm ... | iex"` with:
  ```powershell
  powershell -ExecutionPolicy Bypass -Command "iwr https://raw.githubusercontent.com/akatzmann/slash-agent/main/bin/installer.ps1 -OutFile $env:TEMP\installer.ps1; & $env:TEMP\installer.ps1; Remove-Item $env:TEMP\installer.ps1"
  ```
* Standardize raw repository URLs across all files to `main`.

## Risks & Trade-offs

* **[Risk]** `winget` absent on older Windows Server / LTSC builds without App Installer.
  * *Mitigation:* Wrap `winget` invocation in `if (Get-Command winget -ErrorAction SilentlyContinue)`. If `winget` is missing, gracefully print standard manual download URLs (`https://git-scm.com/download/win`, `https://www.python.org/downloads/windows/`).
