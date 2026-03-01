CloudOPS Proxmox API
=====================

This repository contains a **FortiSOAR solution pack** and a **native Proxmox connector** to provision, manage, and destroy Proxmox VE VMs and containers via the REST API. It also ships an optional Docker inventory integration.

What’s included
---------------
- `proxmox-api/` – Python connector for the Proxmox VE API (`API Connector Proxmox.tgz` is built from this folder, current connector version **2.0.4**).
- **`CloudOPS_Solution_Pack.zip`** – All-in-one importable solution pack (the only pack artifact in the repo). It includes:
  - **VM Instances**, **Network Interfaces**, and **Proxmox Inventory** modules.
  - Playbooks for request → approve → provision → destroy → cleanup, plus **> Refresh Proxmox Inventory**.
  - UI layouts for list/detail views, including the **two‑row VM Instances list** (top: requested VMs/CTs, bottom: Proxmox inventory not tracked in `v_m_instances`).
  - **Policy playbooks (FortiGate)** – **Policies** module, **SOC Review** dashboard, and **00 - Policy Playbooks**: **Import Fortigate Policies**, **Review Policy** (Mark as Approved / **Mark as Denied** → disable on FortiGate, **Refresh Firewall Policies**), **> Update comments on Fortigate**, and **Enable Policy**. See the **Policy playbooks (FortiGate)** section and `POLICY_PLAYBOOKS.md` for setup and post-import config UUID steps.
  - **Docker inventory (optional)** – **Docker Containers** module, navigation entry, roles, and the **> Refresh Docker Inventory** playbook are also shipped in the pack; use them with the Docker connector to sync Docker Engine containers into FortiSOAR. See **Optional: Docker inventory integration** below.
- Other prebuilt content:
  - `API Connector Proxmox.tgz` – Importable Proxmox connector package.
  - `docker-2.0.1.tgz` – Importable Docker connector package (from the `mi4mac/docker` connector).
- Documentation (English):
  - `PACK_README.md` – Pack overview, installation & upgrade.
  - `POLICY_PLAYBOOKS.md` – Policy playbooks (FortiGate): setup and config UUID replacement.
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

2. **Connectors**
   - Proxmox:
     ```bash
     tar -czvf "API Connector Proxmox.tgz" "proxmox-api/"
     ```
     Import `API Connector Proxmox.tgz` into FortiSOAR and create at least one configuration (host, port, API token).
   - Docker:
     - Import `docker-2.0.1.tgz` (Docker connector) into FortiSOAR.
     - Configure it to talk to your Docker Engine API endpoint (for example `http://10.0.0.100:2375`) and verify **Get Version** / **Get Info** succeed.

3. **Solution pack**
   - Import **`CloudOPS_Solution_Pack.zip`** (all-in-one pack) via FortiSOAR Content Hub / Packs.
   - (Optional) Adjust global variables for your environment (node, storage, templates) as described in `SCHRITT_2_GLOBAL_VARIABLES.md` if you want to override the built‑in defaults.

4. **Quick test**
   - Follow `TESTING_GUIDE.md` for a small CT/VM provision + destroy smoke test.

Policy playbooks (FortiGate)
----------------------------
**CloudOPS_Solution_Pack.zip** ships the full **00 - Policy Playbooks** collection: **Import Fortigate Policies**, **Review Policy** (Mark as Approved / Mark as Denied → disable on FortiGate, and Refresh Firewall Policies), **> Update comments on Fortigate**, and **Enable Policy**. The **Policies** module and **SOC Review** dashboard are included. See **POLICY_PLAYBOOKS.md** for details.

**Post-import: config UUID replacement.** Several steps use a placeholder config UUID (e.g. `a18df41f-7370-42b3-b2c2-c21162eadd07`). Config UUIDs are instance-specific. After import, set **Connector** and **Configuration** to your FortiGate in: (1) **> Update comments on Fortigate** → **Update Comments on Policy**; (2) **Review Policy** → **Disable Policy on FortiGate**; (3) **Enable Policy** → **Enable Policy** step. Use connector **Fortinet FortiGate** version **5.4.0** recommended.

**Connector API (5.2.0 vs 5.4.0):** Comment-only steps omit `action`/`status`; **Disable Policy on FortiGate** sends `status`: `disable`; **Enable Policy** sends `status`: `Enable`. See POLICY_PLAYBOOKS.md for full details.

Optional: Docker inventory integration
--------------------------------------
The pack **ships** an integrated **Docker Containers** module, navigation entry, and the **> Refresh Docker Inventory** playbook. Once the Docker connector is configured, you can surface Docker Engine containers in FortiSOAR.

Prerequisites:
- A reachable Docker Engine API (for example `http://10.0.0.100:2375`).
- The **Docker** FortiSOAR connector installed and configured (repository: `mi4mac/docker`).

Steps:
1. **Configure the Docker connector**  
   - Server Address: Docker host IP (for example `10.0.0.100`).  
   - Port: Docker Engine TCP port (for example `2375`).  
   - Protocol: `HTTP` (or `HTTPS` if you have TLS configured).  
   - Verify SSL: disabled for plain HTTP, or configured with the correct CA/cert paths for HTTPS.  
   - Use the connector’s **Get Version** / **Get Info** operations to confirm connectivity.

2. **Import the solution pack**  
   - Import **`CloudOPS_Solution_Pack.zip`** (all-in-one pack) as usual.  
   - During import you should see:
     - The **Docker Containers** module as an existing module (if you already created it via UI) or a new module.  
     - The **Service Management → Docker** navigation entry.

3. **Make `dockerId` unique (post‑install)**  
   - In FortiSOAR go to **Settings → Modules → Docker Containers**.  
   - Ensure all existing Docker Container records have **unique** `dockerId` values (or clear them out if you are starting fresh).  
   - Configure `dockerId` as the unique key for the module and **Publish All Modules**.  
   - If you see an error like *“could not create unique index … duplicate records exist”*, delete the duplicates first and then publish again.
   - Why `dockerId` (and not `name`): `dockerId` is globally unique and immutable per container, while names can be reused or collide across different Docker hosts, so using the name as the unique key can cause incorrect merges or conflicts.

4. **Refresh Docker inventory**  
   - Run the **> Refresh Docker Inventory** playbook in the **00 - Service Management** collection.  
   - The playbook uses the Docker connector’s `list_containers` operation to upsert one record per container into the `docker_containers` module, keyed by `dockerId`, and updates `name`, `image`, `status`, and `lastSeen` on subsequent runs.
   - **Image Size (MB) field**: The Docker Containers grid shows an `Image Size (MB)` column that is populated from Docker’s `SizeRootFs` value returned by `GET /containers/json?size=1`. This is the total container filesystem size (image layers + writable layer) and is typically larger than the base image size reported by `docker images` or GUI tools such as Portainer.

Security & placeholders
-----------------------
- Any API tokens or IPs in the docs are **placeholders** only (e.g. `user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>`); replace them with your own secure values in FortiSOAR.
- Do **not** commit real tokens, passwords or internal hostnames if you fork this repo.

Licensing
---------
- This project is licensed under the **MIT License**. See the `LICENSE` file for details.
