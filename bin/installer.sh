#!/bin/bash

# slash-agent Installer
# Can be run via: curl -fsSL <url>/bin/installer.sh | sh

set -e

# Default settings (can be overridden by environment variables)
REPO_URL="${REPO_URL:-https://github.com/akatzmann/slash-agent.git}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.slash-agent}"

echo "=============================================="
echo "      Installing slash-agent           "
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
    echo "Updating existing repository..."
    cd "$INSTALL_DIR"
    git pull || { echo "Error: Failed to pull latest changes from repository."; exit 1; }
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
.venv/bin/pip install -r requirements.txt || { echo "Error: Failed to install Python dependencies."; exit 1; }

# 4. Interactive LLM Backend Configuration
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

fetch_models() {
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

# Use OLLAMA_HOST env var if pre-set, otherwise probe defaults
if [ -n "$OLLAMA_HOST" ]; then
    echo "Using pre-configured OLLAMA_HOST=$OLLAMA_HOST."
else
    echo "Probing local Ollama service at http://127.0.0.1:11434..."
    if curl -s -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
        OLLAMA_HOST="http://127.0.0.1:11434"
        echo "Ollama detected at http://127.0.0.1:11434."
    else
        echo "Ollama was not found at http://127.0.0.1:11434."
        CUSTOM_HOST=$(prompt_user "Enter your Ollama endpoint URL (or press Enter to skip): " "")
        if [ -n "$CUSTOM_HOST" ]; then
            echo "Probing $CUSTOM_HOST..."
            if curl -s -m 3 "$CUSTOM_HOST/api/tags" >/dev/null 2>&1; then
                OLLAMA_HOST="$CUSTOM_HOST"
                echo "Ollama detected at $CUSTOM_HOST."
            else
                echo "Warning: Could not reach Ollama at $CUSTOM_HOST. Proceeding with manual configuration."
                OLLAMA_HOST="$CUSTOM_HOST"
            fi
        fi
    fi
fi

MODELS=()
if [ -n "$OLLAMA_HOST" ]; then
    MODEL_LIST=$(fetch_models "$OLLAMA_HOST")
    if [ -n "$MODEL_LIST" ]; then
        while IFS= read -r line; do
            [ -n "$line" ] && MODELS+=("$line")
        done <<< "$MODEL_LIST"
    fi
fi

SELECTED_MODEL=""
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
                SELECTED_MODEL=$(prompt_user "Enter model name: " "")
                if [ -z "$SELECTED_MODEL" ]; then
                    echo "Model name cannot be empty."
                    continue
                fi
                break
            else
                SELECTED_MODEL="${MODELS[$((choice-1))]}"
                break
            fi
        else
            echo "Invalid selection. Please try again."
        fi
    done
else
    echo "No models found or Ollama skipped. Using manual configuration."
    if [ -z "$OLLAMA_HOST" ]; then
        OLLAMA_HOST=$(prompt_user "Enter Ollama endpoint URL [default: http://127.0.0.1:11434]: " "http://127.0.0.1:11434")
    fi
    SELECTED_MODEL=$(prompt_user "Enter model name to use [default: gemma4:e4b-it-qat]: " "gemma4:e4b-it-qat")
fi

echo "Saving configuration to $INSTALL_DIR/.env..."
cat <<EOF > "$INSTALL_DIR/.env"
AGENT_ENDPOINT="$OLLAMA_HOST"
AGENT_MODEL="$SELECTED_MODEL"
EOF
echo "Configuration saved successfully."

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
echo "Installation complete!"
echo "To start using the agent in your current shell session, run:"
echo "  source $INSTALL_DIR/bin/slash-agent.sh"
echo "Then use /agent followed by your command."
echo "=============================================="
