# -*- coding: utf-8 -*-
"""
Proxmox VE Hypervisor - operations.
Proxmox VE REST API calls with token authentication.
"""

from connectors.core.connector import get_logger, ConnectorError
import requests
import time
import json
import math
import re
from urllib.parse import quote

logger = get_logger("Proxmox VE Hypervisor")

BASE_PATH = "/api2/json"


def _params_dict(params):
    """FortiSOAR may send params as [] when no step inputs are defined."""
    return params if isinstance(params, dict) else {}


def _resolve_node(config, params):
    """Node from step params or connector configuration (Default Node Name)."""
    p = _params_dict(params)
    node = p.get("node") or config.get("node") or ""
    if isinstance(node, str):
        node = node.strip()
    if not node:
        raise ConnectorError(
            "node is required (pass node in the playbook step or set Default Node Name on the connector configuration)"
        )
    return node


def _base_url(config):
    """Builds the base URL from the connector configuration."""
    host = config.get("host", "").strip().rstrip("/")
    port = int(config.get("port") or 8006)
    protocol = "https" if port in (443, 8006) else "http"
    return "{}://{}:{}".format(protocol, host, port)


def _headers(config):
    """Authorization header with PVEAPIToken."""
    token = config.get("api_token") or ""
    return {"Authorization": "PVEAPIToken={}".format(token)}


def _request(config, method, path, data=None, json_body=None):
    """
    Executes an API request.
    path: path starting after /api2/json, for example "version" or "cluster/nextid".
    """
    url = _base_url(config) + BASE_PATH + "/" + path.lstrip("/")
    verify = bool(config.get("verify_ssl", False))
    headers = _headers(config)

    if json_body is not None:
        headers["Content-Type"] = "application/json"

    try:
        if method.upper() == "GET":
            r = requests.get(url, headers=headers, verify=verify, timeout=30)
        elif method.upper() == "POST":
            if json_body is not None:
                r = requests.post(url, headers=headers, json=json_body, verify=verify, timeout=60)
            else:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                r = requests.post(url, headers=headers, data=data or {}, verify=verify, timeout=60)
        elif method.upper() == "PUT":
            if json_body is not None:
                r = requests.put(url, headers=headers, json=json_body, verify=verify, timeout=30)
            else:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                r = requests.put(url, headers=headers, data=data or {}, verify=verify, timeout=30)
        elif method.upper() == "DELETE":
            # Proxmox returns 501 if DELETE has any body; never send data
            r = requests.delete(url, headers=headers, verify=verify, timeout=60)
        else:
            raise ConnectorError("Unsupported method: {}".format(method))

        # Proxmox may return 200/204 with empty or non-JSON body for DELETE
        try:
            out = r.json() if (r.text and r.text.strip()) else {}
        except (ValueError, TypeError):
            out = {}
        if not r.ok:
            err = out.get("errors") if isinstance(out, dict) else None
            if not err and isinstance(out, dict):
                err = out.get("message")
            if not err:
                err = r.text or "Unknown error"
            raise ConnectorError("API error {}: {}".format(r.status_code, err))
        return out
    except requests.exceptions.RequestException as e:
        raise ConnectorError("Request failed: {}".format(str(e)))


def _wait_for_task(config, node, upid, timeout=300, interval=2, task_label="task"):
    """Poll task status until stopped or timeout. UPID format: UPID:node:pid:..."""
    upid_enc = quote(upid, safe="")
    path = "nodes/{}/tasks/{}/status".format(node, upid_enc)
    deadline = time.time() + timeout
    while time.time() < deadline:
        out = _request(config, "GET", path)
        # Response can be {"data": {...}} or {...} at root
        data = out.get("data") if isinstance(out.get("data"), dict) else (out if isinstance(out, dict) else {})
        status = data.get("status")
        exitstatus = data.get("exitstatus")
        if status == "stopped":
            if exitstatus not in ("OK", "0", 0, None):
                raise ConnectorError("{} failed: exitstatus={}".format(task_label, exitstatus))
            return
        time.sleep(interval)
    raise ConnectorError("Timeout waiting for {} ({}s)".format(task_label, timeout))


def _check_health(config):
    """Health check: GET /api2/json/version."""
    _request(config, "GET", "version")
    return True


def get_version(config, params):
    """GET /api2/json/version."""
    return _request(config, "GET", "version")


def get_next_vmid(config, params):
    """GET /api2/json/cluster/nextid."""
    return _request(config, "GET", "cluster/nextid")


