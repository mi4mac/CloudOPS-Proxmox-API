#!/usr/bin/env bash
# Build connectors/API Connector Proxmox.tgz for FortiSOAR import.
# Archive MUST contain proxmox-api/ at the top level (see proxmox-api/README.md).
# Usage: ./build-connector.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SRC="proxmox-api"
OUT="connectors/API Connector Proxmox.tgz"

if [[ ! -f "$SRC/info.json" ]]; then
    echo "Error: $SRC/info.json not found."
    exit 1
fi

export COPYFILE_DISABLE=1
rm -f "$OUT"
tar -czf "$OUT" "$SRC/"

VERSION="$(tar -xOf "$OUT" proxmox-api/info.json | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])")"
if ! tar -xOf "$OUT" proxmox-api/operations.py | grep -q '_current_vm_disk_size_gb'; then
    echo "Error: resize fix missing from $OUT"
    exit 1
fi

ls -la "$OUT"
echo "Built API Connector Proxmox.tgz (connector version ${VERSION})."
echo "Import this file in FortiSOAR with Delete all existing versions if upgrading."
