#!/usr/bin/env bash
# Build connectors/Proxmox VE Hypervisor.tgz for FortiSOAR import.
# Archive MUST contain proxmox-ve/ at the top level (see proxmox-ve/README.md).
# Usage: ./build-connector.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SRC="proxmox-ve"
OUT="connectors/Proxmox VE Hypervisor.tgz"
LEGACY="connectors/API Connector Proxmox.tgz"

if [[ ! -f "$SRC/info.json" ]]; then
    echo "Error: $SRC/info.json not found."
    exit 1
fi

export COPYFILE_DISABLE=1
rm -f "$OUT" "$LEGACY"
tar -czf "$OUT" "$SRC/"

VERSION="$(tar -xOf "$OUT" proxmox-ve/info.json | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])")"
if ! tar -xOf "$OUT" proxmox-ve/operations.py | grep -q '_current_vm_disk_size_gb'; then
    echo "Error: resize fix missing from $OUT"
    exit 1
fi

cp -f "$OUT" "$LEGACY"

ls -la "$OUT" "$LEGACY"
echo "Built Proxmox VE Hypervisor.tgz (proxmox-ve ${VERSION})."
echo "FortiSOAR: upload with Delete all existing versions when upgrading from proxmox-api."