def clone_vm(config, params):
    """POST /api2/json/nodes/{node}/qemu/{vmid}/clone. Waits for async clone task (UPID) before returning."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/qemu/{}/clone".format(node, vmid)
    data = {
        "newid": params.get("newid"),
        "name": params.get("name"),
        "storage": params.get("storage") or "",
        "full": 1 if params.get("full", True) else 0,
    }
    out = _request(config, "POST", path, data=data)
    upid = out.get("data") if isinstance(out.get("data"), str) and (out.get("data") or "").strip().startswith("UPID:") else None
    if upid:
        wait_timeout = int(params.get("timeout") or config.get("clone_timeout") or 1800)
        _wait_for_task(config, node, upid.strip(), timeout=wait_timeout, task_label="VM clone")
    return out


def create_container(config, params):
    """POST /api2/json/nodes/{node}/lxc. After create, applies features (e.g. nesting=1) via config API so they take effect (like legacy scripts)."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node:
        raise ConnectorError("node is required")
    if vmid is None:
        raise ConnectorError("vmid is required")
    path = "nodes/{}/lxc".format(node)
    data = {
        "vmid": vmid,
        "hostname": params.get("hostname"),
        "ostemplate": params.get("ostemplate"),
        "cores": params.get("cores", 2),
        "memory": params.get("memory", 2048),
        "rootfs": params.get("rootfs"),
        "net0": params.get("net0"),
        "swap": params.get("swap", 0),
        "unprivileged": 1 if params.get("unprivileged", True) else 0,
    }
    if params.get("password"):
        data["password"] = params.get("password")
    if params.get("nameserver"):
        data["nameserver"] = params.get("nameserver")
    if params.get("features") is not None:
        data["features"] = params.get("features")
    out = _request(config, "POST", path, data=data)
    # Create is async: wait for task so container config exists, then set features via config API
    upid = out.get("data") if isinstance(out.get("data"), str) and (out.get("data") or "").strip().startswith("UPID:") else None
    if upid:
        try:
            _wait_for_task(config, node, upid.strip(), task_label="Container create")
        except ConnectorError:
            time.sleep(30)  # fallback: wait 30s then try config PUT anyway
    else:
        time.sleep(30)  # no UPID: wait for create to finish then set features
    features = params.get("features") or "nesting=1"
    config_path = "nodes/{}/lxc/{}/config".format(node, vmid)
    try:
        put_resp = _request(config, "PUT", config_path, data={"features": features})
        if put_resp.get("success") == 0:
            err = put_resp.get("errors") or put_resp.get("message") or put_resp
            logger.warning("Container features (nesting=1) may not be set: %s", err)
    except ConnectorError as e:
        logger.warning("Config PUT for features failed (container created, may lack nesting): %s", str(e))
    return out


def config_container(config, params):
    """PUT /api2/json/nodes/{node}/lxc/{vmid}/config. Set features (e.g. nesting=1), unprivileged, etc."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    body_params = params.get("body_params")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    if not body_params:
        raise ConnectorError("body_params is required")
    path = "nodes/{}/lxc/{}/config".format(node, vmid)
    if isinstance(body_params, dict):
        data = body_params
    elif isinstance(body_params, str):
        try:
            data = json.loads(body_params)
        except ValueError as e:
            raise ConnectorError("body_params must be valid JSON: {}".format(str(e)))
    else:
        raise ConnectorError("body_params must be a dict or JSON string")
    return _request(config, "PUT", path, data=data)


def config_vm(config, params):
    """PUT /api2/json/nodes/{node}/qemu/{vmid}/config."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    body_params = params.get("body_params")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    if not body_params:
        raise ConnectorError("body_params (JSON) is required")
    path = "nodes/{}/qemu/{}/config".format(node, vmid)
    if isinstance(body_params, dict):
        data = body_params
    elif isinstance(body_params, str):
        try:
            data = json.loads(body_params)
        except ValueError as e:
            raise ConnectorError("body_params must be valid JSON: {}".format(str(e)))
    else:
        raise ConnectorError("body_params must be a JSON object or JSON string")
    return _request(config, "PUT", path, data=data)


