# Testing Guide: Proxmox API Migration

## Overview

This guide describes detailed test scenarios for the Proxmox API migration in FortiSOAR.

**Purpose:** Ensure that all functions have been migrated correctly and that the API integration works without errors.

---

## Preparation

### Prepare the test environment

1. **Proxmox server**
   - [ ] Proxmox server is reachable.
   - [ ] API token works.
   - [ ] Templates available:
     - [ ] Rocky9 VM template (VMID: 9000)
     - [ ] Ubuntu2204 CT template
     - [ ] Debian13 CT template
     - [ ] RockyLinux9 CT template

2. **FortiSOAR**
   - [ ] Global variables created.
   - [ ] HTTP connector configured.
   - [ ] Provision playbook migrated.
   - [ ] Destroy playbook migrated.

3. **Test data**
   - [ ] Test user created.
   - [ ] Test department created.
   - [ ] IP addresses available (10.255.255.x).

---

## Test Scenarios

### 1. Container creation: Ubuntu2204 CT

**Goal:** Test container creation via the API.

**Steps:**

1. Create a VM Instance request:
   - Name: `test-ubuntu2204-ct-01`
   - VM Type: `ubuntu2204-ct`
   - CPU Cores: `2`
   - Memory: `2048 MB`
   - Disk: `20 GB`
   - IP Address: `10.255.255.130`
   - Root Password: `fortinet`

2. Run the Provision playbook.

3. **Expected results:**
   - ✅ Container is created.
   - ✅ Container is started.
   - ✅ Proxmox ID is stored.
   - ✅ Status: `Active`.
   - ✅ Logs contain a success message.

4. **Verification on Proxmox:**

   ```bash
   pct list | grep test-ubuntu2204-ct-01
   pct status <CTID>
   ```

**Success criteria:**

- Container exists on Proxmox.
- Container is running (`status: running`).
- Container has the correct configuration (CPU, memory, disk, IP).

---

### 2. Container creation: Debian13 CT

**Goal:** Test Debian13 CT creation.

**Steps:**

1. Create a VM Instance request:
   - Name: `test-debian13-ct-01`
   - VM Type: `debian13-ct`
   - CPU Cores: `2`
   - Memory: `2048 MB`
   - Disk: `20 GB`
   - IP Address: `10.255.255.131`

2. Run the Provision playbook.

3. **Expected results:** Same as in test 1.

4. **Verification:** Same as in test 1.

---

### 3. Container creation: RockyLinux9 CT

**Goal:** Test RockyLinux9 CT creation.

**Steps:**

1. Create a VM Instance request:
   - Name: `test-rockylinux9-ct-01`
   - VM Type: `rockylinux9-ct`
   - CPU Cores: `2`
   - Memory: `2048 MB`
   - Disk: `20 GB`
   - IP Address: `10.255.255.132`

2. Run the Provision playbook.

3. **Expected results:** Same as in test 1.

4. **Verification:** Same as in test 1.

---

### 4. VM creation: Rocky9 VM

**Goal:** Test VM creation via the API (including clone).

**Steps:**

1. Create a VM Instance request:
   - Name: `test-rocky9-vm-01`
   - VM Type: `rocky9-vm`
   - CPU Cores: `2`
   - Memory: `2048 MB`
   - Disk: `20 GB`
   - IP Address: `10.255.255.133`

2. Run the Provision playbook.

3. **Expected results:**
   - ✅ VM template is cloned.
   - ✅ VM is configured.
   - ✅ VM is started.
   - ✅ Proxmox ID is stored.
   - ✅ Status: `Active`.
   - ✅ Logs contain a success message.

4. **Verification on Proxmox:**

   ```bash
   qm list | grep test-rocky9-vm-01
   qm status <VMID>
   qm config <VMID>
   ```

**Success criteria:**

- VM exists on Proxmox.
- VM is running (`status: running`).
- VM has the correct configuration (CPU, memory, disk, IP, network).

