#!/usr/bin/env bash
# Build proxmox-api connector .tgz from proxmox-api/ (version from info.json).
# Usage: ./build-connector.sh
# Output: connectors/proxmox-api_<version>.tgz and connectors/API Connector Proxmox.tgz

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SRC="proxmox-api"
OUT_DIR="connectors"
INFO="$SRC/info.json"

if [[ ! -f "$INFO" ]]; then
    echo "Error: $INFO not found."
    exit 1
fi

VERSION="$(python3 -c "import json; print(json.load(open('$INFO'))['version'])")"
TGZ="$OUT_DIR/proxmox-api_${VERSION}.tgz"
ALIAS="$OUT_DIR/API Connector Proxmox.tgz"

mkdir -p "$OUT_DIR"
export COPYFILE_DISABLE=1

MTIME_EPOCH="$(date +%s)"
TAR_EXTRA=()
if tar --help 2>&1 | grep -q -- '--mtime'; then
    TAR_EXTRA=(--mtime="@${MTIME_EPOCH}")
fi

echo "Building connector proxmox-api ${VERSION} -> ${TGZ}"
rm -f "$TGZ"
tar "${TAR_EXTRA[@]}" -czf "$TGZ" -C "$SRC" .
cp -f "$TGZ" "$ALIAS"

# Drop stale versioned archives (keep docker + current proxmox tgz)
find "$OUT_DIR" -maxdepth 1 -name 'proxmox-api_*.tgz' ! -name "proxmox-api_${VERSION}.tgz" -delete 2>/dev/null || true

ls -la "$TGZ" "$ALIAS"
echo "Connector ${VERSION} built ($(date -u +%Y-%m-%dT%H:%M:%SZ))."
