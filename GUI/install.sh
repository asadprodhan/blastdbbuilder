#!/usr/bin/env bash
set -euo pipefail

APP_NAME="blastdbbuilder-gui"

INSTALL_DIR="$HOME/.local/share/${APP_NAME}"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_APP="${SRC_DIR}/app"

echo "== Installing ${APP_NAME} =="
echo

command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found"; exit 1; }

# tkinter check
python3 - <<'PY'
import tkinter
PY

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICON_DIR"

echo "Copying application..."
rm -rf "${INSTALL_DIR}/app"
mkdir -p "${INSTALL_DIR}/app"
cp -R "${SRC_APP}/." "${INSTALL_DIR}/app/"

# -----------------------------
# Create private venv (robust: no ensurepip required)
# -----------------------------
VENV_DIR="${INSTALL_DIR}/venv"

echo "Creating Python virtual environment..."
rm -rf "$VENV_DIR"
python3 -m venv --without-pip "$VENV_DIR"

# -----------------------------
# Bootstrap pip (works even when ensurepip is disabled)
# -----------------------------
echo "Bootstrapping pip..."
TMP_GETPIP="$(mktemp -t get-pip.XXXXXX.py)"

cleanup() {
  rm -f "$TMP_GETPIP" || true
}
trap cleanup EXIT

if command -v curl >/dev/null 2>&1; then
  curl -sS https://bootstrap.pypa.io/get-pip.py -o "$TMP_GETPIP"
elif command -v wget >/dev/null 2>&1; then
  wget -q https://bootstrap.pypa.io/get-pip.py -O "$TMP_GETPIP"
else
  echo "ERROR: neither curl nor wget found. Install one of them, or bundle get-pip.py in the package."
  exit 1
fi

"$VENV_DIR/bin/python" "$TMP_GETPIP"

"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel

# -----------------------------
# Install blastdbbuilder backend from bundled source
# -----------------------------
if [[ ! -d "${INSTALL_DIR}/app/blastdbbuilder_src" ]]; then
  echo "ERROR: blastdbbuilder_src not found inside app/"
  echo "Expected: ${INSTALL_DIR}/app/blastdbbuilder_src"
  exit 1
fi

echo "Installing blastdbbuilder backend..."
"$VENV_DIR/bin/python" -m pip install "${INSTALL_DIR}/app/blastdbbuilder_src"

# -----------------------------
# Install icon
# -----------------------------
if [[ -f "${INSTALL_DIR}/app/icons/blastdbbuilder.png" ]]; then
  cp "${INSTALL_DIR}/app/icons/blastdbbuilder.png" "${ICON_DIR}/blastdbbuilder.png"
fi

# -----------------------------
# Launcher
# -----------------------------
LAUNCHER="${BIN_DIR}/blastdbbuilder-gui"

cat > "$LAUNCHER" <<'EOF'
#!/usr/bin/env bash
set -e

APP_ROOT="$HOME/.local/share/blastdbbuilder-gui"
VENV="$APP_ROOT/venv"
APP_HOME="$APP_ROOT/app"

export PATH="$VENV/bin:$PATH"

exec "$APP_HOME/run_gui.sh"
EOF

chmod +x "$LAUNCHER"

# -----------------------------
# Desktop entry
# -----------------------------
DESKTOP_FILE="${DESKTOP_DIR}/blastdbbuilder.desktop"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=blastdbbuilder
Comment=Offline BLAST database builder (GUI)
Exec=${BIN_DIR}/blastdbbuilder-gui
Icon=blastdbbuilder
Terminal=false
Categories=Science;Bioinformatics;
EOF

chmod +x "$DESKTOP_FILE"

# Optional Desktop shortcut
if [[ -d "$HOME/Desktop" ]]; then
  cp "$DESKTOP_FILE" "$HOME/Desktop/blastdbbuilder.desktop" || true
  chmod +x "$HOME/Desktop/blastdbbuilder.desktop" || true
fi

command -v update-desktop-database >/dev/null 2>&1 && \
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true

echo
echo "✅ Installation complete."
echo "Launch from Applications menu: blastdbbuilder"
echo "Or double-click Desktop icon: blastdbbuilder"
echo
echo "Quick test:"
echo "  $VENV_DIR/bin/blastdbbuilder --help"
echo
