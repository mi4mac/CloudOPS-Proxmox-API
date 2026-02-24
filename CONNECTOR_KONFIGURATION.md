# Proxmox API Connector – Configuration Guide

## Overview

This document describes how to configure the legacy **HTTP connector “Proxmox API”** in FortiSOAR.  
It is kept for reference only – for new deployments you should prefer the native Python connector `proxmox-api` that is shipped as `API Connector Proxmox.tgz`.

---

## Basic connector details (HTTP connector)

- **Name:** `Proxmox API`  
- **Description:** `HTTP connector for Proxmox VE API integration – token‑based authentication`  
- **Connector type:** `HTTP`  
- **Version:** `2.1.3`

---

## Connection settings

### Host and port

- **Host:** Proxmox VE hostname or IP, for example:

  ```text
  192.168.222.222
  ```

- **Port:** Proxmox API port (default `8006`)

### Protocol and SSL

- **Protocol:** `HTTPS`  
- **Verify SSL:**
  - `false` for lab / PoC with self‑signed certificates  
  - `true` for production with trusted certificates

### Timeouts and retries

- **Timeout:** `30` seconds  
- **Retry count:** `3`  
- **Connection pool size:** `10`

---

## Authentication

The HTTP connector authenticates to Proxmox VE using a **PVEAPIToken** in a custom `Authorization` header.

### Custom header

- **Header name:** `Authorization`  
- **Header value format:**

  ```text
  PVEAPIToken=<user@realm>!<tokenid>=<token_value>
  ```

- **Example:**

  ```text
  PVEAPIToken=user@pve!token-id=<YOUR_PROXMOX_API_TOKEN_UUID>
  ```

**Recommendations:**

- Store the token in a secret/global variable in FortiSOAR.  
- Do not add extra spaces or line breaks in the header value.  
- Make sure the token has the required privileges (as documented in `TOKEN_CAPABILITIES.md`).

---

## Typical API calls (reference only)

These examples show how the HTTP connector would be used against Proxmox VE.

### Version

- **Method:** `GET`  
- **Path:** `/api2/json/version`

Example response:

```json
{
  "data": {
    "version": "9.1.5",
    "release": "...",
    "repoid": "..."
  }
}
```

### Next VMID

- **Method:** `GET`  
- **Path:** `/api2/json/cluster/nextid`

Example response:

```json
{
  "data": "100"
}
```

### List VMs

- **Method:** `GET`  
- **Path:** `/api2/json/nodes/{node}/qemu`

Example snippet:

```json
{
  "data": [
    {
      "vmid": 100,
      "name": "example-vm",
      "status": "running"
    }
  ]
}
```

### Create a container (LXC)

- **Method:** `POST`  
- **Path:** `/api2/json/nodes/{node}/lxc`  
- **Content‑Type:** `application/x-www-form-urlencoded`

Form body example:

```text
vmid=101&hostname=demo-ct&ostemplate=local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

### Clone a VM

- **Method:** `POST`  
- **Path:** `/api2/json/nodes/{node}/qemu/{template_vmid}/clone`

---

## Step‑by‑step configuration in FortiSOAR (HTTP connector)

1. Open **FortiSOAR**.  
2. Go to **Connectors → Add Connector**.  
3. Select **HTTP** from the list.  
4. Fill in:
   - Name: `Proxmox API`  
   - Description: `HTTP connector for Proxmox VE API integration`  
   - Host / Port / Protocol (`HTTPS`)  
   - Verify SSL as needed.  
5. Add the custom header:
   - Name: `Authorization`  
   - Value: `PVEAPIToken=<user@realm>!<tokenid>=<token_value>`  
6. Adjust timeout and retry settings if required.  
7. Save the connector.

> Note: This HTTP connector is kept only for backward compatibility. In this pack, all new playbooks are designed to use the native `proxmox-api` connector instead.

---

## Troubleshooting

**Connection refused**

- Verify host/IP and port.  
- Confirm the Proxmox API service is listening on the configured port.

**401 Unauthorized**

- Check the API token value and format in the `Authorization` header.  
- Confirm the token has the required privileges.  
- Regenerate the token if needed.

**SSL certificate verification failed**

- For testing: set *Verify SSL* to `false`.  
- For production: import the Proxmox certificate into FortiSOAR or use a CA‑signed certificate.

---

## JSON reference

An example of a complete HTTP connector configuration is kept in this repository for historical reference.  
For new configurations, rely on the native `proxmox-api` connector and its `info.json` / Python implementation.

