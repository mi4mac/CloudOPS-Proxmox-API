# Implementation Checklist: SSH → Proxmox API Migration

## Overview

This checklist walks you step by step through migrating from SSH‑based scripts to the Proxmox REST API in FortiSOAR.

**Estimated total effort:** 10–15 hours

---

## Phase 1: Setup & configuration (2–3 hours)

### ✅ Step 1: Proxmox API token setup
- [x] Proxmox user and role for FortiSOAR created  
- [x] API token created  
- [x] Token tested using `curl`  
- [x] Token value stored securely (for example in a password manager)  

**Status:** ✅ Completed  
**Reference:** `SCHRITT_2_GLOBAL_VARIABLES.md` and `TOKEN_CAPABILITIES.md`

---

### ⏳ Step 2: Create global variables in FortiSOAR

**Location:** FortiSOAR → Settings → Global Variables

**Variables to create (12):**

#### API configuration
- [ ] `proxmox_api_host` (e.g. `192.168.222.222`)
- [ ] `proxmox_api_port` (e.g. `8006`)
- [ ] `proxmox_api_token` = `user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>` ⚠️ **ENCRYPTED**

#### Proxmox configuration
- [ ] `proxmox_node_name` (e.g. `pve`)
- [ ] `proxmox_storage` (e.g. `local-lvm`)
- [ ] `proxmox_bridge` (e.g. `vmbr0`)
- [ ] `proxmox_vlan_tag`
- [ ] `proxmox_gateway`

#### Templates
- [ ] `proxmox_template_rocky9_vm`
- [ ] `proxmox_template_ubuntu2204_ct`
- [ ] `proxmox_template_debian13_ct`
- [ ] `proxmox_template_rockylinux9_ct`

**Validation**
- [ ] All 12 variables exist  
- [ ] `proxmox_api_token` is stored as encrypted  
- [ ] A small test playbook can read all variables

**Reference:** `SCHRITT_2_GLOBAL_VARIABLES.md`

---

### ⏳ Step 3: Configure `proxmox-api` connector

You normally install and configure the **native** `proxmox-api` connector shipped with this repo (see `CONNECTOR_KONFIGURATION.md`).  
If you still use an HTTP connector, the settings below are a reference.

**Location:** FortiSOAR → Connectors

**Configuration**
- [ ] Connector `proxmox-api` imported from `API Connector Proxmox.tgz`
- [ ] Host and port set according to the global variables
- [ ] Token configured using the `PVEAPIToken` scheme

**Validation**
- [ ] Test operation `get_version` succeeds  
- [ ] Cluster `nextid` can be fetched  
- [ ] Basic VM/CT lists can be retrieved

**Reference:** `CONNECTOR_KONFIGURATION.md`

---

## Phase 2: Provision playbook migration (4–6 hours)

### ⏳ Step 4: Migrate `> Provision VM Instances`

**Location:** FortiSOAR → Playbooks → `> Provision VM Instances`

High‑level goals:
- Replace SSH‑based provisioning with Proxmox API operations via `proxmox-api`.  
- Derive VMID via `get_next_vmid`.  
- Use different flows for CT vs VM.  
- Persist `proxmoxId` and logs on the `v_m_instances` record.

Key tasks:
- [ ] Ensure configuration steps exist (determine VM type, choose template, compute resources).  
- [ ] Ensure connector steps exist (get next VMID, create CT, clone VM, configure VM, start CT/VM).  
- [ ] Make sure all connector steps point to the correct `proxmox-api` configuration.  
- [ ] Update logic that extracts and stores `proxmoxId` (use the VMID from API, not regex over SSH output).  
- [ ] Make success/failure routes consistent with the updated `Provision` playbook shipped with this repo.

**Validation**
- [ ] CT provisioning works for all supported templates.  
- [ ] VM provisioning works for the Rocky9 template.  
- [ ] `proxmoxId` is stored and the record status is set to *Active* on success.  
- [ ] Logs show the Proxmox task results.

