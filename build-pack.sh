#!/usr/bin/env bash
# Build the CloudOPS Service Management solution pack for FortiSOAR import.
# Pack source (CloudOPS-Prx-pack-install/) mirrors a FortiSOAR content export:
# info.json, picklists, modules, views, roles, playbooks, connectors.
# Usage: ./build-pack.sh [output.zip]
# Default output: CloudOPS_Solution_Pack.zip

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PACK_DIR="CloudOPS-Prx-pack-install"
OUTPUT_ZIP="${1:-CloudOPS_Solution_Pack.zip}"

if [[ ! -d "$PACK_DIR" ]]; then
    echo "Error: $PACK_DIR not found."
    exit 1
fi

if [[ ! -f "$PACK_DIR/info.json" ]]; then
    echo "Error: $PACK_DIR/info.json not found."
    exit 1
fi

echo "Building connector archive..."
./build-connector.sh

echo "Syncing connectors into ${PACK_DIR}/connectors..."
mkdir -p "${PACK_DIR}/connectors"
cp -f connectors/data.json "${PACK_DIR}/connectors/"
cp -f "connectors/API Connector Proxmox.tgz" "${PACK_DIR}/connectors/"
rm -f "${PACK_DIR}/connectors"/proxmox-api_*.tgz

for PB in \
    'playbooks/00 - Service Management/> Provision VM Instances.json' \
    'playbooks/00 - Service Management/> Destroy VM Instance.json' \
    'playbooks/00 - Service Management/> Refresh Proxmox Inventory.json' \
    'playbooks/00 - Service Management/> Refresh Status from Proxmox.json'
do
    if [[ -f "$PB" && -f "${PACK_DIR}/${PB}" ]]; then
        cp -f "$PB" "${PACK_DIR}/${PB}"
    fi
done

echo "Updating solution pack export date..."
python3 <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
for path in (Path("CloudOPS-Prx-pack-install/info.json"), Path("info.json")):
    if not path.is_file():
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    data["date"] = now
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  {path}: date={now}")
PY

echo "Building solution pack from $PACK_DIR..."
rm -f "$OUTPUT_ZIP"
zip -r "$OUTPUT_ZIP" "$PACK_DIR" -x "*.DS_Store" -x "__MACOSX/*"
echo "Created: $OUTPUT_ZIP"
ls -la "$OUTPUT_ZIP"
