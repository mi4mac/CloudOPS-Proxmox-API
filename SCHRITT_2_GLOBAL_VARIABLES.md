# Step 2: Global Variables in FortiSOAR

## Overview

The Proxmox‑related global variables are **already included in the content pack** (`info.json` + `playbooks/globalVariables.json`) and are usually created automatically when you **import the pack** into FortiSOAR.

- **If they already exist after pack import:**  
  Just verify that `proxmox_api_token` is encrypted and adjust the values (host, token, templates, etc.) for your environment.
- **If they were not created automatically:**  
  Create them manually as described below.

**Estimated effort:** 15–20 minutes

---

## Step‑by‑step guide

### 1. Open FortiSOAR

1. Log in to FortiSOAR.
2. Navigate to **Settings → Global Variables**.

### 2. Create the global variables

Create the following global variables **in this order**.

#### 2.1 Proxmox API host

- **Name:** `proxmox_api_host`  
- **Value:** `192.168.222.222`  
- **Default Value:** `192.168.222.222`  
- **Type:** String  
- **Encrypted:** ❌ No  
- **Description:** Proxmox server IP address or hostname  

#### 2.2 Proxmox API port

- **Name:** `proxmox_api_port`  
- **Value:** `8006`  
- **Default Value:** `8006`  
- **Type:** String  
- **Encrypted:** ❌ No  
- **Description:** Proxmox API port (default: 8006)

#### 2.3 Proxmox API token ⚠️ **IMPORTANT: Must be stored encrypted**

- **Name:** `proxmox_api_token`  
- **Value:** `user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>`  
- **Default Value:** `user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>`  
- **Type:** String  
- **Encrypted:** ✅ **YES – MUST be encrypted**  
- **Description:** Proxmox API token used for authentication

**⚠️ Security note:**
- Make sure **Encrypted** is enabled.
- The token is sensitive and must never be stored in clear text.

#### 2.4 Proxmox node name

- **Name:** `proxmox_node_name`  
- **Value:** `pve`  
- **Default Value:** `pve`  
- **Type:** String  
- **Encrypted:** ❌ No  
- **Description:** Name of the Proxmox node (default: `pve`)

#### 2.5 Proxmox storage

- **Name:** `proxmox_storage`  
- **Value:** `local-lvm`  
- **Default Value:** `local-lvm`  
- **Type:** String  
- **Encrypted:** ❌ No  
- **Description:** Storage ID for VM/container disks

#### 2.6 Proxmox bridge

- **Name:** `proxmox_bridge`  
- **Value:** `vmbr0`  
- **Default Value:** `vmbr0`  
- **Type:** String  
- **Encrypted:** ❌ No  
- **Description:** Network bridge for VMs/containers

#### 2.7 Proxmox VLAN tag

- **Name:** `proxmox_vlan_tag`  
- **Value:** `255`  
- **Default Value:** `255`  
- **Type:** String  
- **Encrypted:** ❌ No  
- **Description:** VLAN tag for network interfaces

#### 2.8 Proxmox gateway

- **Name:** `proxmox_gateway`  
- **Value:** `10.255.255.1`  
- **Default Value:** `10.255.255.1`  
- **Type:** String  
- **Encrypted:** ❌ No  
- **Description:** Default gateway for VMs/containers

#### 2.9 Proxmox template: Rocky 9 VM

- **Name:** `proxmox_template_rocky9_vm`  
- **Value:** `9000`  
- **Default Value:** `9000`  
- **Type:** String  
- **Encrypted:** ❌ No  
- **Description:** VMID of the Rocky 9 VM template

#### 2.10 Proxmox template: Ubuntu 22.04 CT

- **Name:** `proxmox_template_ubuntu2204_ct`  
- **Value:** `local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst`  
- **Default Value:** `local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst`  
- **Type:** String  
- **Encrypted:** ❌ No  
- **Description:** Template path for the Ubuntu 22.04 container

#### 2.11 Proxmox template: Debian 13 CT

- **Name:** `proxmox_template_debian13_ct`  
- **Value:** `local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst`  
- **Default Value:** `local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst`  
- **Type:** String  
- **Encrypted:** ❌ No  
- **Description:** Template path for the Debian 13 container

#### 2.12 Proxmox template: Rocky Linux 9 CT

- **Name:** `proxmox_template_rockylinux9_ct`  
- **Value:** `local:vztmpl/rockylinux-9-default_20240912_amd64.tar.xz`  
- **Default Value:** `local:vztmpl/rockylinux-9-default_20240912_amd64.tar.xz`  
- **Type:** String  
- **Encrypted:** ❌ No  
- **Description:** Template path for the Rocky Linux 9 container

