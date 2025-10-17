#!/usr/bin/env bash
# =================================================
# BlastDBBuilder Installer (Modern)
# =================================================

set -euo pipefail

echo "🧬 BlastDBBuilder Installer"

# -----------------------------
# Variables
# -----------------------------
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$HOME/bin"   # target for executable wrapper
mkdir -p "$BIN_DIR"

# Detect shell rc file
SHELL_RC=""
if [ -n "${BASH_VERSION-}" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -n "${ZSH_VERSION-}" ]; then
    SHELL_RC="$HOME/.zshrc"
else
    SHELL_RC="$HOME/.profile"
fi

# -----------------------------
# Check Python and pip
# -----------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "❌ pip not found. Please install pip for Python3."
    exit 1
fi

echo "✅ Python3 and pip detected."

# -----------------------------
# Upgrade pip, setuptools, wheel
# -----------------------------
echo "📦 Upgrading pip, setuptools, wheel..."
python3 -m pip install --upgrade --user pip setuptools wheel

# -----------------------------
# Install package in editable mode
# -----------------------------
echo "📦 Installing blastdbbuilder package (editable install)..."
python3 -m pip install --user --editable "$REPO_ROOT"

# -----------------------------
# Create CLI wrapper in ~/bin
# -----------------------------
WRAPPER="$BIN_DIR/blastdbbuilder"
echo "🔹 Creating CLI wrapper at $WRAPPER ..."
cat > "$WRAPPER" <<'EOF'
#!/usr/bin/env python3
from blastdbbuilder.cli import main
if __name__ == "__main__":
    main()
EOF

chmod +x "$WRAPPER"
echo "✅ Wrapper created."

# -----------------------------
# Add ~/bin to PATH if not already
# -----------------------------
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "🔹 Adding $BIN_DIR to PATH in $SHELL_RC ..."
    echo "" >> "$SHELL_RC"
    echo "# Added by BlastDBBuilder installer" >> "$SHELL_RC"
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
    echo "✅ PATH updated. Run 'source $SHELL_RC' or restart your terminal."
fi

echo "✅ Installation complete!"
echo "You can now run 'blastdbbuilder --help' from any directory."