---

### 5. Refresh Status from Proxmox (CT/VM)

**Goal:** Ensure that the `> Refresh Status from Proxmox` playbook reads the runtime status from Proxmox and updates the VM Instance logs correctly **without** overwriting the `Status` field.

**Steps:**

1. Choose an existing VM Instance that was provisioned successfully (for example `test-debian13-ct-01` or `test-rocky9-vm-01`).  
   - The **Proxmox ID** field must be set (for example `118`).  
   - The instance should be **running** on Proxmox (`status: running`).

2. Open the record in the detail view (`VM Instances` → click on the name).
3. Click **`Refresh Status from Proxmox`** at the bottom.

**Expected results:**

- ✅ Playbook run finishes with status `finished` (no errors in the run log).  
- ✅ A new entry appears in the VM Instance **Logs** field:

  - On success:

    ```html
    Refreshed from Proxmox: running
    ```

  - On error (for example permissions or API issues):

    ```html
    Refresh failed: <specific error message from Proxmox/connector>
    ```

- ✅ The **Status** field (VM Status picklist) remains **unchanged**. Refresh updates only the logs, not the status field.

**Verification on Proxmox:**

```bash
# For containers
pct status <CTID>

# For VMs
qm status <VMID>
```

**Success criteria:**

- Proxmox reports `status: running` (or the expected state).  
- The log message in FortiSOAR reflects the correct Proxmox status.  
- No unexpected changes to the Status field (for example no change to `Failed` just from a refresh).

---

### 6. Container deletion: Ubuntu2204 CT

**Goal:** Test container deletion via the API.

**Steps:**

1. Create the container (see test 1).
2. Run the Destroy playbook.

3. **Expected results:**
   - ✅ Container is stopped.
   - ✅ Container is deleted.
   - ✅ Status: `Destroyed`.
   - ✅ Logs contain a success message.

4. **Verification on Proxmox:**

   ```bash
   pct list | grep test-ubuntu2204-ct-01
   # Should return nothing
   ```

**Success criteria:**

- Container no longer exists on Proxmox.
- Container disks are removed.
- Status in FortiSOAR: `Destroyed`.

---

### 7. VM deletion: Rocky9 VM

**Goal:** Test VM deletion via the API (with `purge`).

**Steps:**

1. Create the VM (see test 4).
2. Run the Destroy playbook.

3. **Expected results:**
   - ✅ VM is stopped.
   - ✅ VM is deleted (with `purge`).
   - ✅ VM disks are removed.
   - ✅ Status: `Destroyed`.
   - ✅ Logs contain a success message.

4. **Verification on Proxmox:**

   ```bash
   qm list | grep test-rocky9-vm-01
   # Should return nothing
   ```

**Success criteria:**

- VM no longer exists on Proxmox.
- VM disks are deleted (purged).
- Status in FortiSOAR: `Destroyed`.

---

### 8. Error Handling: Invalid Parameters

**Goal:** Test error handling for invalid parameters.

**Test 8.1: Invalid VMID**
- [ ] Run the Destroy playbook with an invalid Proxmox ID.
- [ ] Expected: Error is handled correctly.
- [ ] Expected status: `Failed`.
- [ ] Logs contain the error message.

**Test 8.2: Invalid template**
- [ ] Run the Provision playbook with an invalid template.
- [ ] Expected: Error is handled correctly.
- [ ] Expected status: `Failed`.
- [ ] Logs contain the error message.

**Test 8.3: Insufficient resources**
- [ ] Run the Provision playbook with very large resource values.
- [ ] Expected: Error is handled correctly.
- [ ] Expected status: `Failed`.
- [ ] Logs contain the error message.

---

### 9. Edge Cases

**Test 9.1: Already stopped VM / container**
- [ ] Manually stop the VM/container.
- [ ] Run the Destroy playbook.
- [ ] Expected: Stop error is ignored, destroy still succeeds.

