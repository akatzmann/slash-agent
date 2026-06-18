#!/bin/bash

# slash-agent Installer
# Can be run via: curl -fsSL <url>/bin/installer.sh | sh

set -e

# Default settings (can be overridden by environment variables)
REPO_URL="${REPO_URL:-https://github.com/akatzmann/slash-agent.git}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.slash-agent}"

UPDATE_MODE=false
if [ -d "$INSTALL_DIR" ]; then
    UPDATE_MODE=true
fi

echo "=============================================="
if [ "$UPDATE_MODE" = true ]; then
    echo "      Updating slash-agent           "
else
    echo "      Installing slash-agent           "
fi
echo "=============================================="

# 1. Prerequisite Verification
echo "Verifying prerequisites..."

if ! command -v git >/dev/null 2>&1; then
    echo "Error: git is not installed. Please install git and try again."
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is not installed. Please install python3 and try again."
    exit 1
fi

echo "Prerequisites verified successfully."

# 2. Repository Cloning and Setup
if [ -d "$INSTALL_DIR" ]; then
    echo "Target directory $INSTALL_DIR already exists."
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "Updating existing repository..."
        cd "$INSTALL_DIR"
        git pull || {
            echo "Warning: git pull failed. If you have local modifications, please commit or stash them."
            echo "Continuing setup with existing files..."
        }
    else
        echo "Warning: Target directory exists but is not a git repository. Skipping repository update."
        cd "$INSTALL_DIR"
    fi
else
    echo "Cloning repository to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR" || { echo "Error: Failed to clone repository."; exit 1; }
    cd "$INSTALL_DIR"
fi

# 3. Virtual Environment & Dependency Setup
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment in .venv..."
    if python3 -m venv .venv >/dev/null 2>&1; then
        echo "Virtual environment created using 'venv' module."
    elif command -v virtualenv >/dev/null 2>&1 && virtualenv .venv >/dev/null 2>&1; then
        echo "Virtual environment created using 'virtualenv'."
    else
        echo "Error: Failed to create virtual environment."
        echo "Please install python3-venv or virtualenv (e.g. 'sudo apt install python3-venv' or 'pip install virtualenv') and run the installer again."
        exit 1
    fi
fi

echo "Installing Python dependencies..."
.venv/bin/pip install --upgrade pip
if [ "$UPDATE_MODE" = true ]; then
    echo "Bypassing pip git cache for py-agent-core..."
    .venv/bin/pip uninstall -y py-agent-core || true
fi
.venv/bin/pip install -r requirements.txt || { echo "Error: Failed to install Python dependencies."; exit 1; }