def _parse_proxmox_size_gb(size_token):
    """Parse Proxmox size tokens: 10G, 32G, 10GB, or byte counts (10737418240)."""
    if size_token is None:
        return None
    s = str(size_token).strip()
    if not s:
        return None
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([KMGT])?B?$", s, re.I)
    if not m:
        return None
    num = float(m.group(1))
    unit = (m.group(2) or "").upper()
    if unit == "T":
        return num * 1024.0
    if unit == "G":
        return num
    if unit == "M":
        return num / 1024.0
    if unit == "K":
        return num / (1024.0 ** 2)
    # No unit: large values are bytes; small integers are GB (template shorthand).
    if num >= 1024 * 1024:
        return num / (1024.0 ** 3)
    return num


def _disk_size_gb_from_config_value(disk_value):
    """Parse Proxmox disk config (scsi0/virtio0) size in GB, or None if unknown."""
    if not disk_value:
        return None
    s = str(disk_value)
    m = re.search(r"size=(\S+)", s, re.I)
    if m:
        return _parse_proxmox_size_gb(m.group(1))
    return None


def _current_vm_disk_size_gb(config, node, vmid, disk="scsi0", assume_gb=None):
    """Best-effort boot disk size in GB from qemu config, then status/current maxdisk."""
    cfg_resp = get_vm_config(config, {"node": node, "vmid": vmid})
    cfg = cfg_resp.get("data") if isinstance(cfg_resp.get("data"), dict) else cfg_resp
    if isinstance(cfg, dict):
        current_gb = _disk_size_gb_from_config_value(cfg.get(disk))
        if current_gb is not None and current_gb >= 1:
            return current_gb
    try:
        status_resp = get_vm_status(config, {"node": node, "vmid": vmid})
        data = status_resp.get("data") if isinstance(status_resp.get("data"), dict) else status_resp
        if isinstance(data, dict) and data.get("maxdisk") is not None:
            maxdisk_gb = int(data["maxdisk"]) / (1024.0 ** 3)
            if maxdisk_gb >= 1:
                return maxdisk_gb
    except ConnectorError as e:
        logger.warning("Could not read VM %s status for disk size: %s", vmid, str(e))
    if assume_gb is not None:
        try:
            return float(int(assume_gb))
        except (TypeError, ValueError):
            pass
    return None


def _validate_resize_size(size):
    """Proxmox treats bare '11G' as add 11 GB; require leading + or -."""
    if size is None:
        return None
    s = str(size).strip()
    if not s:
        return None
    if s[0] in "+-":
        return s
    if re.match(r"^\d+(\.\d+)?\s*G(B)?$", s, re.I):
        raise ConnectorError(
            "Resize size '{}' is interpreted by Proxmox as ADD that many GB. "
            "Use '+NG' (e.g. +1G) or target_gb with assume_current_gb.".format(s)
        )
    return s


def resize_vm_disk(config, params):
    """PUT /api2/json/nodes/{node}/qemu/{vmid}/resize (qm resize). Grows disk when target_gb exceeds current size."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    disk = params.get("disk") or "scsi0"
    size = _validate_resize_size(params.get("size"))
    target_gb = params.get("target_gb")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    resize_meta = None
    if target_gb is not None and not size:
        try:
            target_gb = int(target_gb)
        except (TypeError, ValueError):
            raise ConnectorError("target_gb must be an integer")
        assume_gb = params.get("assume_current_gb")
        if assume_gb is None:
            assume_gb = params.get("default_disk_gb")
        current_gb = _current_vm_disk_size_gb(
            config, node, vmid, disk, assume_gb=assume_gb
        )
        if current_gb is None:
            return {
                "success": 1,
                "skipped": True,
                "message": (
                    "Could not determine current {} size for VM {}; "
                    "skipped resize to avoid adding {}G instead of growing to {}G total. "
                    "Check qm config / status/current or resize manually."
                ).format(disk, vmid, target_gb, target_gb),
            }
        if target_gb <= int(math.floor(current_gb + 0.001)):
            return {
                "success": 1,
                "skipped": True,
                "message": "disk already {:.2f} GB (target {} GB)".format(current_gb, target_gb),
            }
        delta = max(1, int(math.ceil(target_gb - current_gb)))
        # Mis-read current size (~0) would send +{target}G and double the disk (e.g. 10+11=21).
        if assume_gb is not None and delta >= target_gb:
            try:
                fallback_current = float(int(assume_gb))
                if fallback_current >= 1:
                    logger.warning(
                        "VM %s resize: delta %s G suspicious; using assume_current_gb=%s",
                        vmid,
                        delta,
                        assume_gb,
                    )
                    current_gb = fallback_current
                    delta = max(1, int(math.ceil(target_gb - current_gb)))
            except (TypeError, ValueError):
                pass
        size = "+{}G".format(delta)
        resize_meta = {
            "current_gb": round(current_gb, 2),
            "target_gb": target_gb,
            "delta_gb": delta,
            "size": size,
        }
    if not size:
        raise ConnectorError("size or target_gb is required")
    path = "nodes/{}/qemu/{}/resize".format(node, vmid)
    out = _request(config, "PUT", path, data={"disk": disk, "size": size})
    if resize_meta and isinstance(out, dict):
        out["resize"] = resize_meta
    upid = (
        out.get("data")
        if isinstance(out.get("data"), str) and str(out.get("data", "")).strip().startswith("UPID:")
        else None
    )
    if upid:
        wait_timeout = int(params.get("timeout") or config.get("resize_timeout") or 600)
        _wait_for_task(config, node, upid.strip(), timeout=wait_timeout, task_label="VM disk resize")
    return out


def update_vm_cloudinit(config, params):
    """PUT /api2/json/nodes/{node}/qemu/{vmid}/cloudinit - regenerate cloud-init drive (qm cloudinit update)."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/qemu/{}/cloudinit".format(node, vmid)
    return _request(config, "PUT", path, data={})


