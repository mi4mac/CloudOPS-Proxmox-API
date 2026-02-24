# Proxmox VE 9.1.5 – Specific Notes

## Important Differences from the General API Documentation

### 1. Authentication

#### API Token Format (Recommended)

```text
Authorization: PVEAPIToken={user}@{realm}!{token_id}={token_secret}
```

**Example:**

```text
Authorization: PVEAPIToken=fortisoar@pve!fortisoar-token=aaaaaaaaa-bbb-cccc-dddd-ef0123456789
```

**Important:**
- ✅ Use `PVEAPIToken=` for token‑based API authentication.
- ❌ `PVEAuthCookie=` is only for ticket‑based authentication.
- ✅ API tokens **do not require** a CSRF prevention token.
- ✅ API tokens do not expire (unless an explicit expire time is configured).

#### Creating a Token (Proxmox VE 9.1.5)

```bash
# Create user
pveum user add fortisoar@pve --password <password>

# Create token (token value is shown only once!)
pveum user token add fortisoar@pve fortisoar-token --expire 0

# Output looks like:
# ┌─────────────────────────────────────────────────────────────────────┐
# │ Token ID: fortisoar-token                                           │
# │ Token Value: aaaaa-bbbb-cccc-dddd-eeee-ffff-gggg-hhhh-iiii-jjjj     │
# └─────────────────────────────────────────────────────────────────────┘
```

**Store the token value securely!** It cannot be retrieved again later.

---

### 2. Content‑Type for POST/PUT Requests

The Proxmox VE 9.1.5 API accepts two request body formats:

#### Standard: x‑www‑form‑urlencoded

```text
Content-Type: application/x-www-form-urlencoded
```

**Example body:**

```text
newid=2001&name=testvm&storage=local-lvm&full=1
```

#### Alternative: JSON

```text
Content-Type: application/json
```

**Example body:**

```json
{
  "newid": 2001,
  "name": "testvm",
  "storage": "local-lvm",
  "full": 1
}
```

**Recommendation:** Use `application/x-www-form-urlencoded` for maximum compatibility; JSON also works, but some tooling and examples assume form encoding.

---

### 3. API Endpoints (Confirmed for 9.1.5)

#### VM Operations

- ✅ `GET /api2/json/cluster/nextid` – Fetch next VMID.
- ✅ `POST /api2/json/nodes/{node}/qemu/{vmid}/clone` – Clone VM.
- ✅ `POST /api2/json/nodes/{node}/qemu/{vmid}/config` – Configure VM.
- ✅ `POST /api2/json/nodes/{node}/qemu/{vmid}/status/start` – Start VM.
- ✅ `POST /api2/json/nodes/{node}/qemu/{vmid}/status/stop` – Stop VM.
- ✅ `DELETE /api2/json/nodes/{node}/qemu/{vmid}?purge=1` – Delete VM.

#### Container Operations

- ✅ `POST /api2/json/nodes/{node}/lxc` – Create container.
- ✅ `POST /api2/json/nodes/{node}/lxc/{vmid}/config` – Configure container.
- ✅ `POST /api2/json/nodes/{node}/lxc/{vmid}/status/start` – Start container.
- ✅ `POST /api2/json/nodes/{node}/lxc/{vmid}/status/stop` – Stop container.
- ✅ `DELETE /api2/json/nodes/{node}/lxc/{vmid}` – Delete container.

#### Resource Queries

- ✅ `GET /api2/json/nodes/{node}/status` – Node status (memory, CPU).
- ✅ `GET /api2/json/nodes/{node}/storage/{storage}/status` – Storage status.

---

### 4. Asynchronous Operations

#### Clone Operations Are Asynchronous

**Response:**

```json
{
  "data": "UPID:pve:00001234:5678:90ABCDEF:qmclone:2000:root@pam:"
}
```

**Query task status:**

```text
GET /api2/json/nodes/{node}/tasks/{upid}/status
```

**Example response:**

```json
{
  "data": {
    "status": "running",   // or "stopped"
    "exitstatus": "OK",    // or an error code
    ...
  }
}
```

**Alternative:** Wait until VM/container status is available:

```text
GET /api2/json/nodes/{node}/qemu/{vmid}/status/current
GET /api2/json/nodes/{node}/lxc/{vmid}/status/current
```

---

### 5. Error Handling

#### HTTP Status Codes