# 4. Interactive LLM Backend Configuration
if [ -f "$INSTALL_DIR/.env" ]; then
    echo "Configuration file $INSTALL_DIR/.env already exists. Ensuring all backend variables are configured..."
    
    # Helper to check/append keys
    amend_env_val() {
        local key="$1"
        local val="$2"
        if ! grep -q "^$key=" "$INSTALL_DIR/.env"; then
            echo "$key=\"$val\"" >> "$INSTALL_DIR/.env"
            echo "  Added missing configuration: $key=\"$val\""
        fi
    }
    
    # Infer backend if AGENT_BACKEND is missing
    if ! grep -q "^AGENT_BACKEND=" "$INSTALL_DIR/.env"; then
        existing_endpoint=""
        existing_endpoint=$(grep "^AGENT_ENDPOINT=" "$INSTALL_DIR/.env" | cut -d'=' -f2- | tr -d '"'\' || true)
        if [[ "$existing_endpoint" == *":11434"* ]]; then
            echo "Inferred legacy Ollama backend from existing endpoint."
            amend_env_val "AGENT_BACKEND" "ollama"
        else
            echo "Defaulting to OpenAI backend."
            amend_env_val "AGENT_BACKEND" "openai"
        fi
    fi
    
    # Ensure placeholder keys for API key variables are appended if missing
    for key in OPENAI_API_KEY AZURE_OPENAI_API_KEY AZURE_OPENAI_API_VERSION; do
        if ! grep -q "$key" "$INSTALL_DIR/.env"; then
            if [ "$key" = "AZURE_OPENAI_API_VERSION" ]; then
                echo "# AZURE_OPENAI_API_VERSION=\"2024-02-15-preview\"" >> "$INSTALL_DIR/.env"
            else
                echo "# $key=\"\"" >> "$INSTALL_DIR/.env"
            fi
        fi
    done
    echo "Configuration verification complete."
else
    prompt_user() {
        local prompt_msg="$1"
        local default_val="$2"
        local user_input

        if [ -c /dev/tty ]; then
            read -rp "$prompt_msg" user_input < /dev/tty
        else
            read -rp "$prompt_msg" user_input
        fi

        if [ -z "$user_input" ]; then
            echo "$default_val"
        else
            echo "$user_input"
        fi
    }

    fetch_ollama_models() {
        local host="$1"
        python3 -c "
import urllib.request, json, sys
try:
    with urllib.request.urlopen('${host}/api/tags', timeout=3) as r:
        models = [m['name'] for m in json.loads(r.read().decode('utf-8')).get('models', [])]
        print('\n'.join(models))
except Exception:
    pass
" 2>/dev/null
    }

    echo ""
    echo "Select LLM backend:"
    echo "  [1] OpenAI (default) — gpt-4o-mini or any OpenAI-compatible endpoint"
    echo "  [2] Ollama            — local or remote Ollama instance"
    echo "  [3] Azure OpenAI      — Microsoft Azure OpenAI Service"
    echo "  [4] Dummy             — offline mock (for testing)"
    BACKEND_CHOICE=$(prompt_user "Backend [1-4, default: 1]: " "1")

    AGENT_BACKEND=""
    AGENT_ENDPOINT=""
    AGENT_MODEL=""
    OPENAI_API_KEY_VAL=""
    AZURE_OPENAI_API_KEY_VAL=""
    AZURE_OPENAI_API_VERSION_VAL=""

    if [ "$BACKEND_CHOICE" = "1" ]; then
        AGENT_BACKEND="openai"
        
        echo ""
        echo "Select OpenAI model:"
        echo "  [1] gpt-4o-mini (default)"
        echo "  [2] gpt-4o"
        echo "  [3] o1-mini"
        echo "  [4] o1-preview"
        echo "  [5] Enter a custom model name manually"
        
        while true; do
            OPENAI_MODEL_CHOICE=$(prompt_user "Select a model [1-5, default: 1]: " "1")
            if [ "$OPENAI_MODEL_CHOICE" = "1" ]; then
                AGENT_MODEL="gpt-4o-mini"
                break
            elif [ "$OPENAI_MODEL_CHOICE" = "2" ]; then
                AGENT_MODEL="gpt-4o"
                break
            elif [ "$OPENAI_MODEL_CHOICE" = "3" ]; then
                AGENT_MODEL="o1-mini"
                break
            elif [ "$OPENAI_MODEL_CHOICE" = "4" ]; then
                AGENT_MODEL="o1-preview"
                break
            elif [ "$OPENAI_MODEL_CHOICE" = "5" ]; then
                AGENT_MODEL=$(prompt_user "Enter model name: " "")
                if [ -n "$AGENT_MODEL" ]; then
                    break
                else
                    echo "Model name cannot be empty."
                fi
            else
                echo "Invalid selection. Please try again."
            fi
        done
        
        AGENT_ENDPOINT=$(prompt_user "API endpoint base URL [press Enter to use default https://api.openai.com/v1]: " "")
        OPENAI_API_KEY_VAL=$(prompt_user "OpenAI API key (leave blank to use OPENAI_API_KEY env var): " "")

    elif [ "$BACKEND_CHOICE" = "2" ]; then
        AGENT_BACKEND="ollama"
        echo "Probing local Ollama service at http://127.0.0.1:11434..."
        if curl -s -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
            AGENT_ENDPOINT="http://127.0.0.1:11434"
            echo "Ollama detected at http://127.0.0.1:11434."
        else
            echo "Ollama was not found at http://127.0.0.1:11434."
            AGENT_ENDPOINT=$(prompt_user "Enter Ollama endpoint URL [default: http://127.0.0.1:11434]: " "http://127.0.0.1:11434")
        fi
        MODELS=()
        MODEL_LIST=$(fetch_ollama_models "$AGENT_ENDPOINT")
        if [ -n "$MODEL_LIST" ]; then
            while IFS= read -r line; do
                [ -n "$line" ] && MODELS+=("$line")
            done <<< "$MODEL_LIST"
        fi
        if [ ${#MODELS[@]} -gt 0 ]; then
            echo "Found the following models in your Ollama library:"
            DEFAULT_INDEX=1
            for i in "${!MODELS[@]}"; do
                echo "  [$((i+1))] ${MODELS[$i]}"
                if [ "${MODELS[$i]}" = "gemma4:e4b-it-qat" ]; then
                    DEFAULT_INDEX=$((i+1))
                fi
            done
            CUSTOM_OPTION_INDEX=$((${#MODELS[@]} + 1))
            echo "  [$CUSTOM_OPTION_INDEX] Enter a custom model name manually"
            while true; do
                choice=$(prompt_user "Select a model [1-$CUSTOM_OPTION_INDEX, default: $DEFAULT_INDEX]: " "$DEFAULT_INDEX")
                if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$CUSTOM_OPTION_INDEX" ]; then
                    if [ "$choice" -eq "$CUSTOM_OPTION_INDEX" ]; then
                        AGENT_MODEL=$(prompt_user "Enter model name: " "")
                        [ -z "$AGENT_MODEL" ] && echo "Model name cannot be empty." && continue
                    else
                        AGENT_MODEL="${MODELS[$((choice-1))]}"
                    fi
                    break
                else
                    echo "Invalid selection. Please try again."
                fi
            done
        else
            AGENT_MODEL=$(prompt_user "Enter Ollama model name [default: gemma4:e4b-it-qat]: " "gemma4:e4b-it-qat")
        fi

    elif [ "$BACKEND_CHOICE" = "3" ]; then
        AGENT_BACKEND="azure_openai"
        AGENT_ENDPOINT=$(prompt_user "Azure OpenAI endpoint URL: " "")
        AGENT_MODEL=$(prompt_user "Deployment/model name [default: gpt-4o]: " "gpt-4o")
        AZURE_OPENAI_API_KEY_VAL=$(prompt_user "Azure OpenAI API key: " "")
        AZURE_OPENAI_API_VERSION_VAL=$(prompt_user "API version [default: 2024-02-15-preview]: " "2024-02-15-preview")

    elif [ "$BACKEND_CHOICE" = "4" ]; then
        AGENT_BACKEND="dummy"
        echo "Dummy backend selected. No configuration needed."

    else
        echo "Invalid choice. Defaulting to OpenAI backend."
        AGENT_BACKEND="openai"
        AGENT_MODEL="gpt-4o-mini"
    fi

    echo "Saving configuration to $INSTALL_DIR/.env..."
    {
        echo "AGENT_BACKEND=\"$AGENT_BACKEND\""
        [ -n "$AGENT_ENDPOINT" ] && echo "AGENT_ENDPOINT=\"$AGENT_ENDPOINT\""
        [ -n "$AGENT_MODEL" ] && echo "AGENT_MODEL=\"$AGENT_MODEL\""
        [ -n "$OPENAI_API_KEY_VAL" ] && echo "OPENAI_API_KEY=\"$OPENAI_API_KEY_VAL\""
        [ -n "$AZURE_OPENAI_API_KEY_VAL" ] && echo "AZURE_OPENAI_API_KEY=\"$AZURE_OPENAI_API_KEY_VAL\""
        [ -n "$AZURE_OPENAI_API_VERSION_VAL" ] && echo "AZURE_OPENAI_API_VERSION=\"$AZURE_OPENAI_API_VERSION_VAL\""
    } > "$INSTALL_DIR/.env"
    echo "Configuration saved successfully."
fi
# 5. Idempotent Shell Profile Registration
SHELL_RC="$HOME/.bashrc"
SOURCE_LINE="source $INSTALL_DIR/bin/slash-agent.sh"

echo "Configuring shell integration..."
if [ -f "$SHELL_RC" ]; then
    if grep -Fq "$SOURCE_LINE" "$SHELL_RC"; then
        echo "Shell integration already configured in $SHELL_RC."
    else
        echo "Adding sourcing command to $SHELL_RC..."
        echo "" >> "$SHELL_RC"
        echo "# slash-agent Integration" >> "$SHELL_RC"
        echo "$SOURCE_LINE" >> "$SHELL_RC"
        echo "Shell integration successfully added to $SHELL_RC."
    fi
else
    echo "Warning: Shell configuration file $SHELL_RC not found."
    echo "Please add the following line manually to your shell configuration file:"
    echo "  $SOURCE_LINE"
fi

echo "=============================================="
if [ "$UPDATE_MODE" = true ]; then
    echo "Update complete!"
else
    echo "Installation complete!"
fi
echo "To start using the agent in your current shell session, run:"
echo "  source $INSTALL_DIR/bin/slash-agent.sh"
echo "Then use /agent followed by your command."
echo "=============================================="
