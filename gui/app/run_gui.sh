#!/usr/bin/env bash
set -euo pipefail

APP_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(dirname "$APP_HOME")"
VENV="${APP_ROOT}/venv"

CONTAINER_DIR="${APP_HOME}/containers"

if command -v apptainer >/dev/null 2>&1; then
  export BLASTDBBUILDER_CONTAINER_ENGINE="apptainer"
elif command -v singularity >/dev/null 2>&1; then
  export BLASTDBBUILDER_CONTAINER_ENGINE="singularity"
else
  echo "ERROR: apptainer or singularity not found on PATH."
  exit 1
fi

export BLASTDBBUILDER_CONTAINER_DIR="${CONTAINER_DIR}"

export APPTAINER_CACHEDIR="${APP_HOME}/.apptainer_cache"
export APPTAINER_TMPDIR="${APP_HOME}/.apptainer_tmp"
mkdir -p "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR" || true

exec "${VENV}/bin/python" "${APP_HOME}/blastdbbuilder_gui_tk.py"
