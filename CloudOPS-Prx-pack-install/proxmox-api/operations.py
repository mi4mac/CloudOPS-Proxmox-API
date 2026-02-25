# -*- coding: utf-8 -*-
"""
API Connector Proxmox - operations.
Proxmox VE REST API calls with token authentication.
"""

from connectors.core.connector import get_logger, ConnectorError
import requests
import time
import json
from urllib.parse import quote

logger = get_logger("API Connector Proxmox")

BASE_PATH = "/api2/json"


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


def _wait_for_task(config, node, upid, timeout=300, interval=2):
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
                raise ConnectorError("Container create task failed: exitstatus={}".format(exitstatus))
            return
        time.sleep(interval)
    raise ConnectorError("Timeout waiting for container create task ({}s)".format(timeout))


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
    """POST /api2/json/nodes/{node}/qemu/{vmid}/clone."""
    node = params.get("node") or config.get("node")
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
    return _request(config, "POST", path, data=data)


def create_container(config, params):
    """POST /api2/json/nodes/{node}/lxc. After create, applies features (e.g. nesting=1) via config API so they take effect (like legacy scripts)."""
    node = params.get("node") or config.get("node")
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
            _wait_for_task(config, node, upid.strip())
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
    node = params.get("node") or config.get("node")
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
    node = params.get("node") or config.get("node")
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


def start_vm(config, params):
    """POST /api2/json/nodes/{node}/qemu/{vmid}/status/start."""
    node = params.get("node") or config.get("node")
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/qemu/{}/status/start".format(node, vmid)
    return _request(config, "POST", path, data={})


def stop_vm(config, params):
    """POST /api2/json/nodes/{node}/qemu/{vmid}/status/stop."""
    node = params.get("node") or config.get("node")
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/qemu/{}/status/stop".format(node, vmid)
    return _request(config, "POST", path, data={})


def start_container(config, params):
    """POST /api2/json/nodes/{node}/lxc/{vmid}/status/start."""
    node = params.get("node") or config.get("node")
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/lxc/{}/status/start".format(node, vmid)
    return _request(config, "POST", path, data={})


def stop_container(config, params):
    """POST /api2/json/nodes/{node}/lxc/{vmid}/status/stop."""
    node = params.get("node") or config.get("node")
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/lxc/{}/status/stop".format(node, vmid)
    return _request(config, "POST", path, data={})


def destroy_vm(config, params):
    """DELETE /api2/json/nodes/{node}/qemu/{vmid}?purge=1."""
    node = params.get("node") or config.get("node")
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
    node = params.get("node") or config.get("node")
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
    node = params.get("node") or config.get("node")
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
    node = params.get("node") or config.get("node")
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
    node = params.get("node") or config.get("node")
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/qemu/{}/config".format(node, vmid)
    return _request(config, "GET", path)


def get_container_config(config, params):
    """GET /api2/json/nodes/{node}/lxc/{vmid}/config - container config (rootfs, mp, net, etc.)."""
    node = params.get("node") or config.get("node")
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/lxc/{}/config".format(node, vmid)
    return _request(config, "GET", path)


def get_task_status(config, params):
    """GET /api2/json/nodes/{node}/tasks/{upid}/status - status of a task (for example clone job)."""
    node = params.get("node") or config.get("node")
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
    node = params.get("node") or config.get("node")
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/qemu/{}/status/current".format(node, vmid)
    return _request(config, "GET", path)


def get_container_status(config, params):
    """GET /api2/json/nodes/{node}/lxc/{vmid}/status/current - detailed status of a container. Requires VM.Audit."""
    node = params.get("node") or config.get("node")
    vmid = params.get("vmid")
    if not node or vmid is None:
        raise ConnectorError("node and vmid are required")
    path = "nodes/{}/lxc/{}/status/current".format(node, vmid)
    return _request(config, "GET", path)


def get_node_status(config, params):
    """GET /api2/json/nodes/{node}/status - node resources (memory, CPU). Requires Sys.Audit."""
    node = params.get("node") or config.get("node")
    if not node:
        raise ConnectorError("node is required")
    path = "nodes/{}/status".format(node)
    return _request(config, "GET", path)


def get_storage_status(config, params):
    """GET /api2/json/nodes/{node}/storage/{storage}/status - storage status (disk). Requires Datastore.Audit."""
    node = params.get("node") or config.get("node")
    storage = params.get("storage")
    if not node or not storage:
        raise ConnectorError("node and storage are required")
    path = "nodes/{}/storage/{}/status".format(node, storage)
    return _request(config, "GET", path)


def get_storage_content(config, params):
    """GET /api2/json/nodes/{node}/storage/{storage}/content - storage content (templates, images). Requires Datastore.Audit."""
    node = params.get("node") or config.get("node")
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
