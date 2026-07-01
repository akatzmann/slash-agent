# Native LLM Agent PowerShell Integration
# Sourced via: . "$HOME\.slash-agent\bin\slash-agent.ps1"

# Resolve package root relative to this sourced script's location
$SlashAgentRoot = Split-Path -Parent $PSScriptRoot

function _agent_run {
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$AgentArgs
    )

    # 1. Intercept configuration flags instantly
    if ($AgentArgs -and ($AgentArgs[0] -eq "--configure" -or $AgentArgs[0] -eq "-c")) {
        # Run the powershell installer in configure mode
        & "$SlashAgentRoot\bin\installer.ps1" -Configure
        return
    }

    # Generate temporary files
    $ContextFile = [System.IO.Path]::GetTempFileName()
    $SyncFile = [System.IO.Path]::GetTempFileName()

    # 2. Capture recent command history (PSReadLine integration)
    $HistCommands = if ($env:AGENT_HISTORY_COMMANDS) { [int]$env:AGENT_HISTORY_COMMANDS } else { 20 }
    
    if (Get-Command Get-PSReadLineOption -ErrorAction SilentlyContinue) {
        $HistoryPath = (Get-PSReadLineOption).HistorySavePath
        if (Test-Path $HistoryPath) {
            Get-Content $HistoryPath -Tail $HistCommands | Out-File -FilePath $ContextFile -Encoding utf8
        } else {
            Get-History -Count $HistCommands | ForEach-Object { $_.CommandLine } | Out-File -FilePath $ContextFile -Encoding utf8
        }
    } else {
        Get-History -Count $HistCommands | ForEach-Object { $_.CommandLine } | Out-File -FilePath $ContextFile -Encoding utf8
    }

    # 3. Invoke Python Orchestrator
    $env:PYTHONPATH = $SlashAgentRoot
    $PythonExe = Join-Path $SlashAgentRoot ".venv\Scripts\python.exe"
    if (!(Test-Path $PythonExe)) {
        # Support Linux/macOS pwsh installations
        $PythonExe = Join-Path $SlashAgentRoot ".venv/bin/python3"
    }

    & $PythonExe -m slash_agent.main `
        --context-file $ContextFile `
        --sync-file $SyncFile `
        --shell powershell `
        $AgentArgs

    # 4. Synchronize environment and directory state
    if (Test-Path $SyncFile -PathType Leaf) {
        . $SyncFile
        Remove-Item $SyncFile -ErrorAction SilentlyContinue
    }

    # Cleanup temporary context file
    if (Test-Path $ContextFile) {
        Remove-Item $ContextFile -ErrorAction SilentlyContinue
    }
}

# Register command shortcuts
function /agent { _agent_run $args }
function agent { _agent_run $args }

Write-Host "[slash-agent] Native integration active. Type '/agent <task>' or 'agent <task>' to use." -ForegroundColor Green