---

## Verification (optional but recommended)

After creating the variables (if you decide to use them):

1. **Check the list**
   - Go to **Settings → Global Variables**.
   - Make sure all 12 variables are present.

2. **Check encryption**
   - Open `proxmox_api_token`.
   - Verify that **Encrypted** is enabled.
   - The value should not be visible in clear text.

3. **Test the variables**
   - Create a simple test playbook with a **Configuration** step.
   - Use for example: `{{globalVars.proxmox_api_host}}`.
   - Run the playbook and verify that the value is rendered correctly.

---

## Using the variables in playbooks (optional overrides)

You can access the variables in playbooks like this:

```jinja
# API host and port
{{globalVars.proxmox_api_host}}
{{globalVars.proxmox_api_port or 8006}}

# API token (for Authorization header)
{{globalVars.proxmox_api_token}}

# Node and storage (all have safe in-playbook defaults)
{{globalVars.proxmox_node_name or 'pve'}}           {# default node if unset #}
{{globalVars.proxmox_storage | default('local-lvm')}} {# default storage if unset #}

# Network configuration (all have safe in-playbook defaults)
{{globalVars.proxmox_bridge | default('vmbr0')}}
{{globalVars.proxmox_vlan_tag | default('255')}}
{{globalVars.proxmox_gateway  | default('10.255.255.1')}}

# Templates (all have safe in-playbook defaults)
{{globalVars.proxmox_template_rocky9_vm        | default(9000)}}
{{globalVars.proxmox_template_ubuntu2204_ct    | default('local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst')}}
{{globalVars.proxmox_template_debian13_ct      | default('local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst')}}
{{globalVars.proxmox_template_rockylinux9_ct   | default('local:vztmpl/rockylinux-9-default_20240912_amd64.tar.xz')}}
```

---

## Default values for VM requests

The **Request VM Instance** form and the **Provision** playbook use the following defaults when the requester leaves the fields empty:

| Field       | Default value | Description          |
|------------|---------------|----------------------|
| CPU Cores  | 1             | Number of vCPUs      |
| Memory (MB)| 2048          | RAM in MB            |
| Disk (GB)  | 5             | Disk capacity        |
| Swap (MB)  | 512           | Swap size            |

The success email after provisioning uses the subject **“VM Instance Request Provisioning Success”**.

---

## Proxmox clusters / multiple servers

Each VM instance record has an additional field `proxmoxCluster`. Typical values:

- `lab` – lab / test cluster  
- `prod` – production cluster  

This field is a **logical label** that indicates which Proxmox cluster a VM instance belongs to. The actual mapping from `proxmoxCluster` to a specific `proxmox-api` connector configuration (host/token) is handled in FortiSOAR, for example by using separate playbooks per cluster.

**Recommendation:**

- Create a separate connector configuration for each Proxmox server (for example, `proxmox-lab`, `proxmox-prod`, …).
- In FortiSOAR, clone the provision/destroy playbooks per cluster and point each version to the appropriate connector configuration.

This way you can operate multiple Proxmox servers with the same data model, without hard‑wiring this pack to a single server.

---

## Troubleshooting

### Problem: Variable cannot be found

**Solution:**
- Double‑check the exact spelling (including case).
- Use `{{globalVars.variable_name}}` (note the plural `globalVars`).
- Ensure the variable has been saved.

### Problem: Token is shown in clear text

**Solution:**
- Open the `proxmox_api_token` variable.
- Enable **Encrypted**.
- Save the variable again; the value should now be hidden/obfuscated.

### Problem: Wrong value

**Solution:**
- Check the values documented in your step‑1 environment notes (for example `SCHRITT_1_ABGESCHLOSSEN.md` if present).
- Compare with values in any helper scripts (for example `scripts/*.sh`).
- Update the variable with the correct value.

---

## Installation via the pack

The variables are defined in the pack (`info.json`, `playbooks/globalVariables.json`) and are normally created automatically when you **import the content pack** into FortiSOAR. For details, see `GLOBAL_VARIABLES_PACK_INSTALL.md` (if present).

After importing the pack:

1. Go to **Settings → Global Variables**.
2. Ensure `proxmox_api_token` is set to **Encrypted**.
3. Adjust all values to match your environment.

---

## Next steps

After creating and/or verifying the global variables:

**Step 3: Configure the HTTP connector**
- See `SCHRITT_3_HTTP_CONNECTOR.md` (or the equivalent HTTP connector guide in this repo).

---

*Created: 2026‑02‑20*  
*Version: 1.2*  
*Status: Step 2 – Global Variables (with pack install)*
