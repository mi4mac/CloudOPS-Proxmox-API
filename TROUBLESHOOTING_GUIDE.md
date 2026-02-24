# Troubleshooting Guide: Proxmox API Integration

## Overview

This guide helps you troubleshoot issues with the Proxmox API integration in FortiSOAR.

---

## Errors in VM Instance Logs (Provision / Destroy)

When a provision or destroy run fails, the connector’s error message (for example a Proxmox API error) is written into the **Logs** field of the VM Instance record:

- **Provision:** On error, **Set Provision Failure Result** runs (it reads the error from Get Next VMID, Create Container, Start Container, Clone VM, Config VM, or Start VM). Then **Update VM Instance Failure** writes `cmd_result` into the Logs. On success, **Set Provision Result (CT/VM)** goes directly to **Update VM Instance Success** (status “Active”, Proxmox ID and Logs).
- **Destroy:** Similarly, **Set Destroy Failure Result** (errors from Stop/Destroy VM or container) and **Update Failed Destroyed VM**.

This way you can see the exact Proxmox or connector error directly on the VM Instance record (for example `API error 403: Permission check failed …`). In addition, the playbook execution view contains detailed step logs for each connector step.

---

## Nesting / Features for LXC Containers

**Symptom:** Provisioning completes, but the container does not have `nesting=1` (for example needed for Docker inside a CT). Or you see “Unknown operation: config_container” because the installed connector version does not include the `config_container` operation.

**Background:** For **Create Container**, the connector first calls the create API and then, in the same call, uses the config API to set `features: nesting=1` (same behavior as the earlier scripts). No separate playbook step is required.

**UX note:** In the VM Instance detail view, **Proxmox ID** and **Status** are displayed at the top of the form; the “Proxmox ID” field tooltip contains the nesting command. In the list view, Proxmox ID and Status are also displayed. The **Destroy VM Instance** action is available as a button in the detail view.

**Workaround (without config_container):** Set nesting manually after creation. On the Proxmox node (VMID from the FortiSOAR record, for example `proxmoxId`):

```bash
# Container must be stopped
pct stop <VMID>
pct set <VMID> -features nesting=1
pct start <VMID>
```

**If nesting is still missing:** Re‑import the connector package from this repo – the Create Container call will automatically set nesting via the config API after creation.

---

## Common Issues

### 1. API Connection Errors

#### Problem: "Connection refused" or "Cannot connect"

**Symptoms:**
- HTTP connector cannot connect.
- Timeout errors.
- “Connection refused” errors.

**Possible causes:**
- Incorrect host address.
- Incorrect port.
- Firewall is blocking the connection.
- Proxmox server is not reachable.

**Resolution:**

1. Check the global variable `proxmox_api_host`:

   ```jinja
   {{globalVars.proxmox_api_host}}
   ```

   Expected: `192.168.222.222`

2. Check the global variable `proxmox_api_port`:

   ```jinja
   {{globalVars.proxmox_api_port}}
   ```

   Expected: `8006`

3. Manually test connectivity:

   ```bash
   curl -k https://192.168.222.222:8006/api2/json/version
   ```

4. Check the firewall:

   ```bash
   # On the Proxmox server
   iptables -L -n | grep 8006
   ```

5. Check whether the Proxmox API is running:

   ```bash
   # On the Proxmox server
   systemctl status pveproxy
   ```

---

### 2. Authentication Errors

#### Problem: "401 Unauthorized" or "Permission check failed"

**Symptoms:**
- API calls return HTTP 401.
- “Permission check failed” errors.
- “Authentication failed” errors.

**Possible causes:**
- Wrong API token.
- Token is not passed correctly in the header.
- Token expired or invalid.
- Missing permissions.

**Resolution:**

1. Check the global variable `proxmox_api_token`:

   ```jinja
   {{globalVars.proxmox_api_token}}
   ```

   Expected format: `user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>`

2. Check the Authorization header in the connector:
   - Should be: `PVEAPIToken={{globalVars.proxmox_api_token}}`
   - No additional spaces or line breaks.

3. Manually test the token:

   ```bash
   curl -k -H "Authorization: PVEAPIToken=user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>" \
     https://192.168.222.222:8006/api2/json/version
   ```

4. Check token permissions:

   ```bash
   # On the Proxmox server
   pveum user token show fortisoar@pve fortisoar-token
   ```

5. Check ACLs:

   ```bash
   # On the Proxmox server (Proxmox 8.x: "list" instead of "show")
   pveum acl list
   ```

#### Problem: "Permission check failed (/storage/local, Datastore.AllocateSpace|Datastore.Audit)" during CT provisioning

**Symptoms:**
- Create Container (API) fails with HTTP 403.
- Error message explicitly mentions `/storage/local` and `Datastore.AllocateSpace|Datastore.Audit`.

