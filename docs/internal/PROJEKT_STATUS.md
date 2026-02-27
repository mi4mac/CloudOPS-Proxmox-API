# Project Status: CloudOPS Proxmox API Migration

**Status:** Up to date  
**Goal:** Migrate from SSH-based provisioning to the Proxmox REST API in FortiSOAR.

---

## At a glance

| Area                    | Status | Details |
|-------------------------|--------|---------|
| **Proxmox (server)**    | ✅ Done | User, role, token, ACLs configured; API reachable |
| **API with token**      | ✅ OK   | Version, nextid, VM/CT lists, full VM/CT lifecycle via `proxmox-api` |
| **Resource checks via API** | ⚠️ Minimal | Only basic node/storage checks via API; deeper checks intentionally left out (would require extra Sys.Audit/Datastore.Audit) |
| **FortiSOAR (repo)**    | ✅ Ready | `proxmox-api` connector, solution pack, playbooks for provision/destroy **API‑only** (SSH provisioning removed) |
| **FortiSOAR (live)**    | ✅ Ready to install | Requires connector + pack import and configuration of globals/connector |

---

## What already works

### 1. Proxmox side – ✅

- Proxmox user and role created (see environment docs).  
- API token created and tested with curl.  
- Token format in all docs is now a **placeholder**, e.g.  
  `user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>`.

### 2. Proxmox API with this token – ✅

Working examples:

- `GET /api2/json/version`
- `GET /api2/json/cluster/nextid`
- `GET /api2/json/nodes/pve/qemu` (VM list)
- `GET /api2/json/nodes/pve/lxc` (container list)
- `GET /api2/json/nodes` (node status `online`)
- Full VM/CT lifecycle via the REST API (create/configure/start/stop/destroy).

Via the native FortiSOAR connector `proxmox-api`:

- Inventory:
  - `list_vms`, `list_containers`, `get_nodes`, `get_cluster_resources`
- Lifecycle:
  - `clone_vm`, `create_container`, `config_vm`, `start_*`, `stop_*`, `destroy_*`
- Monitoring:
  - `get_task_status` (UPID), plus optional status/resource operations  
    (see `TOKEN_CAPABILITIES.md` for required permissions).

### 3. Safety logic in playbooks – ✅

- Only VM/CT records with a stored `proxmoxId` can be destroyed.  
- Automatic cleanup only uses records with past `deleteAfter`.  
- Manual approval required when `deleteAfter` is missing or not expired.  
- `v_m_instances` module contains `proxmoxId` and `deleteAfter` and is updated consistently by the playbooks.

### 4. Repository preparation – ✅

- **Connector (HTTP):** `connectors/Proxmox API.json` plus configuration guide.  
- **Connector (native):** `proxmox-api/` with `API Connector Proxmox.tgz` (v1.1.0, including sample playbooks).  
- **Global variables:** Documented in `SCHRITT_2_GLOBAL_VARIABLES.md` and shipped in `playbooks/globalVariables.json`.  
- **Provision:** API‑based provisioning flow implemented.  
- **Destroy:** API‑based destroy flow implemented.  
- **Docs:** Checklists, testing guide, troubleshooting guide, next steps.  
- **Cleanup:** Old/obsolete docs removed.

---

## What is intentionally not API‑based

### Resource checks (RAM/disk)

- Endpoints such as `/nodes/pve/status` and storage status require `Sys.Audit` / `Datastore.Audit`.  
- The current Proxmox role intentionally does **not** grant these permissions.  
- **Decision:** Resource checks (e.g. `df`, `free`) remain via SSH; provisioning and destroy run via the **API**.

If you explicitly add `Sys.Audit` and `Datastore.Audit` to the Proxmox role (or use a higher‑privilege role), the existing `proxmox-api` connector can use the corresponding API endpoints (`get_node_status`, `get_storage_status`, `get_storage_content`, etc.) so that node and storage resource checks also run fully via the Proxmox REST API. This is optional and trades stronger visibility for a higher‑privilege token.

For details, see `RESOURCE_CHECKS_ALTERNATIVE.md`.

---

## Remaining work (in FortiSOAR)

All of this happens **inside the FortiSOAR UI**, not in the Git repository.

- **1. Install connector**  
  - Import `API Connector Proxmox.tgz` (Python connector `proxmox-api`).

- **2. Import solution pack**  
  - Import `CloudOPS Solution Pack Proxmox_Docker.zip`.  
  - This provides modules, views and all playbooks including API‑based provision/destroy.

- **3. Maintain global variables**  
  - Create/verify the variables from `SCHRITT_2_GLOBAL_VARIABLES.md` in FortiSOAR  
    (host, port, token, node, storage, templates, VLAN, gateway, etc.).

- **4. Configure the connector**  
  - In connector `proxmox-api`, set host/port/token (they are **not** shipped in the pack).  
  - Run the test operation `get_version`.

- **5. Run tests in FortiSOAR**  
  - Use the service request playbook to provision a CT/VM.  
  - Run the destroy playbook on the same record.  
  - Validate logs on `v_m_instances` (cmd_result, proxmoxId).

---

## Next concrete step

1. In FortiSOAR: go to **Settings → Global Variables**.  
2. Create all variables from `SCHRITT_2_GLOBAL_VARIABLES.md` (with the token encrypted).  
3. Then create and test the `Proxmox API` connector.

---

## Entry-point files

- **Overview & checklist:** `PACK_README.md`, `IMPLEMENTIERUNGS_CHECKLISTE.md`  
- **Connector configuration:** `CONNECTOR_KONFIGURATION.md`  
- **Global variables:** `SCHRITT_2_GLOBAL_VARIABLES.md`  
- **Tests:** `TESTING_GUIDE.md`  
- **Issues & troubleshooting:** `TROUBLESHOOTING_GUIDE.md`  
- **Token & permissions:** `TOKEN_CAPABILITIES.md`, `PROXMOX_9.1.5_SPECIFIC_NOTES.md`

---

*Last updated: 2026‑02‑24*