**Test 9.2: Already deleted VM / container**
- [ ] Manually delete the VM/container.
- [ ] Run the Destroy playbook.
- [ ] Expected: Error is handled correctly.

**Test 9.3: VMID conflicts**
- [ ] Try to create a VM with an existing VMID.
- [ ] Expected: Error is handled correctly.

**Test 9.4: API connection errors**
- [ ] Make the Proxmox server temporarily unreachable.
- [ ] Run the Provision/Destroy playbook.
- [ ] Expected: Error is handled correctly.

---

### 10. Manual Approval

**Goal:** Test manual approval for destroy operations.

**Steps:**

1. Create a VM/container **without** `deleteAfter`.
2. Run the Destroy playbook.

3. **Expected results:**
   - ✅ Manual approval dialog is shown.
   - ✅ Approval form shows VM details.
   - ✅ Approval workflow works.
   - ✅ VM/container is deleted after approval.

**Test 10.1: Approval accepted**
- [ ] Approve the request.
- [ ] Expected: VM/container is deleted.

**Test 10.2: Approval rejected**
- [ ] Reject the approval.
- [ ] Expected: Playbook stops.
- [ ] VM/container remains.

---

### 11. Performance Tests

**Goal:** Test performance of the API integration.

**Test 11.1: Parallel creation**
- [ ] Create multiple containers in parallel.
- [ ] Expected: All are created successfully.

**Test 11.2: Sequential operations**
- [ ] Create multiple VMs sequentially.
- [ ] Expected: All are created successfully.

**Test 11.3: Large VMs/containers**
- [ ] Create a VM with large resources (for example 8 CPU, 16 GB RAM, 100 GB disk).
- [ ] Expected: VM is created successfully.

---

## Test Log

### Test execution

**Date:** ___________________  
**Tester:** ___________________  

**Environment:**
- FortiSOAR version: ___________________
- Proxmox version: ___________________
- Connector config ID: ___________________

### Results

| Test # | Scenario                    | Status | Notes |
|--------|-----------------------------|--------|-------|
| 1      | Ubuntu2204 CT creation      | ⬜      |       |
| 2      | Debian13 CT creation        | ⬜      |       |
| 3      | RockyLinux9 CT creation     | ⬜      |       |
| 4      | Rocky9 VM creation          | ⬜      |       |
| 5      | Ubuntu2204 CT deletion      | ⬜      |       |
| 6      | Rocky9 VM deletion          | ⬜      |       |
| 7      | Error handling              | ⬜      |       |
| 8      | Edge cases                  | ⬜      |       |
| 9      | Manual approval             | ⬜      |       |
| 10     | Performance                 | ⬜      |       |

**Legend:**
- ✅ Successful
- ❌ Failed
- ⚠️ Partially successful
- ⬜ Not tested

---

## Known Issues

### Issue 1

**Description:** _________________________________________________  
**Workaround:** _________________________________________________  
**Status:** ⬜ Open / ✅ Fixed

---

## Troubleshooting

### Problem: Container is not created

**Possible causes:**
- Invalid template.
- Insufficient resources.
- API error.

**Resolution:**
1. Check the playbook logs.
2. Check API response: `vars.steps.Create_Container.data`.
3. Check Proxmox logs: `journalctl -u pve-cluster`.

### Problem: VM does not start

**Possible causes:**
- Invalid configuration.
- Network issue.
- Storage problem.

**Resolution:**
1. Check VM configuration: `qm config <VMID>`.
2. Check network configuration.
3. Check storage availability.

### Problem: Destroy fails

**Possible causes:**
- VM/container already deleted.
- Permission issue.
- API error.

**Resolution:**
1. Check whether VM/container still exists.
2. Check API response: `vars.steps.Destroy_VM.data`.
3. Check API token permissions.

---

*Created: 2026‑02‑20*  
*Version: 1.0*  
*Status: Testing Guide*

