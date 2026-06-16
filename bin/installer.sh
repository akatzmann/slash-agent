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

# 4. Idempotent Shell Profile Registration
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
