CloudOPS Proxmox Pack
======================

This FortiSOAR solution pack provides playbooks and data models to request, provision, and destroy Proxmox VE VMs and containers, plus an inventory sync.

Requirements
------------
- FortiSOAR 7.2.0 or later
- Proxmox VE with API access and a token
- Proxmox API connector (`proxmox-api`) installed from `API Connector Proxmox.tgz`

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
- Modules and views for VM instances and network interfaces
- Playbooks for requesting, provisioning, destroying, and refreshing Proxmox inventory
- Optional global variables to override default node, storage, network, and template settings
- A sample **actor** (`atlas Me`) and an **AD user enrichment** flow that demonstrate how to plug into an existing directory / user model – these must be adapted to the real users and directory integration in your environment.

Installation
------------
1. Import the connector package `API Connector Proxmox.tgz` in FortiSOAR.
2. Configure the `proxmox-api` connector with the correct **host**, **port**, and **API token** (these values are read from the connector configuration, not from global variables).
3. Import this solution pack `solution-pack-proxmox-api-migration.tgz` or `solution-pack-proxmox-api-migration.zip`.
4. (Optional) If you want to override the built‑in defaults for node, storage, network, or templates, create/update the corresponding Proxmox global variables as described in `SCHRITT_2_GLOBAL_VARIABLES.md`.

Upgrade
-------
To upgrade from a previous version of this pack:

1. **Connector**: Ensure you are using the latest `API Connector Proxmox.tgz` shipped with this repo (it contains fixes for DELETE, container features, etc.).
2. **Pack import**: Import the updated `solution-pack-proxmox-api-migration.zip` (or `.tgz`) into FortiSOAR. Existing data in `v_m_instances` and `network_interfaces` is preserved.
3. **Global variables** (optional): After import, you can review the Proxmox global variables and adjust them if you want to override the defaults for node, storage, network, or templates. See `SCHRITT_2_GLOBAL_VARIABLES.md` for details.
4. **Roles / permissions**: Make sure users who should manage VMs have access to the `VM Instances` module and relevant playbooks.

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

Usage
-----
- Use the service management playbooks to request and provision VMs/containers.
- Use the destroy playbooks to remove instances.
- Use the "> Refresh Proxmox Inventory" playbook to sync Proxmox VMs/CTs with the `v_m_instances` module.

Related documentation
---------------------
- `SCHRITT_2_GLOBAL_VARIABLES.md` – Step‑by‑step guide for the Proxmox global variables used by this pack.
- `REFRESH_INVENTORY_PLAYBOOK.md` – Design and behaviour of the "> Refresh Proxmox Inventory" playbook.
- `TOKEN_CAPABILITIES.md` – Overview of the Proxmox API token role and which connector operations it enables.
- `PROXMOX_9.1.5_SPECIFIC_NOTES.md` – Proxmox 9.1.5 specifics relevant for this integration.
- `TESTING_GUIDE.md` – Suggested test plan before rolling out this pack.
- `TROUBLESHOOTING_GUIDE.md` – Troubleshooting checklist for common provisioning/destroy issues.
