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

echo "Building solution pack from $PACK_DIR..."
rm -f "$OUTPUT_ZIP"
zip -r "$OUTPUT_ZIP" "$PACK_DIR" -x "*.DS_Store" -x "__MACOSX/*"
echo "Created: $OUTPUT_ZIP"
ls -la "$OUTPUT_ZIP"
