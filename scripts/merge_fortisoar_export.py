#!/usr/bin/env python3
"""Merge FortiSOAR workflow_collections export into repo playbooks."""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
EXPORT_PATH = Path(
    "/Users/michaelibe/Downloads/19 Playbooks - 00 - Service Management (2026515443).json"
)
PB_DIR = REPO / "playbooks" / "00 - Service Management"
PACK_DIR = REPO / "CloudOPS-Prx-pack-install"

# Keys stripped for logic-normalized comparison
STRIP_STEP_KEYS = {"uuid", "top", "left", "status", "group", "id"}
STRIP_WORKFLOW_KEYS = {"lastModifyDate", "createDate", "modifyDate", "id"}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")


def strip_iri_urls(obj: Any) -> Any:
    """Replace /api/3/... IRIs with placeholders for comparison."""
    if isinstance(obj, str):
        if obj.startswith("/api/3/"):
            return "<IRI>"
        return obj
    if isinstance(obj, list):
        return [strip_iri_urls(x) for x in obj]
    if isinstance(obj, dict):
        return {k: strip_iri_urls(v) for k, v in obj.items()}
    return obj


def normalize_step(step: dict) -> dict:
    s = copy.deepcopy(step)
    for k in STRIP_STEP_KEYS:
        s.pop(k, None)
    args = s.get("arguments") or {}
    if "conditions" in args:
        for c in args["conditions"]:
            c.pop("step_iri", None)
    return strip_iri_urls(s)


def normalize_workflow(wf: dict) -> dict:
    w = copy.deepcopy(wf)
    for k in STRIP_WORKFLOW_KEYS:
        w.pop(k, None)
    w.pop("triggerStep", None)
    w.pop("collection", None)
    steps = w.get("steps") or []
    w["steps"] = sorted(
        [normalize_step(s) for s in steps], key=lambda x: x.get("name", "")
    )
    routes = w.get("routes") or []
    w["routes"] = sorted(
        [
            {
                "name": r.get("name"),
                "sourceStep": "<IRI>" if r.get("sourceStep") else None,
                "targetStep": "<IRI>" if r.get("targetStep") else None,
            }
            for r in routes
        ],
        key=lambda x: x.get("name", ""),
    )
    return w


def diff_summary(repo_wf: dict | None, export_wf: dict) -> list[str]:
    if repo_wf is None:
        return ["new in export (no repo file)"]
    rn, en = normalize_workflow(repo_wf), normalize_workflow(export_wf)
    changes: list[str] = []

    repo_steps = {s["name"]: s for s in rn.get("steps", [])}
    exp_steps = {s["name"]: s for s in en.get("steps", [])}
    for name in sorted(set(repo_steps) | set(exp_steps)):
        if name not in repo_steps:
            changes.append(f"+step: {name}")
        elif name not in exp_steps:
            changes.append(f"-step: {name}")
        elif repo_steps[name] != exp_steps[name]:
            changes.append(f"~step: {name}")

    repo_routes = {(r.get("name"), r.get("sourceStep"), r.get("targetStep")) for r in rn.get("routes", [])}
    exp_routes = {(r.get("name"), r.get("sourceStep"), r.get("targetStep")) for r in en.get("routes", [])}
    if repo_routes != exp_routes:
        added = len(exp_routes - repo_routes)
        removed = len(repo_routes - exp_routes)
        if added or removed:
            changes.append(f"routes: +{added}/-{removed}")

    for field in ("parameters", "description", "isActive", "synchronous"):
        if repo_wf.get(field) != export_wf.get(field):
            changes.append(f"~{field}")

    return changes if changes else ["unchanged"]


def repo_path_for_name(name: str) -> Path:
    return PB_DIR / f"{name}.json"


def step_by_name(wf: dict, step_name: str) -> dict | None:
    for s in wf.get("steps", []):
        if s.get("name") == step_name:
            return s
    return None


def preserve_destroy_notification(merged: dict, repo: dict) -> None:
    """Keep repo destroy notification flow if export regressed."""
    repo_names = {s["name"] for s in repo.get("steps", [])}
    critical = {
        "Build Destroy Summary",
        "Snapshot Expired Candidates",
        "Destroyed VM Summary Ready",
        "Notify Destroyed Expired",
        "Find Confirmed Destroyed VM Instances",
        "Finish Without Email",
    }
    merged_names = {s["name"] for s in merged.get("steps", [])}
    if critical - merged_names:
        # Export missing critical steps — restore from repo
        merged["steps"] = copy.deepcopy(repo["steps"])
        merged["routes"] = copy.deepcopy(repo.get("routes", []))
        return
    # Restore step bodies if export simplified notification jinja
    for step_name in ("Build Destroy Summary", "Snapshot Expired Candidates"):
        repo_step = step_by_name(repo, step_name)
        exp_step = step_by_name(merged, step_name)
        if repo_step and exp_step:
            repo_args = repo_step.get("arguments") or {}
            exp_args = exp_step.get("arguments") or {}
            if "send_destroy_notification" in repo_args and "send_destroy_notification" not in exp_args:
                exp_step["arguments"] = copy.deepcopy(repo_args)


