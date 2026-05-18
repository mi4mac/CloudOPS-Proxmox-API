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

RELEASE_DIR="releases"
mkdir -p "$RELEASE_DIR"
INSTALL_TGZ="${RELEASE_DIR}/proxmox-api_${VERSION}_INSTALL_THIS.tgz"
PACK_ZIP="${RELEASE_DIR}/API_Connector_Proxmox_Pack.zip"
cp -f "$TGZ" "$INSTALL_TGZ"
shasum -a 256 "$TGZ" | tee "${RELEASE_DIR}/proxmox-api_${VERSION}.sha256"
rm -f "$PACK_ZIP"
zip -q -j "$PACK_ZIP" \
    "$INSTALL_TGZ" \
    "${RELEASE_DIR}/proxmox-api_${VERSION}.sha256"
ls -la "$TGZ" "$ALIAS" "$INSTALL_TGZ" "$PACK_ZIP"
echo "Connector ${VERSION} built ($(date -u +%Y-%m-%dT%H:%M:%SZ))."
echo "FortiSOAR: upload ${INSTALL_TGZ} or unzip ${PACK_ZIP} and upload the .tgz inside."
