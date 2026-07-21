#!/bin/bash

# slash-agent Installer
# Can be run via: curl -fsSL <url>/bin/installer.sh | sh

set -e

# Default settings (can be overridden by environment variables)
REPO_URL="${REPO_URL:-https://github.com/akatzmann/slash-agent.git}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.slash-agent}"
BRANCH="${BRANCH:-}"

# Parse options
FORCE_CONFIGURE=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --configure|-c)
            FORCE_CONFIGURE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

UPDATE_MODE=false
if [ -d "$INSTALL_DIR" ]; then
    UPDATE_MODE=true
fi

echo "=============================================="
if [ "$FORCE_CONFIGURE" = true ]; then
    echo "      Configuring slash-agent          "
elif [ "$UPDATE_MODE" = true ]; then
    echo "      Updating slash-agent           "
else
    echo "      Installing slash-agent           "
fi
echo "=============================================="

# 1. Prerequisite Verification
if [ "$FORCE_CONFIGURE" = false ]; then
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
fi

# 2. Repository Cloning and Setup
if [ "$FORCE_CONFIGURE" = true ]; then
    if [ -d "$INSTALL_DIR" ]; then
        cd "$INSTALL_DIR"
    else
        echo "Error: slash-agent is not installed at $INSTALL_DIR. Please run installer without --configure first."
        exit 1
    fi
else
    if [ -d "$INSTALL_DIR" ]; then
        echo "Target directory $INSTALL_DIR already exists."
        if [ -d "$INSTALL_DIR/.git" ]; then
            echo "Updating existing repository..."
            cd "$INSTALL_DIR"
            if [ -n "$BRANCH" ]; then
                echo "Switching to branch $BRANCH..."
                git checkout "$BRANCH" || { echo "Warning: Failed to checkout branch $BRANCH."; }
            fi
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
        if [ -n "$BRANCH" ]; then
            echo "Cloning branch $BRANCH..."
            git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR" || { echo "Error: Failed to clone repository branch $BRANCH."; exit 1; }
        else
            git clone "$REPO_URL" "$INSTALL_DIR" || { echo "Error: Failed to clone repository."; exit 1; }
        fi
        cd "$INSTALL_DIR"
    fi
fi

