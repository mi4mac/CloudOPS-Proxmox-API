CloudOPS Proxmox Pack
======================

This FortiSOAR solution pack provides playbooks and data models to request, provision, and destroy Proxmox VE VMs and containers, plus an inventory sync.

Requirements
------------
- FortiSOAR 7.2.0 or later
- Proxmox VE with API access and a token
- Proxmox API connector (`proxmox-api`) installed from `API Connector Proxmox.tgz`
- Docker Engine API reachable from FortiSOAR (for Docker inventory, via `docker-2.0.1.tgz`)

Proxmox preparation (mandatory)
-------------------------------
Before installing the connector and pack, prepare Proxmox as follows (see `PROXMOX_9.1.5_SPECIFIC_NOTES.md` and `TOKEN_CAPABILITIES.md` for full commands and explanations):

1. **Create a dedicated FortiSOAR user and role**
   - Create a Proxmox user (for example `fortisoar@pve`).
   - Create the custom role `FortiSOAR-Role` with the minimal privileges listed in `PROXMOX_9.1.5_SPECIFIC_NOTES.md` (covers VM/CT lifecycle and required datastore permissions).
2. **Create an API token for that user**
   - Create a token (for example `fortisoar-token`) and store the token value securely.
   - Use the `PVEAPIToken={user}@{realm}!{token_id}={token_secret}` format when configuring the connector.
3. **Assign the role/ACLs to the user and/or token**
   - Assign `FortiSOAR-Role` on `/` (and, if needed, on your storage paths) to the user or token as shown in the Proxmox notes.

Contents
--------
- Modules and views for VM instances, network interfaces, and **Proxmox inventory** (`proxmox_inventory`).
- Optional **Docker Containers** module and views for Docker Engine containers (see “Docker inventory (optional)” below).
- Playbooks for requesting, provisioning, destroying, and refreshing Proxmox inventory.
- The **> Refresh Docker Inventory** playbook (optional) to sync Docker Engine containers into the Docker Containers module.
- **Policy playbooks (FortiGate)** (shipped in the pack): **Import Fortigate Policies**, **PB_REF_LinkPolicyToFirewallAsset_BySerial**, **Archive Deleted Firewall Policies**, **Review Policy** (with Mark as Denied → disable on FortiGate and Refresh Firewall Policies), **> Update comments on Fortigate**, and **Enable Policy**. See **Policy playbooks (FortiGate)** below for setup and post-import config UUID replacement.
- Optional global variables to override default node, storage, network, and template settings
- A sample **actor** (`atlas Me`) and an **AD user enrichment** flow that demonstrate how to plug into an existing directory / user model – these must be adapted to the real users and directory integration in your environment.

Installation
------------
1. Import the connector package `API Connector Proxmox.tgz` in FortiSOAR.
2. Import the Docker connector package `docker-2.0.1.tgz` in FortiSOAR.
3. Configure the `proxmox-api` connector with the correct **host**, **port**, and **API token** (these values are read from the connector configuration, not from global variables). The inventory features described below require connector version **2.0.4** or later.
4. Configure the `docker` connector with the correct Docker Engine API endpoint (for example `http://192.168.222.223:2375`) and verify **Get Version** / **Get Info** succeed.
5. Import this solution pack from **`CloudOPS_Solution_Pack.zip`** (all-in-one pack; the pack artifact is tracked in the repo).
6. (Optional) If you want to override the built‑in defaults for node, storage, network, or templates, create/update the corresponding Proxmox global variables as described in `SCHRITT_2_GLOBAL_VARIABLES.md`.

Upgrade
-------
To upgrade from a previous version of this pack:

1. **Connector**: Ensure you are using the latest `API Connector Proxmox.tgz` (version **2.0.4** or later) shipped with this repo. It includes improved inventory operations (`list_vms` / `list_containers` with config fetching and human‑friendly disk/interface summaries).
2. **Pack import**: Import the updated **`CloudOPS_Solution_Pack.zip`** into FortiSOAR. Existing data in `v_m_instances`, `network_interfaces` and `proxmox_inventory` is preserved.
3. **Global variables** (optional): After import, you can review the Proxmox global variables and adjust them if you want to override the defaults for node, storage, network, or templates. See `SCHRITT_2_GLOBAL_VARIABLES.md` for details.
4. **Roles / permissions**: Make sure users who should manage VMs have access to the `VM Instances` and `Proxmox Inventory` modules and relevant playbooks.

Post-upgrade quick test
-----------------------
1. **Provision test**  
   - Use the service request flow to create a small CT (e.g. `Debian13-CT`, 1 CPU / 2048 MB / 5 GB / 512 MB swap).  
   - Verify on Proxmox that the CT/VM is created and started.  
   - In FortiSOAR, check the VM Instance record: `Proxmox ID` is set and `Status` is **Active**.

2. **Destroy test**  
   - From the VM Instance detail view, use **Destroy VM Instance**.  
   - Confirm that the CT/VM is removed on Proxmox and the record status is updated to **Destroyed** with appropriate logs.

3. **Expired cleanup (optional)**  
   - Configure a schedule to run the **Destroy Expired VM Instances** playbook.  
   - It finds VM Instances with `deleteAfter` in the past, status **Active**, and a non-empty `Proxmox ID`, then calls the destroy workflow for each and sends a summary email to the infrastructure team.

