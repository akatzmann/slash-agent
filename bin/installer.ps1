# slash-agent PowerShell Installer
# Can be run via: powershell -ExecutionPolicy Bypass -Command "irm <url>/bin/installer.ps1 | iex"

param(
    [switch]$Configure
)

# Default settings (can be overridden by environment variables)
$RepoUrl = if ($env:REPO_URL) { $env:REPO_URL } else { "https://github.com/akatzmann/slash-agent.git" }
$InstallDir = if ($env:INSTALL_DIR) { $env:INSTALL_DIR } else { Join-Path $env:USERPROFILE ".slash-agent" }
$Branch = if ($env:BRANCH) { $env:BRANCH } else { $null }

$UpdateMode = Test-Path $InstallDir

Write-Host "==============================================" -ForegroundColor Cyan
if ($Configure) {
    Write-Host "      Configuring slash-agent          " -ForegroundColor Cyan
} elseif ($UpdateMode) {
    Write-Host "      Updating slash-agent           " -ForegroundColor Cyan
} else {
    Write-Host "      Installing slash-agent           " -ForegroundColor Cyan
}
Write-Host "==============================================" -ForegroundColor Cyan

# Non-interactive / CI detection
$IsInteractive = [Environment]::UserInteractive -and !$env:NONINTERACTIVE -and !$env:CI

function Test-PythonCmd($cmd) {
    if (!(Get-Command $cmd -ErrorAction SilentlyContinue)) { return $false }
    $val = & $cmd -c "import sys; print(sys.version_info[0])" 2>$null
    return ($LASTEXITCODE -eq 0 -and $val -and $val.Trim() -eq "3")
}

function Refresh-ProcessPath {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

# 1. Prerequisite Verification
if (!$Configure) {
    Write-Host "Verifying prerequisites..."
    
    # Check Git
    if (!(Get-Command git -ErrorAction SilentlyContinue)) {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            $DoInstallGit = $true
            if ($IsInteractive) {
                $choice = Read-Host "Git is required but not installed. Install Git via winget now? [Y/n]"
                if ($choice -eq "n") { $DoInstallGit = $false }
            }
            if ($DoInstallGit) {
                Write-Host "Installing Git via winget..."
                winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
                Refresh-ProcessPath
            }
        }
        
        if (!(Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Error "Error: git is not installed. Please install Git manually from https://git-scm.com/download/win and try again."
            exit 1
        }
    }
    
    # Check Python 3 (functional execution test to bypass MS Store app execution alias)
    $PythonCmd = $null
    foreach ($candidate in @("python", "python3", "py")) {
        if (Test-PythonCmd $candidate) {
            $PythonCmd = $candidate
            break
        }
    }
    
    if (!$PythonCmd) {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            $DoInstallPy = $true
            if ($IsInteractive) {
                $choice = Read-Host "Python 3 is required but not installed (or points to MS Store alias). Install Python 3.12 via winget now? [Y/n]"
                if ($choice -eq "n") { $DoInstallPy = $false }
            }
            if ($DoInstallPy) {
                Write-Host "Installing Python 3.12 via winget..."
                winget install --id Python.Python.3.12 -e --source winget --accept-source-agreements --accept-package-agreements
                Refresh-ProcessPath
                foreach ($candidate in @("python", "python3", "py")) {
                    if (Test-PythonCmd $candidate) {
                        $PythonCmd = $candidate
                        break
                    }
                }
            }
        }
        
        if (!$PythonCmd) {
            Write-Error "Error: Python 3 is not installed (or points to Microsoft Store alias). Please install Python 3.10+ from https://www.python.org/downloads/windows/ and try again."
            exit 1
        }
    }
    
    Write-Host "Prerequisites verified successfully (Git & $PythonCmd)."
}

