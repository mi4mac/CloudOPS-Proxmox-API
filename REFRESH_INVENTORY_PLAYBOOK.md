# Playbook: Refresh Proxmox Inventory

## Overview

The **> Refresh Proxmox Inventory** playbook:

- Pulls the current VM and container list from Proxmox (including config for disks and interfaces).
- Upserts a lightweight snapshot into the `proxmox_inventory` module (one record per VM/CT).
- Compares this inventory with the FortiSOAR `v_m_instances` module and generates a synchronization report.

This powers the **two‑row `VM Instances` list view**:

- **Top grid:** Requested / managed instances (`v_m_instances`).
- **Bottom grid:** Proxmox VMs/CTs that exist on Proxmox but are **not yet tracked** in `v_m_instances` (`proxmox_inventory` with `tracked = false`).

## Flow

1. **List VMs** – Fetch all VMs on the default node (from the connector configuration), with config and computed disk/interface summaries.
2. **List Containers** – Fetch all LXC containers on the default node, with config and computed disk/interface summaries.
3. **Get VM Instances** – Load all `v_m_instances` records from FortiSOAR.
4. **Build Sync Report** – Build Proxmox IDs and `vm_records`.
5. **Compute Orphaned and Not Tracked** – Calculate:
   - **Orphaned:** Records with a `proxmoxId` that no longer exist on Proxmox.
   - **Not Tracked:** Proxmox VM/CT IDs that do not have a corresponding `v_m_instances` record.
6. **Sync Proxmox VMs** – For each VM from Proxmox, **upsert** a record in `proxmox_inventory` via `/api/3/upsert/proxmox_inventory`:
   - Keyed by `proxmoxId`.
   - Stores name, node, type, status, CPU cores, memory (MB), disk (GB), last‑seen timestamp.
   - Stores human‑friendly **Disks** and **Interfaces** summaries based on Proxmox config.
   - Sets `tracked = true` if there is a matching `v_m_instances.proxmoxId`, otherwise `false`.
7. **Sync Proxmox Containers** – Same as step 6, but for LXC containers.
8. **Set Sync Report** – Create an HTML report.
9. **Get Sync Log Record** – Look up a record with the name `Inventory-Sync-Log`.
10. **Has Sync Log Record?** – If it exists → **Append Report to Sync Log**, otherwise → **Create Sync Log Record** (automatically created once if missing).

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

**Design note:** In the FortiSOAR playbook UI the steps **Append Report to Sync Log**, **Create Sync Log Record** and **Has Sync Log Record** can look visually “unconnected”, but they are still wired via the conditional step **Has Sync Log Record** and are required for the sync‑log feature to work. Do **not** delete these steps unless you intentionally remove the entire sync‑log behaviour. The step **No Sync Log Record** is optional and can be safely removed if you do not need it.

## Prerequisites

- **proxmox-api** connector (version **2.0.4** or later) with a configured **Default Node Name**.
  - The connector’s `list_vms` / `list_containers` operations must support `include_config` and compute `disksSummary` and `interfacesSummary`.
- FortiSOAR **cyops_utilities** connector (for `make_cyops_request`, `no_op`).

## File

`playbooks/00 - Service Management/> Refresh Proxmox Inventory.json`