Policy playbooks (FortiGate)
----------------------------
The pack ships the **00 - Policy Playbooks** collection: **Import Fortigate Policies**, **PB_REF_LinkPolicyToFirewallAsset_BySerial**, **Archive Deleted Firewall Policies**, **Review Policy** (Mark as Approved / Mark as Denied → disable on FortiGate, Refresh Firewall Policies), **> Update comments on Fortigate**, and **Enable Policy**, plus the **Policies** module and **SOC Review** dashboard.

**Prerequisites**
- FortiGate connector (**Fortinet FortiGate**) installed and at least one configuration pointing at your firewall.
- Connector version **5.4.0** recommended (the playbooks use the 5.4.0 `update_policy` param shape; 5.2.0 had optional `action` and `status` keys, which are omitted here).

**Post-import: config UUID replacement (required)**  
Several steps are stored with a placeholder config UUID (e.g. `a18df41f-7370-42b3-b2c2-c21162eadd07`). Config UUIDs are instance-specific. After importing the pack, set **Connector** and **Configuration** to your FortiGate in: (1) **> Update comments on Fortigate** → **Update Comments on Policy**; (2) **Review Policy** → **Disable Policy on FortiGate**; (3) **Enable Policy** → **Enable Policy** step. See **POLICY_PLAYBOOKS.md** for the full list and details.

**Playbook roles**
- **Import Fortigate Policies**: Fetches policies from the FortiGate and upserts them into the **Policies** module. Can be run manually or on a schedule.
- **PB_REF_LinkPolicyToFirewallAsset_BySerial**: Reference playbook called by **Import Fortigate Policies** to link policy records to firewall assets by serial (`policies.fortiGateSerial` -> `assets.serialNumber`).
- **Archive Deleted Firewall Policies**: Optional retention playbook. Supports `retentionDays` and `dryRun`, prepares a visible candidate list, and archives old soft-deleted policies.
- **Review Policy**: Manual task for SOC analysts: **Mark as Approved**, **Mark as Denied**, or email NOC. For **Mark as Denied**, disables the policy on FortiGate and runs **Refresh Firewall Policies**; for **Mark as Approved**, adds justification and triggers **> Update comments on Fortigate**.
- **> Update comments on Fortigate**: Triggered when a policy’s `businessJustification` changes; pushes the comment to the FortiGate policy and marks the policy review complete (sets `reviewComplete`, `lastReviewedTime`, `nextReviewTime`, `auditStatus`).
- **Enable Policy**: Enables a disabled firewall policy on FortiGate, then runs **Refresh Firewall Policies** to re-import policies.

Recommended scheduler settings (import cadence, daily archive window, and `dryRun` rollout) are documented in `POLICY_PLAYBOOKS.md`.

Usage
-----
- Use the service management playbooks to request and provision VMs/containers.
- Use the destroy playbooks to remove instances.
- Use the "> Refresh Proxmox Inventory" playbook to:
  - Sync Proxmox VMs/CTs into the `proxmox_inventory` module (including CPU, memory, disk, disks summary, interfaces summary).
  - Mark items as **tracked** when they have a corresponding `v_m_instances` record.
  - Populate the second grid in the `VM Instances` list view with **untracked** Proxmox VMs/CTs (inventory items not yet requested in FortiSOAR).

Docker inventory (optional)
---------------------------
If you also want to track Docker containers in FortiSOAR:

1. **Install and configure the Docker connector**
   - Install the Docker connector (for example from the `mi4mac/docker` repository).  
   - Configure it to talk to your Docker Engine API (for example `http://192.168.222.223:2375`) and verify **Get Version** / **Get Info** succeed.

2. **Docker Containers module**
   - This pack includes an optional **Docker Containers** module, views, navigation item under **Service Management → Docker**, and the **> Refresh Docker Inventory** playbook.
   - After import, go to **Settings → Modules → Docker Containers** and ensure:
     - All existing records have unique `dockerId` values (or clear records if you are starting fresh).
     - `dockerId` is configured as the unique key and **Publish All Modules** succeeds.  
       - If you see a publish error about a *unique index* and **duplicate records**, delete the duplicate `dockerId` rows first and publish again.

3. **Refresh Docker inventory**
   - Run the **> Refresh Docker Inventory** playbook in the **00 - Service Management** collection.
   - The playbook calls the Docker `list_containers` operation and upserts one record per container into the `docker_containers` module, keyed by `dockerId`. Subsequent runs update existing records (status, image, `lastSeen`, etc.) instead of creating duplicates.
   - **Image Size (MB) field**: The Docker Containers grid shows an `Image Size (MB)` column that is populated from Docker’s `SizeRootFs` value returned by `GET /containers/json?size=1` (total container filesystem size), so it is usually larger than the base image size reported by `docker images` or GUI tools such as Portainer.

Related documentation
---------------------
- `POLICY_PLAYBOOKS.md` – Policy playbooks (FortiGate): setup, config UUID replacement, and playbook roles.
- `SCHRITT_2_GLOBAL_VARIABLES.md` – Step‑by‑step guide for the Proxmox global variables used by this pack.
- `REFRESH_INVENTORY_PLAYBOOK.md` – Design and behaviour of the "> Refresh Proxmox Inventory" playbook.
- `TOKEN_CAPABILITIES.md` – Overview of the Proxmox API token role and which connector operations it enables.
- `PROXMOX_9.1.5_SPECIFIC_NOTES.md` – Proxmox 9.1.5 specifics relevant for this integration.
- `TESTING_GUIDE.md` – Suggested test plan before rolling out this pack.
- `TROUBLESHOOTING_GUIDE.md` – Troubleshooting checklist for common provisioning/destroy issues.
