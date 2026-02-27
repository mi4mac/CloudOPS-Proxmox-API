CloudOPS Proxmox API
=====================

This repository contains a **FortiSOAR solution pack** and a **native Proxmox connector** to provision, manage, and destroy Proxmox VE VMs and containers via the REST API.

What’s included
---------------
- `proxmox-api/` – Python connector for the Proxmox VE API (`API Connector Proxmox.tgz` is built from this folder, current connector version **2.0.4**).
- `CloudOPS-Prx-pack-install/` – Solution pack source with:
  - `VM Instances`, `Network Interfaces` and `Proxmox Inventory` modules.
  - Playbooks for request → approve → provision → destroy → cleanup, plus **> Refresh Proxmox Inventory**.
  - UI layouts for list/detail views, including the **two‑row VM Instances list** (top: requested VMs/CTs, bottom: Proxmox inventory not tracked in `v_m_instances`).
  - Optional **Docker Containers** module, navigation entry, roles, and the **> Refresh Docker Inventory** playbook to sync Docker Engine containers into FortiSOAR.
- Prebuilt content:
  - `CloudOPS Solution Pack Proxmox_Docker.zip` – Importable solution pack built from `CloudOPS-Prx-pack-install/` (includes the `proxmox_inventory` module, inventory views, and the optional Docker Containers module + playbook wiring).
  - `API Connector Proxmox.tgz` – Importable connector package.
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
1. **Prepare Proxmox (user, role, token)**
   - Follow `PROXMOX_9.1.5_SPECIFIC_NOTES.md` and `TOKEN_CAPABILITIES.md` to:
     - Create a dedicated Proxmox user for FortiSOAR.
     - Create the `FortiSOAR-Role` with the required privileges.
     - Create an API token for that user and assign the role/ACLs.

2. **Connector**
   - Build the connector package:
     ```bash
     tar -czvf "API Connector Proxmox.tgz" "proxmox-api/"
     ```
   - Import `API Connector Proxmox.tgz` into FortiSOAR and create at least one configuration (host, port, API token).

3. **Solution pack**
   - Import `CloudOPS Solution Pack Proxmox_Docker.zip` via FortiSOAR Content Hub / Packs.
   - (Optional) Adjust global variables for your environment (node, storage, templates) as described in `SCHRITT_2_GLOBAL_VARIABLES.md` if you want to override the built‑in defaults.

4. **Quick test**
   - Follow `TESTING_GUIDE.md` for a small CT/VM provision + destroy smoke test.

Optional: Docker inventory integration
--------------------------------------
The pack can also surface Docker containers in a dedicated **Docker Containers** module and menu entry.

Prerequisites:
- A reachable Docker Engine API (for example `http://192.168.222.223:2375`).
- The **Docker** FortiSOAR connector installed and configured (repository: `mi4mac/docker`).

Steps:
1. **Configure the Docker connector**  
   - Server Address: Docker host IP (for example `192.168.222.223`).  
   - Port: Docker Engine TCP port (for example `2375`).  
   - Protocol: `HTTP` (or `HTTPS` if you have TLS configured).  
   - Verify SSL: disabled for plain HTTP, or configured with the correct CA/cert paths for HTTPS.  
   - Use the connector’s **Get Version** / **Get Info** operations to confirm connectivity.

2. **Import the solution pack**  
   - Import `CloudOPS Solution Pack Proxmox_Docker.zip` as usual.  
   - During import you should see:
     - The **Docker Containers** module as an existing module (if you already created it via UI) or a new module.  
     - The **Service Management → Docker** navigation entry.

3. **Make `dockerId` unique (post‑install)**  
   - In FortiSOAR go to **Settings → Modules → Docker Containers**.  
   - Ensure all existing Docker Container records have **unique** `dockerId` values (or clear them out if you are starting fresh).  
   - Configure `dockerId` as the unique key for the module and **Publish All Modules**.  
   - If you see an error like *“could not create unique index … duplicate records exist”*, delete the duplicates first and then publish again.

4. **Refresh Docker inventory**  
   - Run the **> Refresh Docker Inventory** playbook in the **00 - Service Management** collection.  
   - The playbook uses the Docker connector’s `list_containers` operation to upsert one record per container into the `docker_containers` module, keyed by `dockerId`, and updates `name`, `image`, `status`, and `lastSeen` on subsequent runs.

Security & placeholders
-----------------------
- Any API tokens or IPs in the docs are **placeholders** only (e.g. `user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>`); replace them with your own secure values in FortiSOAR.
- Do **not** commit real tokens, passwords or internal hostnames if you fork this repo.

Licensing
---------
- This project is licensed under the **MIT License**. See the `LICENSE` file for details.