**Reference:** `playbooks/00 - Service Management/> Provision VM Instances.json`

---

## Phase 3: Destroy playbook migration (2–3 hours)

### ⏳ Step 5: Migrate `> Destroy VM Instance`

**Location:** FortiSOAR → Playbooks → `> Destroy VM Instance`

High‑level goals:
- Use Proxmox API to stop and destroy CT/VM.  
- Route correctly depending on VM vs CT.  
- Keep the safety checks around `deleteAfter` and manual approval.  
- Update record status and logs correctly.

Key tasks:
- [ ] Make sure there is a step that decides CT vs VM type.  
- [ ] Ensure connector steps exist to stop and destroy containers and VMs.  
- [ ] Route CT and VM paths to the correct steps.  
- [ ] Remove dependencies on SSH `cmd_result` strings.  
- [ ] Make the "Destroyed successfully" condition depend on Proxmox task results instead of simple string checks.

**Validation**
- [ ] CTs and VMs created during testing can be destroyed cleanly.  
- [ ] Records move to the *Destroyed* state.  
- [ ] Logs clearly show the destroy operations and results.  

**Reference:** `playbooks/00 - Service Management/> Destroy VM Instance.json`

---

## Phase 4: Testing & validation (3–4 hours)

### ⏳ Step 6: Run comprehensive tests

Recommended scenarios (see `TESTING_GUIDE.md` for details):

#### Container provisioning
- [ ] Provision Ubuntu 22.04 CT and verify running status + `proxmoxId`.  
- [ ] Provision Debian 13 CT and verify running status + `proxmoxId`.  
- [ ] Provision Rocky Linux 9 CT and verify running status + `proxmoxId`.  

#### VM provisioning
- [ ] Provision Rocky 9 VM and verify it is cloned, configured, running and has `proxmoxId`.  

#### Container destruction
- [ ] Destroy all test CTs via `> Destroy VM Instance`.  
- [ ] Confirm CTs are stopped and deleted in Proxmox and marked *Destroyed* in FortiSOAR.  

#### VM destruction
- [ ] Destroy the test VM and confirm it is purged and marked *Destroyed*.  

#### Error handling & edge cases
- [ ] Invalid parameters (VMID/template) are handled gracefully.  
- [ ] Destroying already stopped CT/VM works (stop errors ignored, destroy still succeeds).  
- [ ] Manual approval kicks in when `deleteAfter` is missing or not expired.  
- [ ] API connection errors surface clearly in logs.

---

## Phase 5: Finalization (1–2 hours)

### ⏳ Step 7: Cleanup & documentation

Optional cleanup (after you are confident with the API‑based flow):
- [ ] Remove any remaining SSH‑only provisioning or deprovisioning steps.  
- [ ] Remove obsolete testing playbooks that used the old connector design.

Documentation:
- [ ] Update `README.md` with the final architecture and usage notes.  
- [ ] Keep `TROUBLESHOOTING_GUIDE.md` in sync with current behaviour.  
- [ ] Maintain a short changelog in `TROUBLESHOOTING_GUIDE.md` or `PACK_README.md`.

Monitoring:
- [ ] Ensure logging for API calls is enabled.  
- [ ] Configure alerts for repeated failures.  
- [ ] Add simple performance/latency monitoring where helpful.

---

## Summary

### ✅ Completed
- Step 1: Proxmox API token setup.

### ⏳ In progress / ready
- Step 2: Global variables.  
- Step 3: `proxmox-api` connector configuration.  
- Step 4: Provision playbook migration.  
- Step 5: Destroy playbook migration.  
- Step 6: Testing & validation.  
- Step 7: Cleanup & documentation.

---

## Notes

### Connector configuration
Record the connector configuration ID (if applicable) and keep it documented alongside this checklist so future environments can be configured faster.

### Test VMs/containers
Keep a short list of test CTs/VMs you regularly use for validation so that repeat runs stay predictable and comparable.

---

*Created: 2026‑02‑20*  
*Version: 1.1 (English migration)*  
*Status: Implementation checklist*