**Background:** LXC templates are often stored on `local` (for example `local:vztmpl/...`). When creating the container, Proxmox checks the API token’s permissions for this path. In some Proxmox versions, the standard role **PVEVMAdmin** is not sufficient for tokens; the custom role **FortiSOAR-Role** explicitly includes `Datastore.AllocateSpace` and `Datastore.Audit` (see `TOKEN_CAPABILITIES.md`).

**Resolution:** On the Proxmox node, also assign **FortiSOAR-Role** for `/storage/local` (quote the token because of the `!`):

```bash
# For the user
pveum acl modify /storage/local -user fortisoar@pve -role FortiSOAR-Role

# For the API token (quotes are important because of "!")
pveum acl modify /storage/local -token 'fortisoar@pve!fortisoar-token' -role FortiSOAR-Role
```

Verify:

```bash
pveum acl list | grep '/storage/local'
# Optional: show token permissions (depending on Proxmox version)
pveum user token permissions fortisoar@pve fortisoar-token
```

Then run the provisioning playbook again.

---

### 3. Multiple Proxmox Servers / Clusters

#### Problem: VMs are spread across multiple Proxmox servers, but FortiSOAR should manage all of them

**Background:**

- The native Python connector `proxmox-api` supports multiple **connector configurations** (per server/cluster).
- This pack uses a fixed connector configuration per playbook. A single playbook run therefore cannot dynamically switch between multiple Proxmox configurations.
- The data model has an additional field `proxmoxCluster` that logically labels which cluster/connector a VM belongs to (for example `lab`, `prod`).

**Recommended approach:**

1. **Create one `proxmox-api` configuration per Proxmox server**, for example:
   - `proxmox-lab` (host/token for lab)
   - `proxmox-prod` (host/token for prod)

2. **Clone playbooks per cluster** (in FortiSOAR):
   - `> Provision VM Instances (lab)` → connector configuration: `proxmox-lab`
   - `> Provision VM Instances (prod)` → connector configuration: `proxmox-prod`
   - Same pattern for `> Destroy VM Instance`, `Destroy Expired VM Instances`, etc.

3. **Set `proxmoxCluster` in the request form**:
   - End users select for example `lab` or `prod`.
   - Depending on the value, the appropriate (lab/prod) playbook is started in FortiSOAR.

This allows you to use the same pack and data model across multiple Proxmox servers without a single playbook having to dynamically switch connector configurations.

---

### 4. SSL Certificate Errors

#### Problem: "SSL certificate verification failed"

**Symptoms:**
- SSL certificate errors.
- “Certificate verify failed” errors.

**Possible causes:**
- Self‑signed certificate.
- Certificate expired.
- Hostname mismatch.

**Resolution:**

1. **For testing:** Set `Verify SSL` to `false` in the HTTP connector.

2. **For production:** Import the Proxmox certificate:

   ```bash
   # Fetch certificate from the Proxmox server
   openssl s_client -showcerts -connect 192.168.222.222:8006 </dev/null 2>/dev/null | \
     openssl x509 -outform PEM > proxmox-cert.pem
   ```

   Then import it into FortiSOAR (steps depend on the FortiSOAR version).

3. Alternatively, use the IP address instead of the hostname.

---

### 5. Global Variable Not Found

#### Problem: "Global Variable not found" or variable is empty

**Symptoms:**
- Variable cannot be found.
- Variable is empty.
- Jinja2 errors.

**Possible causes:**
- Variable not created.
- Variable name is wrong.
- Jinja2 syntax is incorrect.

**Resolution:**

1. Check whether the variable exists:
   - FortiSOAR → Settings → Global Variables.
   - Search for `proxmox_api_host`.

2. Check the syntax:

   ```jinja
   {{globalVars.proxmox_api_host}}  ✅ Correct
   {{globalvars.proxmox_api_host}}  ❌ Wrong (lowercase)
   {{globalVars.proxmox_api_host }} ❌ Wrong (trailing space)
   ```

3. Check case sensitivity:
   - `globalVars` (capital `V`).
   - Variable names are case‑sensitive.

4. Test the variable in a test playbook:

   ```jinja
   test_value: "{{globalVars.proxmox_api_host}}"
   ```

---

### 6. Container / VM Is Not Created

#### Problem: Container/VM is not created, but there is no error

**Symptoms:**
- Playbook completes without errors.
- Container/VM does not exist on Proxmox.
- Status stays “Pending”.

**Possible causes:**
- API call fails but the error isn’t handled.
- Wrong parameters.
- Template not available.

**Resolution:**

1. Check the playbook logs:
   - Open the playbook execution.
   - Inspect the logs for each step.

2. Check the API response:

   ```jinja
   {{vars.steps.Create_Container.data}}
   {{vars.steps.Create_Container.error}}
   ```

3. Check parameters:
   - VMID correct?
   - Template available?
   - Storage available?

4. Check Proxmox logs:

   ```bash
   # On the Proxmox server
   journalctl -u pve-cluster -f
   ```

---

### 7. Container / VM Is Not Deleted

#### Problem: Destroy fails

**Symptoms:**
- Destroy playbook fails.
- Container/VM still exists on Proxmox.
- Status remains “Active”.

