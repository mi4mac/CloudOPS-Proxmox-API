# VM provisioning (Rocky9-VM and containers)

Guide for **> Provision VM Instances**, the Proxmox connector, and the **Disk GB** field on VM Instance records.

See also: [PACK_README.md](PACK_README.md), [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md), [TESTING_GUIDE.md](TESTING_GUIDE.md), [SCHRITT_2_GLOBAL_VARIABLES.md](SCHRITT_2_GLOBAL_VARIABLES.md).

## Prerequisites

- FortiSOAR with **API Connector Proxmox** **2.0.8+** (from `CloudOPS_Solution_Pack.zip` or `API Connector Proxmox.tgz`)
- Proxmox user/role/token with clone, config, cloud-init, resize, and power permissions ([TOKEN_CAPABILITIES.md](TOKEN_CAPABILITIES.md))
- Rocky 9 **QEMU template** with cloud-init drive (`ide2`), virtio NIC, `qemu-guest-agent` recommended
- Globals (optional): `proxmox_template_rocky9_vm`, `proxmox_ci_user`, `proxmox_default_disk_gb`, `proxmox_vm_boot_disk`, network/storage globals in [SCHRITT_2_GLOBAL_VARIABLES.md](SCHRITT_2_GLOBAL_VARIABLES.md)

## Approval flow

1. **Request VM Instance** → creates a VM Instance record  
2. **> Manage Service Request** → AD enrichment, approval, then calls **> Provision VM Instances**  
3. Success email includes IP, `proxmox_ci_user`, and password from **rootPassword**

Sub-playbook UUIDs must match the pack (see [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md#import-uuid-missing)).

## Rocky9-VM playbook steps

| Step | Proxmox / action |
|------|------------------|
| Clone VM API | `qm clone` full; connector waits for clone task |
| Config VM API | `qm set`: CPU, RAM, `net0`, `ipconfig0`, `ciuser`, `cipassword`, `nameserver` — **does not set scsi0** |
| Custom VM Disk Size | Decision: resize only if **diskGB** ≠ default (see below) |
| Resize VM Disk API | `qm resize` grow-only to **diskGB** (connector `resize_vm_disk`) |
| Update Cloud-Init API | `qm cloudinit update` |
| Start VM API | `qm start` |

Open the playbook in the designer for the sticky note **Info - VM Disk GB**.

## Disk GB on the VM Instance record

| Value | Rocky9-VM behavior | Container behavior |
|-------|-------------------|-------------------|
| Empty or **10** (`proxmox_default_disk_gb`) | **No resize** — keep template disk size | **rootfs** default 10 GB at create |
| **20**, **32**, etc. | **Resize VM Disk API** grows `scsi0` to target (grow-only; never shrinks) | N/A (size fixed at create) |

The default **10** means “use template size” for VMs, not “add 10 GB”. To grow a VM, set an explicit size other than 10 before provisioning.

## Manual equivalent (Rocky 9)

```bash
qm clone 9000 <NEWID> --name my-vm --full 1
qm set <NEWID> --net0 virtio,bridge=vmbr0,tag=255
qm set <NEWID> --ipconfig0 ip=10.255.255.x/24,gw=10.255.255.1
# Optional only if you need a larger disk than the template:
# qm resize <NEWID> scsi0 +10G   # or set diskGB to 20 in FortiSOAR
qm cloudinit update <NEWID>
qm start <NEWID>
```

## Common issues

| Symptom | See |
|---------|-----|
| No bootable disk | [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) — do not set `scsi0` on config |
| Disk became 20 GB with diskGB 10 | Resize no longer runs for default 10; re-import latest pack |
| Asked for 11 GB, got 22 GB | Connector **2.0.8+** only uses `+delta G` after reading real disk size; older builds could treat `11G` as **add** 11 GB |
| `lock-*.conf` timeout | Clone not finished — use connector 2.0.5+ / wait on Proxmox tasks |
| Login password wrong | `proxmox_ci_user`, **Update Cloud-Init API**, **rootPassword** on record |
| Import UUID error | [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) |

## Connector versions (summary)

| Version | Capability |
|---------|------------|
| 2.0.5+ | Clone waits for async task |
| 2.0.6+ | `update_vm_cloudinit` |
| 2.0.7+ | `resize_vm_disk` (grow-only `target_gb`) |
| 2.0.8+ | Reliable current disk size (`qm config` + `maxdisk`); skips resize if unknown (no accidental double grow) |

## Testing

- [TESTING_GUIDE.md](TESTING_GUIDE.md) §4 — default disk, no resize  
- [TESTING_GUIDE.md](TESTING_GUIDE.md) §4b — custom disk resize (e.g. 20 GB)
