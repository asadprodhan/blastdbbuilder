#!/bin/bash
# ========================================================
# blastdbbuilder Installer
# Copies the CLI entrypoint to ~/bin for global access
# ========================================================

set -euo pipefail

# -----------------------------
# 1. Check for ~/bin in PATH
# -----------------------------
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo "⚠️ Warning: ~/bin is not in your PATH."
    echo "Add the following line to your ~/.bashrc or ~/.zshrc:"
    echo 'export PATH="$HOME/bin:$PATH"'
    echo ""
fi

# -----------------------------
# 2. Ensure ~/bin exists
# -----------------------------
mkdir -p "$HOME/bin"

# -----------------------------
# 3. Determine repo root
# -----------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

# -----------------------------
# 4. Copy CLI script to ~/bin
# -----------------------------
CLI_SCRIPT="$REPO_ROOT/blastdbbuilder"  # your CLI entrypoint
if [[ ! -f "$CLI_SCRIPT" ]]; then
    echo "❌ Error: CLI script '$CLI_SCRIPT' not found!"
    exit 1
fi

cp "$CLI_SCRIPT" "$HOME/bin/"
chmod +x "$HOME/bin/blastdbbuilder"

# -----------------------------
# 5. Optional: Install dependencies via pip
# -----------------------------
if [[ -f "$REPO_ROOT/setup.py" ]]; then
    echo "📦 Installing Python package dependencies..."
    python3 -m pip install --user .
fi

# -----------------------------
# 6. Completion message
# -----------------------------
echo ""
echo "✅ Installation complete!"
echo "You can now run 'blastdbbuilder' from any directory."
echo "If 'blastdbbuilder' is not found, add ~/bin to your PATH:"
echo '  export PATH="$HOME/bin:$PATH"'
echo "Then, try: blastdbbuilder --help"
