# Proxmox API Token – Capabilities and Permissions

This document lists what the FortiSOAR Proxmox API token can query and perform – and which additional permissions are required for extended features.

---

## 1. Current Token (FortiSOAR‑Role)

The token uses the role **FortiSOAR-Role** with the following privileges:

```text
Datastore.AllocateSpace, Datastore.Audit, Pool.Allocate,
Sys.Audit, Sys.Console, Sys.Modify, VM.Allocate, VM.Audit,
VM.Clone, VM.Config.CDROM, VM.Config.CPU, VM.Config.Cloudinit,
VM.Config.Disk, VM.Config.HWType, VM.Config.Memory, VM.Config.Network,
VM.Config.Options, VM.PowerMgmt, SDN.Use
```

**Note:** In the minimal role example for least privilege, `Sys.Audit` and `Datastore.Audit` may be intentionally omitted. Without them, resource checks (RAM/disk) via the API do not work – they continue to run via SSH instead (see `RESOURCE_CHECKS_ALTERNATIVE.md`).

---

## 2. What Works with the Current Token

### 2.1 Authentication and Metadata

| Connector Operation | API Endpoint                  | Description                                    |
|---------------------|-------------------------------|------------------------------------------------|
| `get_version`       | `GET /api2/json/version`      | Proxmox version, basic health check            |
| `get_next_vmid`     | `GET /api2/json/cluster/nextid` | Next free VMID                              |
| `get_nodes`         | `GET /api2/json/nodes`        | List of all nodes, online/offline status       |
| `get_cluster_resources` | `GET /api2/json/cluster/resources` | Cluster resources (minimal info without Sys.Audit) |

### 2.2 Inventory (without extended permissions)

| Connector Operation | API Endpoint                         | Description                         |
|---------------------|--------------------------------------|-------------------------------------|
| `list_vms`          | `GET /api2/json/nodes/{node}/qemu`  | All VMs on the node                 |
| `list_containers`   | `GET /api2/json/nodes/{node}/lxc`   | All LXC containers on the node      |

### 2.3 Task Monitoring

| Connector Operation | API Endpoint                                             | Description                                   |
|---------------------|----------------------------------------------------------|-----------------------------------------------|
| `get_task_status`   | `GET /api2/json/nodes/{node}/tasks/{upid}/status`       | Status of an asynchronous task (for example clone) |

### 2.4 VM / Container Lifecycle (Create, Configure, Start/Stop, Destroy)

| Connector Operation  | API Endpoint                                              | Description             |
|----------------------|-----------------------------------------------------------|-------------------------|
| `clone_vm`           | `POST /nodes/{node}/qemu/{vmid}/clone`                   | Clone VM                |
| `create_container`   | `POST /nodes/{node}/lxc`                                  | Create LXC container    |
| `config_vm`          | `PUT /nodes/{node}/qemu/{vmid}/config`                   | Configure VM           |
| `start_vm`           | `POST /nodes/{node}/qemu/{vmid}/status/start`            | Start VM                |
| `stop_vm`            | `POST /nodes/{node}/qemu/{vmid}/status/stop`             | Stop VM                 |
| `start_container`    | `POST /nodes/{node}/lxc/{vmid}/status/start`             | Start container         |
| `stop_container`     | `POST /nodes/{node}/lxc/{vmid}/status/stop`              | Stop container          |
| `destroy_vm`         | `DELETE /nodes/{node}/qemu/{vmid}?purge=1`               | Delete VM               |
| `destroy_container`  | `DELETE /nodes/{node}/lxc/{vmid}`                        | Delete container        |

### 2.5 Generic API Requests

| Connector Operation | Description                                                         |
|---------------------|---------------------------------------------------------------------|
| `api_request`       | Arbitrary GET/POST/PUT/DELETE request (path relative to `/api2/json/`) |

---

## 3. Operations Requiring Extended Permissions

The following operations are implemented in the connector, but only work **after** the corresponding Proxmox permissions are granted.

### 3.1 VM / Container Detail Status

