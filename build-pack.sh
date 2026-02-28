#!/usr/bin/env bash
# Build the CloudOPS Proxmox + Policy solution pack for FortiSOAR import.
# Usage: ./build-pack.sh [output.zip]
# Default output: CloudOPS_Solution_Pack.zip (slim build, excludes optional content)
#
# Excluded from slim build:
#   - Activate all users.json (training playbook)
#   - TESTING_GUIDE.md, SCHRITT_2_GLOBAL_VARIABLES.md (docs)
#   - README.md (pack root; PACK_README.md retained)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PACK_DIR="CloudOPS-Prx-pack-install"
OUTPUT_ZIP="${1:-CloudOPS_Solution_Pack.zip}"

if [[ ! -d "$PACK_DIR" ]]; then
    echo "Error: $PACK_DIR not found."
    exit 1
fi

echo "Building solution pack from $PACK_DIR (slim build)..."
rm -f "$OUTPUT_ZIP"
zip -r "$OUTPUT_ZIP" "$PACK_DIR" \
    -x "*.DS_Store" \
    -x "__MACOSX/*" \
    -x "CloudOPS-Prx-pack-install/playbooks/00 - Policy Playbooks/Activate all users.json" \
    -x "CloudOPS-Prx-pack-install/TESTING_GUIDE.md" \
    -x "CloudOPS-Prx-pack-install/SCHRITT_2_GLOBAL_VARIABLES.md" \
    -x "CloudOPS-Prx-pack-install/README.md"
echo "Created: $OUTPUT_ZIP"
ls -la "$OUTPUT_ZIP"
