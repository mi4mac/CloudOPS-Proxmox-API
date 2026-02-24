CloudOPS Proxmox API
=====================

This repository contains a **FortiSOAR solution pack** and a **native Proxmox connector** to provision, manage, and destroy Proxmox VE VMs and containers via the REST API.

What’s included
---------------
- `proxmox-api/` – Python connector for the Proxmox VE API (`API Connector Proxmox.tgz` can be built from this folder).
- `pack_build/CloudOPS-Prx-pack-install/` – Solution pack with:
  - `VM Instances` and `Network Interfaces` modules.
  - Playbooks for request → approve → provision → destroy → cleanup.
  - UI layouts for list/detail views.
- Prebuilt content:
  - `solution-pack-proxmox-api-migration.zip` – Importable solution pack.
- Documentation (English):
  - `PACK_README.md` – Pack overview, installation & upgrade.
  - `SCHRITT_2_GLOBAL_VARIABLES.md` – Proxmox‑related global variables (step‑by‑step).
  - `REFRESH_INVENTORY_PLAYBOOK.md` – Details for the "> Refresh Proxmox Inventory" playbook.
  - `TOKEN_CAPABILITIES.md` – Proxmox API token capabilities and required permissions.
  - `PROXMOX_9.1.5_SPECIFIC_NOTES.md` – Environment‑specific Proxmox 9.1.5 notes.
  - `TESTING_GUIDE.md` – End‑to‑end and regression test scenarios.
  - `TROUBLESHOOTING_GUIDE.md` – Common issues and troubleshooting steps.
  - `proxmox-api/playbooks/Proxmox API Samples/README.md` – Sample playbooks for each connector operation.
  - `docs/internal/PROJEKT_STATUS.md` – Internal project status for this migration.
  - `docs/internal/IMPLEMENTIERUNGS_CHECKLISTE.md` – Internal implementation checklist (SSH → API migration).

Installation (high level)
-------------------------
1. **Connector**
   - Build the connector package:
     ```bash
     tar -czvf "API Connector Proxmox.tgz" "proxmox-api/"
     ```
   - Import `API Connector Proxmox.tgz` into FortiSOAR and create at least one configuration (host, port, API token).

2. **Solution pack**
   - Import `solution-pack-proxmox-api-migration.zip` via FortiSOAR Content Hub / Packs.
   - Adjust global variables for your environment (host, token, node, storage, templates) as described in `SCHRITT_2_GLOBAL_VARIABLES.md`.

3. **Quick test**
   - Follow `TESTING_GUIDE.md` for a small CT/VM provision + destroy smoke test.

Security & placeholders
-----------------------
- Any API tokens or IPs in the docs are **placeholders** only (e.g. `user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>`); replace them with your own secure values in FortiSOAR.
- Do **not** commit real tokens, passwords or internal hostnames if you fork this repo.

Licensing
---------
- This project is licensed under the **MIT License**. See the `LICENSE` file for details.