| Connector Operation      | API Endpoint                                         | Required Permission |
|--------------------------|------------------------------------------------------|---------------------|
| `get_vm_status`          | `GET /nodes/{node}/qemu/{vmid}/status/current`      | `VM.Audit` on the VM |
| `get_container_status`   | `GET /nodes/{node}/lxc/{vmid}/status/current`       | `VM.Audit` on the container |

**Purpose:** Status (running/stopped), uptime, and CPU/memory details per VM/CT.

### 3.2 Node Resources (Memory, CPU)

| Connector Operation | API Endpoint                     | Required Permission |
|---------------------|----------------------------------|---------------------|
| `get_node_status`   | `GET /nodes/{node}/status`       | `Sys.Audit`         |

**Purpose:** Available RAM and CPU usage per node – replaces SSH‑based resource checks.

### 3.3 Storage Resources (Disk, Templates)

| Connector Operation   | API Endpoint                                 | Required Permission |
|-----------------------|----------------------------------------------|---------------------|
| `get_storage_status`  | `GET /nodes/{node}/storage/{storage}/status`| `Datastore.Audit`   |
| `get_storage_content` | `GET /nodes/{node}/storage/{storage}/content`| `Datastore.Audit`  |

**Purpose:**
- `get_storage_status`: Disk total/free/used per storage.
- `get_storage_content`: Templates and images – enables dynamic template lists instead of fixed global variables.

---

## 4. Adding Permissions (Optional)

If you want to perform resource checks or build template lists via the API:

```bash
# Add Sys.Audit and Datastore.Audit to the role
pveum rolemod FortiSOAR-Role -privs "+Sys.Audit,Datastore.Audit"
```

**Alternative:** Use the standard role `PVEVMAdmin` (more rights, less granular control):

```bash
pveum aclmod / -user fortisoar@pve -role PVEVMAdmin
```

For more details, see `RESOURCE_CHECKS_ALTERNATIVE.md` and `PROXMOX_9.1.5_SPECIFIC_NOTES.md`.

---

## 5. Connector Operations – Overview

### All 22 Connector Operations (proxmox-api 1.0.0)

| Operation             | Works with current token?            |
|-----------------------|--------------------------------------|
| `get_version`         | ✅                                   |
| `get_next_vmid`       | ✅                                   |
| `get_nodes`           | ✅                                   |
| `get_cluster_resources` | ✅ (minimal)                       |
| `list_vms`            | ✅                                   |
| `list_containers`     | ✅                                   |
| `get_task_status`     | ✅                                   |
| `clone_vm`            | ✅                                   |
| `create_container`    | ✅                                   |
| `config_vm`           | ✅                                   |
| `start_vm`            | ✅                                   |
| `stop_vm`             | ✅                                   |
| `start_container`     | ✅                                   |
| `stop_container`      | ✅                                   |
| `destroy_vm`          | ✅                                   |
| `destroy_container`   | ✅                                   |
| `get_vm_status`       | ⚠️ Requires `VM.Audit` on the VM     |
| `get_container_status`| ⚠️ Requires `VM.Audit` on the container |
| `get_node_status`     | ⚠️ Requires `Sys.Audit`              |
| `get_storage_status`  | ⚠️ Requires `Datastore.Audit`        |
| `get_storage_content` | ⚠️ Requires `Datastore.Audit`        |
| `api_request`         | ✅ (depending on endpoint)           |

---

## 6. Sample Playbooks in the Connector

The connector ships with sample playbooks for all operations, including:

- Test Proxmox Connection
- Get Next VMID
- List VMs (Sample)
- List Containers (Sample)
- Get Nodes (Sample)
- Get Task Status (Sample)
- Clone VM (Sample)
- Create Container (Sample)
- Destroy VM (Sample)
- Destroy Container (Sample)
- API Request Generic (Sample)

---

## 7. References

- `RESOURCE_CHECKS_ALTERNATIVE.md` – Resource checks via SSH.
- `PROXMOX_9.1.5_SPECIFIC_NOTES.md` – Proxmox‑specific notes.
- `API_IMPLEMENTATION_GUIDE.md` – API implementation details.
- `proxmox-api/README.md` – Connector documentation.

---

*Created: 2026‑02‑23*