def start_vm(config, params):
    """POST /api2/json/nodes/{node}/qemu/{vmid}/status/start."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/qemu/{}/status/start".format(node, vmid)
    return _request(config, "POST", path, data={})


def stop_vm(config, params):
    """POST /api2/json/nodes/{node}/qemu/{vmid}/status/stop."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/qemu/{}/status/stop".format(node, vmid)
    return _request(config, "POST", path, data={})


def start_container(config, params):
    """POST /api2/json/nodes/{node}/lxc/{vmid}/status/start."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/lxc/{}/status/start".format(node, vmid)
    return _request(config, "POST", path, data={})


def stop_container(config, params):
    """POST /api2/json/nodes/{node}/lxc/{vmid}/status/stop."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/lxc/{}/status/stop".format(node, vmid)
    return _request(config, "POST", path, data={})


def destroy_vm(config, params):
    """DELETE /api2/json/nodes/{node}/qemu/{vmid}?purge=1."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/qemu/{}".format(node, vmid)
    if params.get("purge", True):
        path += "?purge=1"
    return _request(config, "DELETE", path)


def _truthy(value):
    """Return True if value is truthy (boolean true, string 'true'/'1', or 1)."""
    if value is True or value == 1:
        return True
    if isinstance(value, str) and value.lower() in ("true", "1", "yes"):
        return True
    return False


def destroy_container(config, params):
    """DELETE /api2/json/nodes/{node}/lxc/{vmid}.

    Proxmox requires containers to be stopped before destruction.
    Do not send a body with DELETE (Proxmox returns 501). Use query param for force.
    """
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/lxc/{}".format(node, vmid)
    if _truthy(params.get("force")):
        path += "?force=1"
    last_error = None
    max_attempts = 8
    retry_delay_seconds = 8
    for attempt in range(max_attempts):
        try:
            return _request(config, "DELETE", path)
        except ConnectorError as e:
            last_error = e
            msg = (str(e) or "").lower()
            if "container is running" in msg or "unable to destroy" in msg:
                if attempt < max_attempts - 1:
                    logger.info("Destroy CT %s: still running, waiting %ss before retry (%d/%d)",
                                vmid, retry_delay_seconds, attempt + 1, max_attempts)
                    time.sleep(retry_delay_seconds)
                    continue
            raise
    raise last_error


def api_request(config, params):
    """Generic API request."""
    method = (params.get("method") or "GET").upper()
    url_path = (params.get("url_path") or "").strip().lstrip("/")
    if not url_path:
        raise ConnectorError("url_path is required")
    body = params.get("body")
    body_json = params.get("body_json")
    if body_json is not None and not isinstance(body_json, dict):
        raise ConnectorError("body_json must be a JSON object")
    data = None
    json_body = None
    if body_json is not None:
        json_body = body_json
    elif body:
        data = body if isinstance(body, dict) else {"_raw": body}
    return _request(config, method, url_path, data=data, json_body=json_body)


# --- Inventory & monitoring (without extended permissions) ---


def _format_disks_summary(cfg):
    """Human‑friendly summary from Proxmox disk keys (scsi0, ide0, rootfs, mp0, etc.)."""
    if not cfg or not isinstance(cfg, dict):
        return ""
    parts = []
    for k in sorted(cfg.keys()):
        v = cfg.get(k)
        if v is None:
            continue
        v = str(v).strip()
        if not v:
            continue
        # QEMU: ide0, scsi0, sata0, virtio0; LXC: rootfs, mp0, mp1; unused
        is_disk = (
            k == "rootfs"
            or k.startswith("ide")
            or k.startswith("scsi")
            or k.startswith("sata")
            or k.startswith("virtio")
            or k.startswith("unused")
            or (k.startswith("mp") and (len(k) == 2 or (len(k) > 2 and k[2:].isdigit())))
        )
        if is_disk:
            storage = None
            size = None
            first_seg = v.split(",", 1)[0]
            if ":" in first_seg:
                storage = first_seg.split(":", 1)[0]
            for seg in v.split(","):
                seg = seg.strip()
                if seg.startswith("size="):
                    size = seg.split("=", 1)[1]
                    break
            label_bits = []
            if size:
                label_bits.append(size)
            if storage:
                label_bits.append("on {}".format(storage))
            if label_bits:
                label = " ".join(label_bits)
            else:
                # Fallback to raw but keep short
                label = v if len(v) <= 60 else v[:57] + "..."
            parts.append("{}: {}".format(k, label))
    return "; ".join(parts)


def _format_interfaces_summary(cfg):
    """Human‑friendly summary from Proxmox net keys (net0, net1, ...)."""
    if not cfg or not isinstance(cfg, dict):
        return ""
    parts = []
    for k in sorted(cfg.keys()):
        if not k.startswith("net"):
            continue
        v = cfg.get(k)
        if v is None:
            continue
        v = str(v).strip()
        if not v:
            continue
        bridge = None
        vlan = None
        ip = None
        for seg in v.split(","):
            seg = seg.strip()
            if seg.startswith("bridge="):
                bridge = seg.split("=", 1)[1]
            elif seg.startswith("tag="):
                vlan = seg.split("=", 1)[1]
            elif seg.startswith("ip="):
                ip = seg.split("=", 1)[1]
        label_bits = []
        if bridge:
            label_bits.append(bridge)
        if vlan:
            label_bits.append("vlan {}".format(vlan))
        if ip:
            label_bits.append(ip)
        if label_bits:
            label = ", ".join(label_bits)
        else:
            label = v if len(v) <= 60 else v[:57] + "..."
        parts.append("{}: {}".format(k, label))
    return "; ".join(parts)


def list_vms(config, params):
    """GET /api2/json/nodes/{node}/qemu - list all VMs on the node. Optionally include config (disks, net) per VM."""
    node = _resolve_node(config, params)
    if not node:
        raise ConnectorError("node is required")
    path = "nodes/{}/qemu".format(node)
    out = _request(config, "GET", path)
    raw_flag = params.get("include_config")
    include_config = True if raw_flag is None else _truthy(raw_flag)
    if include_config and out.get("data"):
        for vm in out["data"]:
            vmid = vm.get("vmid")
            if vmid is not None:
                try:
                    cfg_path = "nodes/{}/qemu/{}/config".format(node, vmid)
                    cfg_resp = _request(config, "GET", cfg_path)
                    cfg = cfg_resp.get("data") if isinstance(cfg_resp, dict) else {}
                    vm["config"] = cfg
                except Exception as e:
                    logger.warning("get vm config vmid=%s: %s", vmid, e)
                    vm["config"] = {}
                    cfg = {}
                vm["disksSummary"] = _format_disks_summary(cfg)
                vm["interfacesSummary"] = _format_interfaces_summary(cfg)
    return out


def list_containers(config, params):
    """GET /api2/json/nodes/{node}/lxc - list all containers on the node. Optionally include config (rootfs, mp, net) per container."""
    node = _resolve_node(config, params)
    if not node:
        raise ConnectorError("node is required")
    path = "nodes/{}/lxc".format(node)
    out = _request(config, "GET", path)
    raw_flag = params.get("include_config")
    include_config = True if raw_flag is None else _truthy(raw_flag)
    if include_config and out.get("data"):
        for ct in out["data"]:
            vmid = ct.get("vmid")
            if vmid is not None:
                try:
                    cfg_path = "nodes/{}/lxc/{}/config".format(node, vmid)
                    cfg_resp = _request(config, "GET", cfg_path)
                    cfg = cfg_resp.get("data") if isinstance(cfg_resp, dict) else {}
                    ct["config"] = cfg
                except Exception as e:
                    logger.warning("get container config vmid=%s: %s", vmid, e)
                    ct["config"] = {}
                    cfg = {}
                ct["disksSummary"] = _format_disks_summary(cfg)
                ct["interfacesSummary"] = _format_interfaces_summary(cfg)
    return out


def get_vm_config(config, params):
    """GET /api2/json/nodes/{node}/qemu/{vmid}/config - VM config (disks, net, etc.)."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/qemu/{}/config".format(node, vmid)
    return _request(config, "GET", path)


