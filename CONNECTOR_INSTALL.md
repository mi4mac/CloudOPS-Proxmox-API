# Install / upgrade API Connector Proxmox (read this if you still see 2.0.7)

**Importing `CloudOPS_Solution_Pack.zip` does not upgrade an already-installed connector.**  
If FortiSOAR still shows **2.0.7** and a file time around **12:34**, you are on the **old pack build** (May 18) or the connector was never replaced.

## 1. Get the correct file from GitHub

After `git pull`, use **one** of these (same content):

| File | Purpose |
|------|---------|
| `releases/proxmox-api_2.1.0_INSTALL_THIS.tgz` | **Recommended** — upload this in FortiSOAR |
| `releases/API_Connector_Proxmox_Pack.zip` | Zip of the `.tgz` + `.sha256` (unzip, then upload the `.tgz`) |
| `connectors/API Connector Proxmox.tgz` | Same build (from `./build-connector.sh`) |
| `connectors/proxmox-api_2.1.0.tgz` | Versioned name |

Verify before upload (must print **2.1.0**):

```bash
tar -xOf releases/proxmox-api_2.1.0_INSTALL_THIS.tgz info.json | grep '"version"'
shasum -a 256 releases/proxmox-api_2.1.0_INSTALL_THIS.tgz
# compare to releases/proxmox-api_2.1.0.sha256
```

Wrong file if version is **2.0.7** or size is ~18 KB from an old `proxmox-api_2.0.7.tgz`.

## 2. Upload in FortiSOAR (connector import, not solution pack)

1. **Content Hub** (or **Connectors** → import / upload).
2. Upload **`proxmox-api_2.1.0_INSTALL_THIS.tgz`**.
3. Enable **Delete all existing versions** (removes 2.0.7 / 2.0.8 / 2.0.9).
4. Complete configuration (host, token, etc.).

## 3. Confirm

**Connectors** → **API Connector Proxmox** → version must be **2.1.0** (not 2.0.7).

Description should mention **build 2026-05-18** and **disk resize +delta G**.

## 4. Then import the solution pack (optional)

`./build-pack.sh` → import **`CloudOPS_Solution_Pack.zip`** for playbook changes.  
Playbooks now reference connector **2.1.0**; they will fail until step 2 is done.

## 5. SSH fallback (if UI import still shows 2.0.7)

On the FortiSOAR application host:

```bash
/opt/cyops-integrations/.env/bin/python /opt/cyops-integrations/integrations/manage.py reimport_connector -n proxmox-api -cv -migrate
```

Copy the new `.tgz` to the server first if the UI cannot see it.

See also [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md).
