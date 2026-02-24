# Proxmox API Samples

This playbook collection is shipped with the **API Connector Proxmox** connector. There is a sample playbook for each connector operation.

## Playbooks (All Operations)

| Playbook                       | Operation        | Description                                           |
|--------------------------------|------------------|-------------------------------------------------------|
| **Test Proxmox Connection**    | `get_version`    | Query Proxmox version and verify the connection.      |
| **Get Next VMID**              | `get_next_vmid`  | Retrieve the next available VMID.                     |
| **Clone VM (Sample)**          | `clone_vm`       | Clone a VM from a template.                           |
| **Create Container (Sample)**  | `create_container` | Create an LXC container.                            |
| **Configure VM (Sample)**      | `config_vm`      | Configure a VM (for example cloud‑init, network).     |
| **Start VM (Sample)**          | `start_vm`       | Start a VM.                                           |
| **Start Container (Sample)**   | `start_container`| Start an LXC container.                               |
| **Stop Container (Sample)**    | `stop_container` | Stop an LXC container.                                |
| **Destroy VM (Sample)**        | `stop_vm` + `destroy_vm` | Stop and delete a VM.                        |
| **Destroy Container (Sample)** | `stop_container` + `destroy_container` | Stop and delete a container. |
| **API Request Generic (Sample)** | `api_request`  | Execute an arbitrary API request (GET/POST/PUT/DELETE). |

## Usage

1. Import the **API Connector Proxmox** (`proxmox-api`) into FortiSOAR and create a connector configuration (host, port, API token).
2. When running a sample playbook, select the appropriate **connector configuration**.
3. In the sample steps, adjust parameters (node, vmid, name, url_path, …) for your environment or pass them via variables.