def get_container_config(config, params):
    """GET /api2/json/nodes/{node}/lxc/{vmid}/config - container config (rootfs, mp, net, etc.)."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/lxc/{}/config".format(node, vmid)
    return _request(config, "GET", path)


def get_task_status(config, params):
    """GET /api2/json/nodes/{node}/tasks/{upid}/status - status of a task (for example clone job)."""
    node = _resolve_node(config, params)
    upid = params.get("upid")
    if not node or not upid:
        raise ConnectorError("node and upid are required")
    path = "nodes/{}/tasks/{}/status".format(node, upid)
    return _request(config, "GET", path)


def get_nodes(config, params):
    """GET /api2/json/nodes - list of all cluster nodes with status."""
    return _request(config, "GET", "nodes")


def get_cluster_resources(config, params):
    """GET /api2/json/cluster/resources - cluster resources (optional: type=node|vm|storage)."""
    path = "cluster/resources"
    if params.get("type"):
        path += "?type={}".format(params.get("type"))
    return _request(config, "GET", path)


# --- Status queries (requires VM.Audit on the VM/CT or Sys.Audit/Datastore.Audit) ---


def get_vm_status(config, params):
    """GET /api2/json/nodes/{node}/qemu/{vmid}/status/current - detailed status of a VM. Requires VM.Audit."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/qemu/{}/status/current".format(node, vmid)
    return _request(config, "GET", path)


