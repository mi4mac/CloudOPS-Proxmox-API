# Playbook: Refresh Proxmox Inventory

## Overview

The **> Refresh Proxmox Inventory** playbook compares the current VM and container list from Proxmox with the records in the FortiSOAR `v_m_instances` module and generates a synchronization report.

## Flow

1. **List VMs** – Fetch all VMs on the default node (from the connector configuration).
2. **List Containers** – Fetch all LXC containers on the default node.
3. **Get VM Instances** – Load all `v_m_instances` records from FortiSOAR.
4. **Build Sync Report** – Build Proxmox IDs and `vm_records`.
5. **Compute Orphaned and Not Tracked** – Calculate:
   - **Orphaned:** Records with a `proxmoxId` that no longer exist on Proxmox.
   - **Not Tracked:** Proxmox VMs/CTs that do not have a corresponding `v_m_instances` record.
6. **Set Sync Report** – Create an HTML report.
7. **Get Sync Log Record** – Look up a record with the name `Inventory-Sync-Log`.
8. **Has Sync Log Record?** – If it exists → **Append Report to Sync Log**, otherwise → **Create Sync Log Record** (automatically created once if missing).

## Report contents

- Number of Proxmox VMs and containers
- Number of `v_m_instances` records with a `proxmoxId` set
- **Orphaned:** FortiSOAR records whose VM/CT has been deleted on Proxmox
- **Not tracked:** Proxmox VMs/CTs without a FortiSOAR record

## Sync-log record (automatic)

To persist the report, the playbook uses a dedicated **v_m_instances** record:

- **Name:** `Inventory-Sync-Log` (exactly this value).

Behaviour:

- If this record already exists, the HTML report is appended on every run to the **Logs** field of that record.
- If the record does **not** exist, the step **Create Sync Log Record** will automatically create it (with just `name = Inventory-Sync-Log`). The first run in this state only shows the report in the **Execution Details**; from the second run onwards, the report is also appended to the log record.

## Prerequisites

- **proxmox-api** connector (v1.1.0) with a configured **Default Node Name**
- FortiSOAR **cyops_utilities** connector (for `make_cyops_request`, `no_op`)

## File

`playbooks/00 - Service Management/> Refresh Proxmox Inventory.json`
