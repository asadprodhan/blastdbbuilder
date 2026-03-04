#!/usr/bin/env bash
set -euo pipefail

APP_NAME="blastdbbuilder-gui"
INSTALL_DIR="$HOME/.local/share/${APP_NAME}"
BIN_FILE="$HOME/.local/bin/blastdbbuilder-gui"
APP_DESKTOP="$HOME/.local/share/applications/blastdbbuilder.desktop"
DESKTOP_SHORTCUT="$HOME/Desktop/blastdbbuilder.desktop"
ICON_FILE="$HOME/.local/share/icons/hicolor/256x256/apps/blastdbbuilder.png"

echo "== Uninstalling ${APP_NAME} =="

rm -rf "$INSTALL_DIR" || true
rm -f "$BIN_FILE" || true
rm -f "$APP_DESKTOP" || true
rm -f "$DESKTOP_SHORTCUT" || true
rm -f "$ICON_FILE" || true

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true

echo "✅ Uninstalled."
read -rp "Press Enter to close..."