**Possible causes:**
- Container/VM already deleted.
- Permission issue.
- Container/VM is still running.

**Resolution:**

1. Check whether the container/VM still exists:

   ```bash
   # Container
   pct list | grep <CTID>

   # VM
   qm list | grep <VMID>
   ```

2. Check the API response:

   ```jinja
   {{vars.steps.Destroy_Container.data}}
   {{vars.steps.Destroy_Container.error}}
   {{vars.steps.Destroy_Container.data.message}}
   ```

3. Check whether container/VM is stopped:

   ```bash
   # Container
   pct status <CTID>

   # VM
   qm status <VMID>
   ```

4. Manually stop if needed:

   ```bash
   # Container
   pct stop <CTID>

   # VM
   qm stop <VMID>
   ```

---

### 8. Stop Error When VM / Container Is Already Stopped

#### Problem: Stop fails even though the VM/container is already stopped

**Symptoms:**
- Stop step fails.
- Error message: “VM/Container already stopped”.
- Playbook run stops.

**Resolution:**

1. **Option 1:** Handle this case in the playbook:

   ```jinja
   {%- if vars.steps.Stop_Container.error -%}
     {# Check if the container is already stopped #}
     {%- set stop_success = true -%}
   {%- else -%}
     {%- set stop_success = true -%}
   {%- endif -%}
   ```

2. **Option 2:** Check status before stopping (optional):
   - GET `/api2/json/nodes/{node}/lxc/{vmid}/status/current`
   - Only stop if status is not `stopped`.

---

### 9. Content‑Type Errors

#### Problem: "400 Bad Request" on POST requests

**Symptoms:**
- POST requests fail.
- “Invalid parameter” errors.
- “Content‑Type” errors.

**Possible causes:**
- Wrong Content‑Type.
- Body not correctly formatted.

**Resolution:**

1. Check the Content‑Type:
   - Should be: `application/x-www-form-urlencoded`.
   - Not: `application/json`.

2. Check body formatting:

   ```text
   param1=value1&param2=value2&param3=value3
   ```

   - URL‑encoded.
   - `&` as a separator.
   - No spaces.

3. Example for Create Container:

   ```text
   vmid=100&hostname=test&ostemplate=local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst&cores=2&memory=2048&rootfs=local-lvm:20&net0=name=eth0,bridge=vmbr0,tag=255,ip=10.255.255.100/24,gw=10.255.255.1&nameserver=1.1.1.1&password=fortinet&swap=0&features=nesting=1
   ```

---

## Debugging Tips

### 1. Check Playbook Logs

**Location:** FortiSOAR → Playbooks → [Playbook name] → Execution History.

**What to check:**
- Which step is failing?
- What is the error message?
- What is the API response?

### 2. Log API Responses

**In playbook steps:**

```jinja
debug_response: "{{vars.steps.Create_Container.data | tojson}}"
debug_error: "{{vars.steps.Create_Container.error}}"
```

### 3. Manual API Tests

**Using curl:**

```bash
# Get version
curl -k -H "Authorization: PVEAPIToken=user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>" \
  https://192.168.222.222:8006/api2/json/version

# Get next VMID
curl -k -H "Authorization: PVEAPIToken=user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>" \
  https://192.168.222.222:8006/api2/json/cluster/nextid
```

### 4. Check Proxmox Logs

**On the Proxmox server:**

```bash
# Cluster logs
journalctl -u pve-cluster -f

# API access logs
tail -f /var/log/pveproxy/access.log

# System logs
journalctl -f
```

---

## Support & References

### Proxmox documentation

- API documentation: https://pve.proxmox.com/pve-docs/api-viewer/
- Forum: https://forum.proxmox.com/

### FortiSOAR documentation

- FortiSOAR playbook documentation.
- FortiSOAR connector documentation.

---

## Refresh Status from Proxmox

**Symptom:** The VM Instance shows status “Failed”, even though the VM/container is running on Proxmox.

**Resolution:** Run the **“> Refresh Status from Proxmox”** playbook (via **Execute → Refresh Status** on the VM Instance record). The playbook retrieves the current status from Proxmox (running/stopped) and updates the record (for example, sets status to “Active” and adds a log entry `Refreshed from Proxmox: running`). Prerequisite: the **Proxmox ID** field is populated.

---

## What’s New / Changelog

- **Refresh Status:** New playbook **“> Refresh Status from Proxmox”** (Execute → Refresh Status on VM Instance) synchronizes status with Proxmox.
- **Default VM request values:** In the request form and provisioning flow, the following defaults apply when users do not provide values: **CPU 1**, **Disk 5 GB**, **Swap 512 MB**, **Memory 2048 MB**.
- **Success email:** The success notification after provisioning now uses the subject **“VM Instance Request Provisioning Success”** (previously it incorrectly used “Provisioning Failure”). The failure email keeps the subject “VM Instance Request Provisioning Failure”.

---

*Created: 2026‑02‑20*  
*Version: 1.1*  
*Status: Troubleshooting Guide*

