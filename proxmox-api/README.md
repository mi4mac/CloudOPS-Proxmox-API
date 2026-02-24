# API Connector Proxmox

Native FortiSOAR connector for the **Proxmox VE REST API**. One connector instance represents a configuration (host, port, API token); you can create multiple configurations (for example per environment or per customer).

## Structure (FortiSOAR connector package)

```
proxmox-api/
├── connector.py       # Connector class (execute, check_health)
├── operations.py      # Proxmox API operations
├── info.json          # Metadata, configuration, operations
├── requirements.txt   # Python dependencies (requests)
├── playbooks/
│   ├── __init__.py
│   ├── playbooks.json       # Sample playbooks (type "workflow_collections", data with collection + workflows)
│   └── Proxmox API Samples/ # Individual files only as reference; import uses playbooks.json
├── images/
│   ├── proxmox_small.png    # optional
│   └── proxmox_large.png    # optional
└── README.md
```

## Configuration (per connector instance)

| Field      | Description                                      |
|-----------|--------------------------------------------------|
| Hostname  | IP address or hostname of the Proxmox VE server  |
| Port      | API port (default: 8006)                         |
| Verify SSL| Verify server SSL certificate                    |
| API Token | PVEAPIToken (user@realm!tokenid=secret)          |

No global variables are required – everything is stored in the connector configuration.

## Operations

### Basic & metadata
- **Get Version** – Query Proxmox version  
- **Get Next VMID** – Get next free VMID  
- **Get Nodes** – Cluster nodes and status (online/offline)  
- **Get Cluster Resources** – Cluster resources (optionally filtered)  

### Inventory
- **List VMs** – All VMs on a node  
- **List Containers** – All LXC containers on a node  

### Lifecycle (VM/container)
- **Clone VM** – Clone a VM from a template  
- **Create Container** – Create an LXC container  
- **Configure VM** – Configure VM (cloud-init, networking)  
- **Start/Stop VM** – Start/stop VM  
- **Start/Stop Container** – Start/stop container  
- **Destroy VM / Destroy Container** – Delete VM/container  

### Monitoring (some operations require additional permissions)
- **Get Task Status** – Status of asynchronous tasks (for example clone job)  
- **Get VM Status** – Detailed status of a VM (requires VM.Audit)  
- **Get Container Status** – Detailed status of a container (requires VM.Audit)  
- **Get Node Status** – Node resources memory/CPU (requires Sys.Audit)  
- **Get Storage Status** – Storage disk info (requires Datastore.Audit)  
- **Get Storage Content** – Templates/images (requires Datastore.Audit)  

### Generic
- **API Request (Generic)** – Arbitrary API call (GET/POST/PUT/DELETE)

For each operation there are **sample playbooks** in the collection `Sample - API Connector Proxmox - 1.0.0`. Token capabilities and permission requirements: `TOKEN_CAPABILITIES.md` in the project root.  

## Import into FortiSOAR

1. Package the folder as `.tgz`:
   ```bash
   tar -czvf "API Connector Proxmox.tgz" "proxmox-api/"
   ```
2. In FortiSOAR: **Content Hub** or **Connectors** → **Add Connector** → select the file.
3. Create a configuration (host, port, API token) and save.
4. In playbooks, select the connector and the desired operation.

## Proxmox API

- [Proxmox API Viewer](https://pve.proxmox.com/pve-docs/api-viewer/)  
- Authentication: `Authorization: PVEAPIToken=user@realm!tokenid=secret`

---

## Changelog

**1.1.0**
- New operations: list_vms, list_containers, get_task_status, get_nodes, get_cluster_resources  
- New operations (extended permissions): get_vm_status, get_container_status, get_node_status, get_storage_status, get_storage_content  
- 4 additional sample playbooks: List VMs, List Containers, Get Nodes, Get Task Status  
- Documentation: `TOKEN_CAPABILITIES.md` in the project root  

---

*Version 1.1.0 | Built for Proxmox VE 9.x*