# 2. Repository Cloning and Setup
if ($Configure) {
    if (Test-Path $InstallDir) {
        Set-Location -LiteralPath $InstallDir
    } else {
        Write-Error "Error: slash-agent is not installed at $InstallDir. Please run installer without -Configure first."
        exit 1
    }
} else {
    if (Test-Path $InstallDir) {
        Write-Host "Target directory $InstallDir already exists."
        if (Test-Path (Join-Path $InstallDir ".git")) {
            Write-Host "Updating existing repository..."
            Set-Location -LiteralPath $InstallDir
            if ($Branch) {
                Write-Host "Switching to branch $Branch..."
                git checkout $Branch
            }
            git pull
        } else {
            Write-Host "Warning: Target directory exists but is not a git repository. Skipping repository update."
            Set-Location -LiteralPath $InstallDir
        }
    } else {
        Write-Host "Cloning repository to $InstallDir..."
        if ($Branch) {
            Write-Host "Cloning branch $Branch..."
            git clone -b $Branch $RepoUrl $InstallDir
        } else {
            git clone $RepoUrl $InstallDir
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Error: Failed to clone repository."
            exit 1
        }
        Set-Location -LiteralPath $InstallDir
    }
}

# 3. Virtual Environment & Dependency Setup
if (!$Configure) {
    $VenvPath = Join-Path $InstallDir ".venv"
    if (!(Test-Path $VenvPath)) {
        Write-Host "Creating Python virtual environment in .venv..."
        & $PythonCmd -m venv $VenvPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Error: Failed to create virtual environment."
            exit 1
        }
    }
    
    Write-Host "Installing Python dependencies..."
    $PipExe = Join-Path $VenvPath "Scripts\pip.exe"
    if (!(Test-Path $PipExe)) {
        # Support Linux/macOS pwsh setup fallback
        $PipExe = Join-Path $VenvPath "bin/pip"
    }
    
    & $PipExe install --upgrade pip
    & $PipExe install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Error: Failed to install Python dependencies."
        exit 1
    }
}

# 4. Interactive LLM Backend Configuration
function Get-ConfigPath {
    if ($env:SLASH_AGENT_CONFIG_FILE) {
        return $env:SLASH_AGENT_CONFIG_FILE
    }
    $HomeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
    if ($IsWindows -or ($env:OS -eq "Windows_NT")) {
        $ConfigDir = Join-Path $HomeDir ".config/slash-agent"
        return Join-Path $ConfigDir "env"
    } else {
        # Linux/macOS: match Python agent's get_config_path() which uses ".env"
        $XdgConfig = $env:XDG_CONFIG_HOME
        if ($XdgConfig) {
            $ConfigDir = Join-Path $XdgConfig "slash-agent"
        } else {
            $ConfigDir = Join-Path $HomeDir ".config/slash-agent"
        }
        return Join-Path $ConfigDir ".env"
    }
}

$ConfigPath = Get-ConfigPath

# Load current variables to pre-populate defaults for prompts
$AgentBackend = "ollama"
$AgentEndpoint = ""
$AgentModel = ""
$OpenaiApiKey = ""
$AzureOpenaiApiKey = ""
$AzureOpenaiApiVersion = "2025-04-01-preview"
$AgentThinkingLevel = "off"
$AgentTemperature = ""
$AgentTopP = ""

if (Test-Path $ConfigPath) {
    # Parse existing .env format config
    Get-Content $ConfigPath | ForEach-Object {
        $Line = $_.Trim()
        if ($Line -and !$Line.StartsWith("#") -and $Line -match "^([^=]+)=(.*)$") {
            $Key = $Matches[1].Trim()
            $Val = $Matches[2].Trim().Trim('"').Trim("'")
            if ($Key -eq "AGENT_BACKEND") { $AgentBackend = $Val }
            elseif ($Key -eq "AGENT_ENDPOINT") { $AgentEndpoint = $Val }
            elseif ($Key -eq "AGENT_MODEL") { $AgentModel = $Val }
            elseif ($Key -eq "OPENAI_API_KEY") { $OpenaiApiKey = $Val }
            elseif ($Key -eq "AZURE_OPENAI_API_KEY") { $AzureOpenaiApiKey = $Val }
            elseif ($Key -eq "AZURE_OPENAI_API_VERSION") { $AzureOpenaiApiVersion = $Val }
            elseif ($Key -eq "AGENT_THINKING_LEVEL") { $AgentThinkingLevel = $Val }
            elseif ($Key -eq "AGENT_TEMPERATURE") { $AgentTemperature = $Val }
            elseif ($Key -eq "AGENT_TOP_P") { $AgentTopP = $Val }
        }
    }
}