def preserve_provision_failure_jinja(merged: dict, repo: dict) -> None:
    repo_step = step_by_name(repo, "Set Provision Failure Result")
    exp_step = step_by_name(merged, "Set Provision Failure Result")
    if not repo_step or not exp_step:
        return
    repo_cmd = (repo_step.get("arguments") or {}).get("cmd_result", "")
    exp_cmd = (exp_step.get("arguments") or {}).get("cmd_result", "")
    if "namespace(err" in repo_cmd and "namespace(err" not in exp_cmd:
        exp_step["arguments"] = copy.deepcopy(repo_step.get("arguments", {}))
    # Broken nested default() in export
    if exp_cmd.count("default(") > repo_cmd.count("default(") + 2 and "namespace(err" in repo_cmd:
        exp_step["arguments"] = copy.deepcopy(repo_step.get("arguments", {}))


def apply_from_str_export(merged: dict, export: dict) -> None:
    """Match from_str to export (user synced)."""
    for ms, es in zip(merged.get("steps", []), export.get("steps", [])):
        if ms.get("name") != es.get("name"):
            continue
        ma, ea = ms.get("arguments") or {}, es.get("arguments") or {}
        if "from_str" in ea:
            ma["from_str"] = ea["from_str"]


def merge_workflow(export_wf: dict, repo_wf: dict | None) -> dict:
    merged = copy.deepcopy(export_wf)
    if repo_wf is None:
        return merged
    name = merged.get("name", "")
    if name == "Destroy Expired VM Instances":
        preserve_destroy_notification(merged, repo_wf)
    if name == "> Provision VM Instances":
        preserve_provision_failure_jinja(merged, repo_wf)
    apply_from_str_export(merged, export_wf)
    return merged


def merge_global_vars(export_macros: list, repo_path: Path) -> bool:
    if not export_macros:
        return False
    repo_vars = load_json(repo_path) if repo_path.exists() else []
    by_name = {v["name"]: v for v in repo_vars}
    changed = False
    for m in export_macros:
        if m["name"] not in by_name or by_name[m["name"]] != m:
            by_name[m["name"]] = m
            changed = True
    merged = sorted(by_name.values(), key=lambda x: x["name"])
    if merged != repo_vars:
        save_json(repo_path, merged)
        return True
    return changed


def merge_tags(export_tags: list, repo_path: Path) -> bool:
    if not export_tags:
        return False
    repo_tags = load_json(repo_path) if repo_path.exists() else []
    merged = sorted(set(repo_tags) | set(export_tags))
    if merged != repo_tags:
        save_json(repo_path, merged)
        return True
    return False


def sync_pack_from_repo() -> None:
    if PACK_DIR.exists():
        shutil.rmtree(PACK_DIR)
    PACK_DIR.mkdir(parents=True)

    for item in [
        "info.json",
        "picklists",
        "modules",
        "views",
        "roles",
        "connectors",
        "actors",
        "dashboards",
        "playbooks",
    ]:
        src = REPO / item
        if src.exists():
            dest = PACK_DIR / item
            if src.is_dir():
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)


def validate_json_paths(*roots: Path) -> list[str]:
    errors = []
    paths: list[Path] = []
    for root in roots:
        if root.is_file():
            paths.append(root)
        else:
            paths.extend(sorted(root.rglob("*.json")))
    for p in paths:
        try:
            subprocess.run(
                [sys.executable, "-m", "json.tool", str(p)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            errors.append(f"{p}: {e.stderr.decode()}")
    return errors


def main() -> int:
    export = load_json(EXPORT_PATH)
    if export.get("type") != "workflow_collections":
        print("ERROR: expected workflow_collections export", file=sys.stderr)
        return 1

    collection = export["data"][0]
    workflows = collection.get("workflows", [])
    names = [w["name"] for w in workflows]
    print("=== 19 workflows in export ===")
    for i, n in enumerate(names, 1):
        print(f"{i:2}. {n}")

    results: list[dict] = []
    any_pb_change = False

    for export_wf in workflows:
        name = export_wf["name"]
        path = repo_path_for_name(name)
        repo_wf = load_json(path) if path.exists() else None
        summary = diff_summary(repo_wf, export_wf)
        changed = summary != ["unchanged"]
        merged = merge_workflow(export_wf, repo_wf)
        if repo_wf is None or normalize_workflow(repo_wf) != normalize_workflow(merged):
            save_json(path, merged)
            any_pb_change = True
            status = "CHANGED"
        else:
            status = "unchanged"

        results.append({"name": name, "status": status, "summary": "; ".join(summary)})

    gv_changed = merge_global_vars(
        export.get("macros", []), REPO / "playbooks" / "globalVariables.json"
    )
    tags_changed = merge_tags(
        export.get("exported_tags", []), REPO / "playbooks" / "tags.json"
    )

    print("\n=== Merge summary ===")
    print(f"{'Playbook':<50} {'Status':<10} Changes")
    print("-" * 100)
    for r in results:
        print(f"{r['name']:<50} {r['status']:<10} {r['summary']}")

    sync_pack_from_repo()
    print(f"\nSynced pack dir: {PACK_DIR}")

    subprocess.run([str(REPO / "build-pack.sh")], cwd=REPO, check=True)

    errors = validate_json_paths(
        PB_DIR,
        REPO / "playbooks" / "globalVariables.json",
        REPO / "playbooks" / "tags.json",
        PACK_DIR / "playbooks",
    )
    if errors:
        print("JSON validation errors:", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    # Write report for parent agent
    report = {
        "workflows": results,
        "globalVariables_changed": gv_changed,
        "tags_changed": tags_changed,
        "any_playbook_change": any_pb_change,
    }
    save_json(REPO / "scripts" / "merge_report.json", report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