def get_container_status(config, params):
    """GET /api2/json/nodes/{node}/lxc/{vmid}/status/current - detailed status of a container. Requires VM.Audit."""
    node = _resolve_node(config, params)
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/lxc/{}/status/current".format(node, vmid)
    return _request(config, "GET", path)


def get_node_status(config, params):
    """GET /api2/json/nodes/{node}/status - node resources (memory, CPU). Requires Sys.Audit."""
    node = _resolve_node(config, params)
    path = "nodes/{}/status".format(node)
    return _request(config, "GET", path)


def get_storage_status(config, params):
    """GET /api2/json/nodes/{node}/storage/{storage}/status - storage status (disk). Requires Datastore.Audit."""
    p = _params_dict(params)
    node = _resolve_node(config, params)
    storage = p.get("storage")
    if not storage:
        raise ConnectorError("storage is required")
    path = "nodes/{}/storage/{}/status".format(node, storage)
    return _request(config, "GET", path)


def get_storage_content(config, params):
    """GET /api2/json/nodes/{node}/storage/{storage}/content - storage content (templates, images). Requires Datastore.Audit."""
    node = _resolve_node(config, params)
    storage = params.get("storage")
    if not node or not storage:
        raise ConnectorError("node and storage are required")
    path = "nodes/{}/storage/{}/content".format(node, storage)
    if params.get("content"):
        path += "?content={}".format(params.get("content"))
    return _request(config, "GET", path)


operations = {
    "get_version": get_version,
    "get_next_vmid": get_next_vmid,
    "clone_vm": clone_vm,
    "create_container": create_container,
    "config_container": config_container,
    "config_vm": config_vm,
    "resize_vm_disk": resize_vm_disk,
    "update_vm_cloudinit": update_vm_cloudinit,
    "start_vm": start_vm,
    "stop_vm": stop_vm,
    "start_container": start_container,
    "stop_container": stop_container,
    "destroy_vm": destroy_vm,
    "destroy_container": destroy_container,
    "api_request": api_request,
    # Inventar & Monitoring
    "list_vms": list_vms,
    "list_containers": list_containers,
    "get_vm_config": get_vm_config,
    "get_container_config": get_container_config,
    "get_task_status": get_task_status,
    "get_nodes": get_nodes,
    "get_cluster_resources": get_cluster_resources,
    # Status (teilweise erweiterte Berechtigungen)
    "get_vm_status": get_vm_status,
    "get_container_status": get_container_status,
    "get_node_status": get_node_status,
    "get_storage_status": get_storage_status,
    "get_storage_content": get_storage_content,
    "check_health": _check_health,
}
