#!/usr/bin/env bash
# =================================================
# BlastDBBuilder Installer
# =================================================

set -euo pipefail

# -----------------------------
# Variables
# -----------------------------
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/bin"  # target for the executable

mkdir -p "$BIN_DIR"

CLI_WRAPPER="$BIN_DIR/blastdbbuilder"

# -----------------------------
# 1. Install the Python package in user space
# -----------------------------
echo "📦 Installing blastdbbuilder Python package..."
python3 -m pip install --user -e "$REPO_ROOT"

# -----------------------------
# 2. Create CLI wrapper in ~/bin
# -----------------------------
if [ ! -f "$CLI_WRAPPER" ]; then
    echo "⚡ Creating CLI wrapper executable at $CLI_WRAPPER..."
    cat > "$CLI_WRAPPER" <<'EOF'
#!/usr/bin/env python3
from blastdbbuilder.cli import main
if __name__ == "__main__":
    main()
EOF
    chmod +x "$CLI_WRAPPER"
fi

# -----------------------------
# 3. Add ~/bin to PATH if missing
# -----------------------------
SHELL_RC=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "🔧 Adding $BIN_DIR to PATH in $SHELL_RC..."
    echo "" >> "$SHELL_RC"
    echo "# Added by BlastDBBuilder installer" >> "$SHELL_RC"
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
    echo "⚠️ Please run 'source $SHELL_RC' or open a new terminal to use blastdbbuilder"
fi

echo "✅ Installation complete!"
echo "You can now run 'blastdbbuilder --help' from any directory."
