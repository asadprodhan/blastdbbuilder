#!/bin/bash
# =========================================
# blastdbbuilder Installer
# Copies CLI to ~/bin and updates PATH
# =========================================

set -euo pipefail

# -----------------------------
# Variables
# -----------------------------
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/bin"
CLI_SCRIPT="blastdbbuilder"
TARGET="$BIN_DIR/$CLI_SCRIPT"

# -----------------------------
# Step 1: Ensure ~/bin exists
# -----------------------------
mkdir -p "$BIN_DIR"

# -----------------------------
# Step 2: Copy CLI to ~/bin
# -----------------------------
if [[ -f "$TARGET" ]]; then
    echo "[⚠] Existing installation detected at $TARGET"
    read -p "Do you want to overwrite it? [y/N]: " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        cp "$PROJECT_DIR/$CLI_SCRIPT" "$TARGET"
        chmod +x "$TARGET"
        echo "[✔] Updated $CLI_SCRIPT in $BIN_DIR"
    else
        echo "[ℹ] Installation aborted. Existing file preserved."
        exit 0
    fi
else
    cp "$PROJECT_DIR/$CLI_SCRIPT" "$TARGET"
    chmod +x "$TARGET"
    echo "[✔] Installed $CLI_SCRIPT to $BIN_DIR"
fi

# -----------------------------
# Step 3: Ensure ~/bin is in PATH
# -----------------------------
SHELL_RC=""
if [[ -n "$BASH_VERSION" ]]; then
    SHELL_RC="$HOME/.bashrc"
elif [[ -n "$ZSH_VERSION" ]]; then
    SHELL_RC="$HOME/.zshrc"
else
    echo "[⚠] Unknown shell. Make sure $BIN_DIR is in your PATH manually."
fi

if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    if [[ -n "$SHELL_RC" ]]; then
        echo "export PATH=\"\$HOME/bin:\$PATH\"" >> "$SHELL_RC"
        echo "[✔] Added $BIN_DIR to PATH in $SHELL_RC"
        echo "[ℹ] Please restart your terminal or run 'source $SHELL_RC' to update PATH."
    else
        echo "[⚠] Please add $BIN_DIR to your PATH manually."
    fi
else
    echo "[ℹ] $BIN_DIR already in PATH"
fi

# -----------------------------
# Step 4: Finish
# -----------------------------
echo "✅ Installation complete. You can now run 'blastdbbuilder --help' from any directory."