- `200` – Success.
- `201` – Created.
- `400` – Bad Request (invalid parameters).
- `401` – Unauthorized (invalid token).
- `403` – Forbidden (insufficient permissions).
- `404` – Not Found (VMID/template does not exist).
- `500` – Internal Server Error.
- `503` – Service Unavailable.

#### Error Response Format

```json
{
  "errors": {
    "property": "error message"
  }
}
```

---

### 6. Permissions for the API Token

**Minimal permissions for VM/container management:**

```bash
pveum role add FortiSOAR-Role -privs \
  "Datastore.AllocateSpace \
   Datastore.Audit \
   Pool.Allocate \
   Sys.Audit \
   Sys.Console \
   Sys.Modify \
   VM.Allocate \
   VM.Audit \
   VM.Clone \
   VM.Config.CDROM \
   VM.Config.CPU \
   VM.Config.Cloudinit \
   VM.Config.Disk \
   VM.Config.HWType \
   VM.Config.Memory \
   VM.Config.Network \
   VM.Config.Options \
   VM.Monitor \
   VM.PowerMgmt \
   SDN.Use"
```

**Notes:**

- `VM.Allocate` covers both creation and deletion of VMs/containers. There is no separate `VM.Delete` privilege in Proxmox VE.

**Assigning the role:**

```bash
pveum aclmod / -user fortisoar@pve -role FortiSOAR-Role
```

---

### 7. Differences Compared to Older Versions

#### Proxmox VE 9.1.5 vs. older versions

- ✅ API token format remains the same (`PVEAPIToken=`).
- ✅ Endpoints remain compatible within the same major version.
- ✅ JSON schema‑based validation.
- ✅ Automatic parameter validation.

---

### 8. Best Practices for FortiSOAR Integration

1. **Token security**
   - Store the token encrypted in FortiSOAR global variables.
   - Create tokens with minimal required permissions.
   - Implement token rotation (optional).

2. **Error handling**
   - Check HTTP status codes.
   - Parse the error response body (`errors` field).
   - Store error messages in the VM Instance logs.

3. **Async operations**
   - Treat clone operations as asynchronous.
   - Monitor task status or poll the VM/container status.
   - Implement a timeout mechanism (for example 60 seconds).

4. **Content‑Type**
   - Default: `application/x-www-form-urlencoded`.
   - JSON is accepted as well, but `x-www-form-urlencoded` is more widely compatible.

5. **VMID management**
   - On creation: store the Proxmox ID in the `v_m_instances` record.
   - On destroy: read the Proxmox ID from the record (do not search by name).

6. **Privilege separation & token ACLs**
   - When `privsep=1` (default), user ACLs do **not** automatically apply to the token.
   - In that case, you must assign ACLs explicitly to the token, for example:

     ```bash
     pveum user token modify fortisoar@pve fortisoar-token --privsep 1

     # Base rights
     pveum aclmod /          -token 'fortisoar@pve!fortisoar-token' -role FortiSOAR-Role
     pveum aclmod /nodes     -token 'fortisoar@pve!fortisoar-token' -role FortiSOAR-Role
     pveum aclmod /nodes/pve -token 'fortisoar@pve!fortisoar-token' -role FortiSOAR-Role

     # Full VM/CT rights on the node
     pveum aclmod /nodes/pve -token 'fortisoar@pve!fortisoar-token' -role PVEVMAdmin

     # Optional: storage rights
     pveum aclmod /storage           -token 'fortisoar@pve!fortisoar-token' -role PVEVMAdmin
     pveum aclmod /storage/local-lvm -token 'fortisoar@pve!fortisoar-token' -role FortiSOAR-Role
     ```

   - Alternatively, you can set `privsep` to `0` so that the token inherits the user ACLs:

     ```bash
     pveum user token modify fortisoar@pve fortisoar-token --privsep 0
     ```

---

## References

- **Project:** `TOKEN_CAPABILITIES.md` – Overview of all connector operations and permission requirements.
- **Documentation:**  
  - Proxmox VE API documentation – `https://pve.proxmox.com/wiki/Proxmox_VE_API`  
  - Proxmox VE API viewer – `https://pve.proxmox.com/pve-docs/api-viewer/index.html`  
  - Proxmox VE 9.1 release notes – `https://pve.proxmox.com/wiki/Roadmap`

---

*Created: 2026‑02‑20, updated: 2026‑02‑23*  
*Version: 1.1*  
*Proxmox VE version: 9.1.5*