if ((Test-Path $ConfigPath) -and !$Configure) {
    Write-Host "Configuration file $ConfigPath already exists. Verifying setup..."
    # Ensure any missing defaults are set (handled by backend load, but keeping structure clean)
} else {
    Write-Host ""
    Write-Host "Select LLM backend:"
    Write-Host "  [1] OpenAI            - gpt-6.1-sol or any OpenAI-compatible endpoint"
    Write-Host "  [2] Ollama (default)  - local or remote Ollama instance"
    Write-Host "  [3] Local OpenAI API  - llama.cpp, vLLM, SGLang, Xinference, etc."
    Write-Host "  [4] Azure OpenAI      - Microsoft Azure OpenAI Service"
    Write-Host "  [5] Dummy             - offline mock (for testing)"
    
    $BackendDefault = "2"
    if ($AgentBackend -eq "openai") { $BackendDefault = "1" }
    elseif ($AgentBackend -eq "local_openai") { $BackendDefault = "3" }
    elseif ($AgentBackend -eq "azure_openai") { $BackendDefault = "4" }
    elseif ($AgentBackend -eq "dummy") { $BackendDefault = "5" }
    
    $BackendChoice = Read-Host "Backend [1-5, default: $BackendDefault]"
    if ($BackendChoice -eq "") { $BackendChoice = $BackendDefault }
    
    if ($BackendChoice -eq "1") {
        $AgentBackend = "openai"
        
        Write-Host ""
        Write-Host "Select OpenAI model:"
        Write-Host "  [1] gpt-6.1-sol (default)"
        Write-Host "  [2] gpt-5.5"
        Write-Host "  [3] gpt-5.4-mini"
        Write-Host "  [4] gpt-5.4-nano"
        Write-Host "  [5] gpt-5.3-codex"
        Write-Host "  [6] o3"
        Write-Host "  [7] Enter a custom model name manually"
        
        $ModelDefault = "1"
        $OpenaiModelChoice = Read-Host "Select a model [1-7, default: $ModelDefault]"
        if ($OpenaiModelChoice -eq "") { $OpenaiModelChoice = $ModelDefault }
        
        if ($OpenaiModelChoice -eq "1") { $AgentModel = "gpt-6.1-sol" }
        elseif ($OpenaiModelChoice -eq "2") { $AgentModel = "gpt-5.5" }
        elseif ($OpenaiModelChoice -eq "3") { $AgentModel = "gpt-5.4-mini" }
        elseif ($OpenaiModelChoice -eq "4") { $AgentModel = "gpt-5.4-nano" }
        elseif ($OpenaiModelChoice -eq "5") { $AgentModel = "gpt-5.3-codex" }
        elseif ($OpenaiModelChoice -eq "6") { $AgentModel = "o3" }
        else {
            $AgentModel = Read-Host "Enter model name"
        }
        
        $EndpointDefault = if ($AgentEndpoint) { $AgentEndpoint } else { "https://api.openai.com/v1" }
        $AgentEndpoint = Read-Host "API endpoint base URL [default: $EndpointDefault]"
        if ($AgentEndpoint -eq "") { $AgentEndpoint = $EndpointDefault }
        
        $OpenaiApiKey = Read-Host "OpenAI API key (leave blank to keep current)"
        if ($OpenaiApiKey -eq "") { $OpenaiApiKey = (Get-Content $ConfigPath -ErrorAction SilentlyContinue | Select-String "OPENAI_API_KEY" | ForEach-Object { $_.Line.Split("=")[1].Trim('"').Trim("'") }) }
        
    } elseif ($BackendChoice -eq "2") {
        $AgentBackend = "ollama"
        $OllamaDefault = if ($AgentEndpoint) { $AgentEndpoint } else { "http://127.0.0.1:11434" }
        $AgentEndpoint = Read-Host "Enter Ollama endpoint URL [default: $OllamaDefault]"
        if ($AgentEndpoint -eq "") { $AgentEndpoint = $OllamaDefault }
        
        $AgentModel = Read-Host "Enter Ollama model name [default: gemma4:latest]"
        if ($AgentModel -eq "") { $AgentModel = "gemma4:latest" }
        
    } elseif ($BackendChoice -eq "3") {
        $AgentBackend = "local_openai"
        $LocalDefault = if ($AgentEndpoint) { $AgentEndpoint } else { "http://127.0.0.1:8080/v1" }
        $AgentEndpoint = Read-Host "API endpoint base URL [default: $LocalDefault]"
        if ($AgentEndpoint -eq "") { $AgentEndpoint = $LocalDefault }
        
        $LocalModelDefault = if ($AgentModel) { $AgentModel } else { "local-model" }
        $AgentModel = Read-Host "Enter model name [default: $LocalModelDefault]"
        if ($AgentModel -eq "") { $AgentModel = $LocalModelDefault }
        
        $OpenaiApiKey = Read-Host "API key (optional, leave blank if not required)"
        
    } elseif ($BackendChoice -eq "4") {
        $AgentBackend = "azure_openai"
        $AgentEndpoint = Read-Host "Azure OpenAI endpoint URL"
        $AgentModel = Read-Host "Deployment/model name [default: gpt-6.1-sol]"
        if ($AgentModel -eq "") { $AgentModel = "gpt-6.1-sol" }
        $AzureOpenaiApiKey = Read-Host "Azure OpenAI API key"
        $AzureOpenaiApiVersion = Read-Host "API version [default: 2025-04-01-preview]"
        if ($AzureOpenaiApiVersion -eq "") { $AzureOpenaiApiVersion = "2025-04-01-preview" }
        
    } elseif ($BackendChoice -eq "5") {
        $AgentBackend = "dummy"
    }
    
    Write-Host ""
    Write-Host "Select Agent thinking / reasoning level:"
    Write-Host "  [1] Off (default)"
    Write-Host "  [2] Low"
    Write-Host "  [3] Medium"
    Write-Host "  [4] High"
    
    $ThinkingDefault = "1"
    if ($AgentThinkingLevel -eq "low") { $ThinkingDefault = "2" }
    elseif ($AgentThinkingLevel -eq "medium") { $ThinkingDefault = "3" }
    elseif ($AgentThinkingLevel -eq "high") { $ThinkingDefault = "4" }
    
    $ThinkingChoice = Read-Host "Thinking level [1-4, default: $ThinkingDefault]"
    if ($ThinkingChoice -eq "") { $ThinkingChoice = $ThinkingDefault }
    
    if ($ThinkingChoice -eq "2") { $AgentThinkingLevel = "low" }
    elseif ($ThinkingChoice -eq "3") { $AgentThinkingLevel = "medium" }
    elseif ($ThinkingChoice -eq "4") { $AgentThinkingLevel = "high" }
    else { $AgentThinkingLevel = "off" }
    
    # Save configuration
    $ConfigDir = Split-Path $ConfigPath
    if (!(Test-Path $ConfigDir)) {
        New-Item -ItemType Directory -Path $ConfigDir -Force
    }
    
    $ConfigContent = @(
        "AGENT_BACKEND=`"$AgentBackend`"",
        "AGENT_ENDPOINT=`"$AgentEndpoint`"",
        "AGENT_MODEL=`"$AgentModel`"",
        "OPENAI_API_KEY=`"$OpenaiApiKey`"",
        "AZURE_OPENAI_API_KEY=`"$AzureOpenaiApiKey`"",
        "AZURE_OPENAI_API_VERSION=`"$AzureOpenaiApiVersion`"",
        "AGENT_THINKING_LEVEL=`"$AgentThinkingLevel`"",
        "AGENT_TEMPERATURE=`"$AgentTemperature`"",
        "AGENT_TOP_P=`"$AgentTopP`""
    )
    
    $ConfigContent | Out-File -FilePath $ConfigPath -Encoding utf8
    Write-Host "Configuration saved successfully to $ConfigPath"
}

# 5. Shell Profile & Execution Policy Configuration
if (!$Configure) {
    Write-Host "Configuring shell integration..."
    
    # Unblock the sourced script to remove NTFS Zone.Identifier stream ("Downloaded from Internet")
    $AgentScriptPath = Join-Path $InstallDir "bin\slash-agent.ps1"
    if (Test-Path $AgentScriptPath) {
        Unblock-File -Path $AgentScriptPath -ErrorAction SilentlyContinue
    }
    
    # Check and suggest updating ExecutionPolicy for CurrentUser if restricted
    $CurrentEP = Get-ExecutionPolicy -Scope CurrentUser
    if ($CurrentEP -in @("Restricted", "Undefined")) {
        $SysEP = Get-ExecutionPolicy
        if ($SysEP -in @("Restricted", "AllSigned")) {
            if ($IsInteractive) {
                Write-Host "Notice: PowerShell script execution is currently restricted on this system." -ForegroundColor Yellow
                $epChoice = Read-Host "Set ExecutionPolicy to RemoteSigned for CurrentUser? [Y/n]"
                if ($epChoice -ne "n") {
                    try {
                        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
                        Write-Host "ExecutionPolicy successfully updated to RemoteSigned for CurrentUser." -ForegroundColor Green
                    } catch {
                        Write-Host "Warning: Could not update ExecutionPolicy automatically. If sourcing fails, run: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
                    }
                }
            }
        }
    }
    
    $ProfileDir = Split-Path $PROFILE
    if (!(Test-Path $ProfileDir)) {
        New-Item -ItemType Directory -Path $ProfileDir -Force
    }
    if (!(Test-Path $PROFILE)) {
        New-Item -ItemType File -Path $PROFILE -Force
    }
    
    $SourceLine = ". `"$InstallDir\bin\slash-agent.ps1`""
    
    # Read profile content
    $ProfileLines = Get-Content $PROFILE -ErrorAction SilentlyContinue
    $AlreadyConfigured = $false
    if ($ProfileLines) {
        foreach ($Line in $ProfileLines) {
            if ($Line.Trim() -eq $SourceLine) {
                $AlreadyConfigured = $true
                break
            }
        }
    }
    
    if ($AlreadyConfigured) {
        Write-Host "Shell integration already configured in `$PROFILE ($PROFILE)."
    } else {
        Write-Host "Adding sourcing command to $PROFILE..."
        Add-Content -Path $PROFILE -Value "`n# slash-agent Integration`n$SourceLine"
        Write-Host "Shell integration successfully added to `$PROFILE."
    }
}

Write-Host "==============================================" -ForegroundColor Green
if ($Configure) {
    Write-Host "Configuration complete!" -ForegroundColor Green
} elseif ($UpdateMode) {
    Write-Host "Update complete!" -ForegroundColor Green
} else {
    Write-Host "Installation complete!" -ForegroundColor Green
}

if (!$Configure) {
    Write-Host "To start using slash-agent in your CURRENT PowerShell session, run:" -ForegroundColor Green
    Write-Host "  . `"$InstallDir\bin\slash-agent.ps1`"" -ForegroundColor Yellow
    Write-Host "Then use /agent or 'agent' followed by your task." -ForegroundColor Green
    Write-Host "If script execution is blocked when opening a new terminal window, run:" -ForegroundColor Yellow
    Write-Host "  Set-ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
}
Write-Host "==============================================" -ForegroundColor Green