# 3. Virtual Environment & Dependency Setup
suggest_venv_installation_command() {
    if command -v apt-get >/dev/null 2>&1; then
        echo "Please install python3-venv or virtualenv (e.g. 'sudo apt install python3-venv' or 'pip install virtualenv') and run the installer again."
    elif command -v dnf >/dev/null 2>&1; then
        echo "Please install python3-virtualenv or virtualenv (e.g. 'sudo dnf install python3-virtualenv' or 'pip install virtualenv') and run the installer again."
    elif command -v pacman >/dev/null 2>&1; then
        echo "Please install python-virtualenv or virtualenv (e.g. 'sudo pacman -S python-virtualenv' or 'pip install virtualenv') and run the installer again."
    elif command -v apk >/dev/null 2>&1; then
        echo "Please install py3-virtualenv or virtualenv (e.g. 'sudo apk add py3-virtualenv' or 'pip install virtualenv') and run the installer again."
    elif [ "$(uname -s)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
        echo "Please install python or virtualenv (e.g. 'brew install python' or 'pip install virtualenv') and run the installer again."
    else
        echo "Please install python3-venv or virtualenv (e.g. 'pip install virtualenv') and run the installer again."
    fi
}

if [ "$FORCE_CONFIGURE" = false ]; then
    if [ ! -d ".venv" ]; then
        echo "Creating Python virtual environment in .venv..."
        if python3 -m venv .venv >/dev/null 2>&1; then
            echo "Virtual environment created using 'venv' module."
        elif command -v virtualenv >/dev/null 2>&1 && virtualenv .venv >/dev/null 2>&1; then
            echo "Virtual environment created using 'virtualenv'."
        else
            echo "Error: Failed to create virtual environment."
            suggest_venv_installation_command
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
fi

# 4. Interactive LLM Backend Configuration
get_config_path() {
    if [ -n "$SLASH_AGENT_CONFIG_FILE" ]; then
        # Resolve to absolute path if possible
        readlink -f "$SLASH_AGENT_CONFIG_FILE" 2>/dev/null || echo "$SLASH_AGENT_CONFIG_FILE"
        return
    fi
    local xdg_config="${XDG_CONFIG_HOME:-$HOME/.config}"
    if [ -n "$HOME" ]; then
        echo "$xdg_config/slash-agent/env"
    else
        # Fallback to repo root .env
        echo "$INSTALL_DIR/.env"
    fi
}

migrate_legacy_config() {
    local legacy_path="$INSTALL_DIR/.env"
    local target_path="$CONFIG_PATH"

    if [ -f "$legacy_path" ] && [ "$legacy_path" != "$target_path" ]; then
        echo "Migrating legacy configuration from $legacy_path to $target_path..."
        
        local target_dir
        target_dir=$(dirname "$target_path")
        mkdir -p "$target_dir"
        
        if [ ! -f "$target_path" ]; then
            touch "$target_path"
            chmod 600 "$target_path"
        fi

        if [ ! -s "$target_path" ]; then
            cp "$legacy_path" "$target_path"
            chmod 600 "$target_path"
        else
            # Merge logic
            while IFS= read -r line || [ -n "$line" ]; do
                # Trim spaces
                line=$(echo "$line" | xargs)
                if [[ -z "$line" || "$line" == "#"* ]]; then
                    continue
                fi
                if [[ "$line" == *"="* ]]; then
                    local key
                    key=$(echo "$line" | cut -d'=' -f1 | xargs)
                    if ! grep -q "^$key=" "$target_path"; then
                        echo "$line" >> "$target_path"
                    fi
                fi
            done < "$legacy_path"
        fi

        rm -f "$legacy_path"
        echo "Migration complete. Legacy configuration deleted."
    fi
}

CONFIG_PATH=$(get_config_path)
migrate_legacy_config

if [ -f "$CONFIG_PATH" ] && [ "$FORCE_CONFIGURE" = "false" ]; then
    echo "Configuration file $CONFIG_PATH already exists. Ensuring all backend variables are configured..."
    
    # Helper to check/append keys
    amend_env_val() {
        local key="$1"
        local val="$2"
        if ! grep -q "^$key=" "$CONFIG_PATH"; then
            mkdir -p "$(dirname "$CONFIG_PATH")"
            [ ! -f "$CONFIG_PATH" ] && touch "$CONFIG_PATH" && chmod 600 "$CONFIG_PATH"
            echo "$key=\"$val\"" >> "$CONFIG_PATH"
            echo "  Added missing configuration: $key=\"$val\""
        fi
    }
    
    # Infer backend if AGENT_BACKEND is missing
    if ! grep -q "^AGENT_BACKEND=" "$CONFIG_PATH"; then
        existing_endpoint=""
        existing_endpoint=$(grep "^AGENT_ENDPOINT=" "$CONFIG_PATH" | cut -d'=' -f2- | tr -d '"'\' || true)
        if [[ "$existing_endpoint" == *":11434"* ]]; then
            echo "Inferred legacy Ollama backend from existing endpoint."
            amend_env_val "AGENT_BACKEND" "ollama"
        else
            echo "Defaulting to OpenAI backend."
            amend_env_val "AGENT_BACKEND" "openai"
        fi
    fi
    
    # Ensure placeholder keys for API key variables are appended if missing
    for key in OPENAI_API_KEY AZURE_OPENAI_API_KEY AZURE_OPENAI_API_VERSION AGENT_THINKING_LEVEL AGENT_TEMPERATURE AGENT_TOP_P; do
        if ! grep -q "$key" "$CONFIG_PATH"; then
            if [ "$key" = "AZURE_OPENAI_API_VERSION" ]; then
                amend_env_val "AZURE_OPENAI_API_VERSION" "2025-04-01-preview"
            elif [ "$key" = "AGENT_THINKING_LEVEL" ]; then
                amend_env_val "AGENT_THINKING_LEVEL" "off"
            else
                amend_env_val "$key" ""
            fi
        fi
    done
    echo "Configuration verification complete."
else
    # Load current variables to pre-populate defaults for prompts
    if [ -f "$CONFIG_PATH" ]; then
        source "$CONFIG_PATH"
    fi

    prompt_user() {
        local prompt_msg="$1"
        local default_val="$2"
        local user_input

        if [ -c /dev/tty ] && [ -z "$TEST_MODE" ]; then
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
    if any(h in '${host}' for h in ('127.0.0.1', 'localhost')):
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        r = opener.open('${host}/api/tags', timeout=3)
    else:
        r = urllib.request.urlopen('${host}/api/tags', timeout=3)
    with r:
        models = [m['name'] for m in json.loads(r.read().decode('utf-8')).get('models', [])]
        print('\n'.join(models))
except Exception:
    pass
" 2>/dev/null
    }

    echo ""
    echo "Select LLM backend:"
    echo "  [1] OpenAI            - gpt-5.4-nano or any OpenAI-compatible endpoint"
    echo "  [2] Ollama (default)  - local or remote Ollama instance"
    echo "  [3] Local OpenAI API  - llama.cpp, vLLM, SGLang, Xinference, etc."
    echo "  [4] Azure OpenAI      - Microsoft Azure OpenAI Service"
    echo "  [5] Dummy             - offline mock (for testing)"
    
    BACKEND_DEFAULT="2"
    if [ "$AGENT_BACKEND" = "openai" ]; then
        if [[ "$AGENT_ENDPOINT" == *"127.0.0.1"* || "$AGENT_ENDPOINT" == *"localhost"* ]]; then
            BACKEND_DEFAULT="3"
        else
            BACKEND_DEFAULT="1"
        fi
    elif [ "$AGENT_BACKEND" = "azure_openai" ]; then
        BACKEND_DEFAULT="4"
    elif [ "$AGENT_BACKEND" = "dummy" ]; then
        BACKEND_DEFAULT="5"
    elif [ "$AGENT_BACKEND" = "ollama" ]; then
        BACKEND_DEFAULT="2"
    fi
    BACKEND_CHOICE=$(prompt_user "Backend [1-5, default: $BACKEND_DEFAULT]: " "$BACKEND_DEFAULT")

    CHOSEN_BACKEND=""
    if [ "$BACKEND_CHOICE" = "1" ]; then
        CHOSEN_BACKEND="openai"
    elif [ "$BACKEND_CHOICE" = "2" ]; then
        CHOSEN_BACKEND="ollama"
    elif [ "$BACKEND_CHOICE" = "3" ]; then
        CHOSEN_BACKEND="openai"
    elif [ "$BACKEND_CHOICE" = "4" ]; then
        CHOSEN_BACKEND="azure_openai"
    elif [ "$BACKEND_CHOICE" = "5" ]; then
        CHOSEN_BACKEND="dummy"
    fi

    if [ "$CHOSEN_BACKEND" != "$AGENT_BACKEND" ]; then
        AGENT_ENDPOINT=""
        AGENT_MODEL=""
    fi
    AGENT_BACKEND="$CHOSEN_BACKEND"

    OPENAI_API_KEY_VAL=""
    AZURE_OPENAI_API_KEY_VAL=""
    AZURE_OPENAI_API_VERSION_VAL=""

    if [ "$BACKEND_CHOICE" = "1" ]; then
        AGENT_BACKEND="openai"
        
        echo ""
        echo "Select OpenAI model:"
        echo "  [1] gpt-5.5"
        echo "  [2] gpt-5.4-mini"
        echo "  [3] gpt-5.4-nano (default)"
        echo "  [4] gpt-5.3-codex"
        echo "  [5] o3"
        echo "  [6] Enter a custom model name manually"
        
        OPENAI_MODEL_DEFAULT="3"
        if [ "$AGENT_MODEL" = "gpt-5.5" ]; then
            OPENAI_MODEL_DEFAULT="1"
        elif [ "$AGENT_MODEL" = "gpt-5.4-mini" ]; then
            OPENAI_MODEL_DEFAULT="2"
        elif [ "$AGENT_MODEL" = "gpt-5.4-nano" ]; then
            OPENAI_MODEL_DEFAULT="3"
        elif [ "$AGENT_MODEL" = "gpt-5.3-codex" ]; then
            OPENAI_MODEL_DEFAULT="4"
        elif [ "$AGENT_MODEL" = "o3" ]; then
            OPENAI_MODEL_DEFAULT="5"
        elif [ -n "$AGENT_MODEL" ]; then
            OPENAI_MODEL_DEFAULT="6"
        fi
        
        while true; do
            OPENAI_MODEL_CHOICE=$(prompt_user "Select a model [1-6, default: $OPENAI_MODEL_DEFAULT]: " "$OPENAI_MODEL_DEFAULT")
            if [ "$OPENAI_MODEL_CHOICE" = "1" ]; then
                AGENT_MODEL="gpt-5.5"
                break
            elif [ "$OPENAI_MODEL_CHOICE" = "2" ]; then
                AGENT_MODEL="gpt-5.4-mini"
                break
            elif [ "$OPENAI_MODEL_CHOICE" = "3" ]; then
                AGENT_MODEL="gpt-5.4-nano"
                break
            elif [ "$OPENAI_MODEL_CHOICE" = "4" ]; then
                AGENT_MODEL="gpt-5.3-codex"
                break
            elif [ "$OPENAI_MODEL_CHOICE" = "5" ]; then
                AGENT_MODEL="o3"
                break
            elif [ "$OPENAI_MODEL_CHOICE" = "6" ]; then
                AGENT_MODEL=$(prompt_user "Enter model name [default: $AGENT_MODEL]: " "$AGENT_MODEL")
                if [ -n "$AGENT_MODEL" ]; then
                    break
                else
                    echo "Model name cannot be empty."
                fi
            else
                echo "Invalid selection. Please try again."
            fi
        done
        
        ENDPOINT_DEFAULT="${AGENT_ENDPOINT:-https://api.openai.com/v1}"
        AGENT_ENDPOINT=$(prompt_user "API endpoint base URL [press Enter to use default $ENDPOINT_DEFAULT]: " "$AGENT_ENDPOINT")
        OPENAI_API_KEY_VAL=$(prompt_user "OpenAI API key (leave blank to keep current): " "$OPENAI_API_KEY")

    elif [ "$BACKEND_CHOICE" = "2" ]; then
        AGENT_BACKEND="ollama"
        OLLAMA_ENDPOINT_DEFAULT="${AGENT_ENDPOINT:-http://127.0.0.1:11434}"
        echo "Probing local Ollama service at $OLLAMA_ENDPOINT_DEFAULT..."
        if curl -s -m 2 "$OLLAMA_ENDPOINT_DEFAULT/api/tags" >/dev/null 2>&1; then
            AGENT_ENDPOINT="$OLLAMA_ENDPOINT_DEFAULT"
            echo "Ollama detected at $AGENT_ENDPOINT."
        else
            echo "Ollama was not found at $OLLAMA_ENDPOINT_DEFAULT."
            AGENT_ENDPOINT=$(prompt_user "Enter Ollama endpoint URL [default: $OLLAMA_ENDPOINT_DEFAULT]: " "$OLLAMA_ENDPOINT_DEFAULT")
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
                if [ "${MODELS[$i]}" = "$AGENT_MODEL" ]; then
                    DEFAULT_INDEX=$((i+1))
                elif [ -z "$AGENT_MODEL" ] && [ "${MODELS[$i]}" = "gemma4:latest" ]; then
                    DEFAULT_INDEX=$((i+1))
                fi
            done
            CUSTOM_OPTION_INDEX=$((${#MODELS[@]} + 1))
            echo "  [$CUSTOM_OPTION_INDEX] Enter a custom model name manually"
            while true; do
                choice=$(prompt_user "Select a model [1-$CUSTOM_OPTION_INDEX, default: $DEFAULT_INDEX]: " "$DEFAULT_INDEX")
                if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$CUSTOM_OPTION_INDEX" ]; then
                    if [ "$choice" -eq "$CUSTOM_OPTION_INDEX" ]; then
                        AGENT_MODEL=$(prompt_user "Enter model name [default: $AGENT_MODEL]: " "$AGENT_MODEL")
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
            AGENT_MODEL=$(prompt_user "Enter Ollama model name [default: ${AGENT_MODEL:-gemma4:latest}]: " "${AGENT_MODEL:-gemma4:latest}")
        fi

    elif [ "$BACKEND_CHOICE" = "3" ]; then
        AGENT_BACKEND="openai"
        LOCAL_ENDPOINT_DEFAULT="${AGENT_ENDPOINT:-http://127.0.0.1:8080/v1}"
        echo ""
        echo "Configure Local API Endpoint (e.g. llama-server default: http://127.0.0.1:8080/v1)"
        echo "                            (e.g. vLLM default:         http://127.0.0.1:8000/v1)"
        echo "                            (e.g. SGLang default:       http://127.0.0.1:30000/v1)"
        echo "                            (e.g. Xinference default:   http://127.0.0.1:9997/v1)"
        AGENT_ENDPOINT=$(prompt_user "Local API base URL [default: $LOCAL_ENDPOINT_DEFAULT]: " "$LOCAL_ENDPOINT_DEFAULT")
        
        # Suffix sanitization: append /v1 if missing
        if [[ "$AGENT_ENDPOINT" != *"/v1"* && "$AGENT_ENDPOINT" != *"/v1/"* ]]; then
            AGENT_ENDPOINT="${AGENT_ENDPOINT%/}/v1"
            echo "  Sanitized endpoint URL to: $AGENT_ENDPOINT"
        fi
        
        MODELS=()
        fetch_local_models() {
            local host="$1"
            python3 -c "
import urllib.request, json
try:
    if any(h in '${host}' for h in ('127.0.0.1', 'localhost')):
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        r = opener.open('${host}/models', timeout=3)
    else:
        r = urllib.request.urlopen('${host}/models', timeout=3)
    with r:
        models = [m['id'] for m in json.loads(r.read().decode('utf-8')).get('data', [])]
        print('\n'.join(models))
except Exception:
    pass
" 2>/dev/null
        }
        
        echo "Probing local API service at $AGENT_ENDPOINT..."
        MODEL_LIST=$(fetch_local_models "$AGENT_ENDPOINT")
        if [ -n "$MODEL_LIST" ]; then
            while IFS= read -r line; do
                [ -n "$line" ] && MODELS+=("$line")
            done <<< "$MODEL_LIST"
        fi
        
        if [ ${#MODELS[@]} -gt 0 ]; then
            echo "Found the following models loaded in your local server:"
            DEFAULT_INDEX=1
            for i in "${!MODELS[@]}"; do
                echo "  [$((i+1))] ${MODELS[$i]}"
                if [ "${MODELS[$i]}" = "$AGENT_MODEL" ]; then
                    DEFAULT_INDEX=$((i+1))
                fi
            done
            CUSTOM_OPTION_INDEX=$((${#MODELS[@]} + 1))
            echo "  [$CUSTOM_OPTION_INDEX] Enter a custom model name manually"
            while true; do
                choice=$(prompt_user "Select a model [1-$CUSTOM_OPTION_INDEX, default: $DEFAULT_INDEX]: " "$DEFAULT_INDEX")
                if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$CUSTOM_OPTION_INDEX" ]; then
                    if [ "$choice" -eq "$CUSTOM_OPTION_INDEX" ]; then
                        AGENT_MODEL=$(prompt_user "Enter model name [default: $AGENT_MODEL]: " "$AGENT_MODEL")
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
            echo "Local API service did not respond or has no active models loaded."
            AGENT_MODEL=$(prompt_user "Enter model identifier [default: ${AGENT_MODEL:-gemma4-27b}]: " "${AGENT_MODEL:-gemma4-27b}")
        fi
        
        if [ -z "$OPENAI_API_KEY" ]; then
            OPENAI_API_KEY_VAL="local-api-key"
        else
            OPENAI_API_KEY_VAL="$OPENAI_API_KEY"
        fi

    elif [ "$BACKEND_CHOICE" = "4" ]; then
        AGENT_BACKEND="azure_openai"
        AGENT_ENDPOINT=$(prompt_user "Azure OpenAI endpoint URL [default: $AGENT_ENDPOINT]: " "$AGENT_ENDPOINT")
        AGENT_MODEL=$(prompt_user "Deployment/model name [default: ${AGENT_MODEL:-gpt-5.4-nano}]: " "${AGENT_MODEL:-gpt-5.4-nano}")
        AZURE_OPENAI_API_KEY_VAL=$(prompt_user "Azure OpenAI API key [default: $AZURE_OPENAI_API_KEY]: " "$AZURE_OPENAI_API_KEY")
        AZURE_OPENAI_API_VERSION_VAL=$(prompt_user "API version [default: ${AZURE_OPENAI_API_VERSION:-2025-04-01-preview}]: " "${AZURE_OPENAI_API_VERSION:-2025-04-01-preview}")

    elif [ "$BACKEND_CHOICE" = "5" ]; then
        AGENT_BACKEND="dummy"
        echo "Dummy backend selected. No configuration needed."

    else
        echo "Invalid choice. Defaulting to OpenAI backend."
        AGENT_BACKEND="openai"
        AGENT_MODEL="gpt-5.4-nano"
    fi

    echo ""
    echo "Select Agent thinking / reasoning level:"
    echo "  [1] Off (default) - recommended for standard models"
    echo "  [2] Low           - for GPT-5/o1/o3 reasoning models (reasoning_effort=low)"
    echo "  [3] Medium        - for GPT-5/o1/o3 reasoning models (reasoning_effort=medium)"
    echo "  [4] High          - for GPT-5/o1/o3 reasoning models (reasoning_effort=high)"
    
    THINKING_DEFAULT="1"
    if [ "$AGENT_THINKING_LEVEL" = "low" ]; then THINKING_DEFAULT="2"; fi
    if [ "$AGENT_THINKING_LEVEL" = "medium" ]; then THINKING_DEFAULT="3"; fi
    if [ "$AGENT_THINKING_LEVEL" = "high" ]; then THINKING_DEFAULT="4"; fi
    
    THINKING_CHOICE=$(prompt_user "Thinking level [1-4, default: $THINKING_DEFAULT]: " "$THINKING_DEFAULT")
    
    AGENT_THINKING_LEVEL_VAL="off"
    if [ "$THINKING_CHOICE" = "2" ]; then
        AGENT_THINKING_LEVEL_VAL="low"
    elif [ "$THINKING_CHOICE" = "3" ]; then
        AGENT_THINKING_LEVEL_VAL="medium"
    elif [ "$THINKING_CHOICE" = "4" ]; then
        AGENT_THINKING_LEVEL_VAL="high"
    fi

    echo "Saving configuration to $CONFIG_PATH..."
    mkdir -p "$(dirname "$CONFIG_PATH")"
    [ ! -f "$CONFIG_PATH" ] && touch "$CONFIG_PATH" && chmod 600 "$CONFIG_PATH"
    {
        echo "AGENT_BACKEND=\"$AGENT_BACKEND\""
        [ -n "$AGENT_ENDPOINT" ] && echo "AGENT_ENDPOINT=\"$AGENT_ENDPOINT\""
        [ -n "$AGENT_MODEL" ] && echo "AGENT_MODEL=\"$AGENT_MODEL\""
        [ -n "$OPENAI_API_KEY_VAL" ] && echo "OPENAI_API_KEY=\"$OPENAI_API_KEY_VAL\""
        [ -n "$AZURE_OPENAI_API_KEY_VAL" ] && echo "AZURE_OPENAI_API_KEY=\"$AZURE_OPENAI_API_KEY_VAL\""
        [ -n "$AZURE_OPENAI_API_VERSION_VAL" ] && echo "AZURE_OPENAI_API_VERSION=\"$AZURE_OPENAI_API_VERSION_VAL\""
        echo "AGENT_THINKING_LEVEL=\"$AGENT_THINKING_LEVEL_VAL\""
        echo "AGENT_TEMPERATURE=\"$AGENT_TEMPERATURE\""
        echo "AGENT_TOP_P=\"$AGENT_TOP_P\""
    } > "$CONFIG_PATH"
    chmod 600 "$CONFIG_PATH"
    echo "Configuration saved successfully."
fi
# 5. Idempotent Shell Profile Registration
if [ "$FORCE_CONFIGURE" = false ]; then
    echo "Configuring shell integration..."
    
    # Detect active shell from $SHELL variable, default to bash
    CURRENT_SHELL=$(basename "${SHELL:-bash}")
    SHELL_RC=""
    SOURCE_LINE="source $INSTALL_DIR/bin/slash-agent.sh"
    
    OS_TYPE=$(uname -s 2>/dev/null || echo "Unknown")
    
    if [ "$CURRENT_SHELL" = "zsh" ] || [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ "$CURRENT_SHELL" = "fish" ]; then
        SHELL_RC="$HOME/.config/fish/config.fish"
        SOURCE_LINE="source $INSTALL_DIR/bin/slash-agent.fish"
    elif [ "$CURRENT_SHELL" = "ksh" ]; then
        SHELL_RC="$HOME/.kshrc"
    else
        # Bash or other Bourne-like shell
        if [ "$OS_TYPE" = "Darwin" ]; then
            # On macOS, login shells read .bash_profile / .profile
            if [ -f "$HOME/.bash_profile" ]; then
                SHELL_RC="$HOME/.bash_profile"
            else
                SHELL_RC="$HOME/.profile"
            fi
        else
            SHELL_RC="$HOME/.bashrc"
        fi
    fi
    
    # Ensure parent directory for configuration file exists (e.g. for ~/.config/fish)
    mkdir -p "$(dirname "$SHELL_RC")"
    
    # Create the file if it does not exist
    if [ ! -f "$SHELL_RC" ]; then
        touch "$SHELL_RC"
    fi
    
    if grep -Fq "$SOURCE_LINE" "$SHELL_RC"; then
        echo "Shell integration already configured in $SHELL_RC."
    else
        echo "Adding sourcing command to $SHELL_RC..."
        echo "" >> "$SHELL_RC"
        echo "# slash-agent Integration" >> "$SHELL_RC"
        echo "$SOURCE_LINE" >> "$SHELL_RC"
        echo "Shell integration successfully added to $SHELL_RC."
    fi
fi

echo "=============================================="
if [ "$FORCE_CONFIGURE" = true ]; then
    echo "Configuration complete!"
elif [ "$UPDATE_MODE" = true ]; then
    echo "Update complete!"
else
    echo "Installation complete!"
fi
if [ "$FORCE_CONFIGURE" = false ]; then
    echo "To start using the agent in your current shell session, run:"
    echo "  $SOURCE_LINE"
    echo "Then use /agent (or 'agent' in Fish) followed by your command."
fi
echo "=============================================="
