# Policy playbooks (FortiGate)

This document describes the **00 - Policy Playbooks** collection and the **Policies** module included in the CloudOPS Proxmox pack: what each playbook does, prerequisites, and **post-import configuration** (config UUID replacement, policy-to-asset linking, and stale policy lifecycle).

## Contents

- **Policies** module – Stores firewall policy records synced from FortiGate (and used for SOC review).
- **00 - Policy Playbooks** – Import, review, and push comments back to FortiGate.
- **SOC Review** dashboard – Shows policies needing review (`reviewComplete` = false).

## Prerequisites

- **FortiGate connector** (**Fortinet FortiGate**) installed in FortiSOAR.
- At least one **connector configuration** pointing at your FortiGate (host, credentials).
- Connector version **5.4.0** recommended. The playbooks are aligned to 5.4.0’s `update_policy` params (no `action` or `status` for comment-only updates; the older 5.2.0 shape had those as optional empty keys).

## Post-import: config UUID replacement (required)

Several steps call the FortiGate API and are stored with a **placeholder config UUID** (e.g. `a18df41f-7370-42b3-b2c2-c21162eadd07`). Config UUIDs are **instance-specific**—you must point each step to your own connector and config.

**Steps:**

1. **> Update comments on Fortigate** – Edit the playbook, open **Update Comments on Policy**, set **Connector** and **Configuration** to your FortiGate.
2. **Review Policy** – Edit the playbook, open **Disable Policy on FortiGate**, set the same **Connector** and **Configuration** (used when the analyst selects **Mark as Denied**).
3. **Enable Policy** – Edit the playbook, open the **Enable Policy** step, set the same **Connector** and **Configuration**.
4. Save each playbook.

After this, comments and disable/enable actions will target the correct FortiGate.

## Playbooks


| Playbook                                      | Trigger                                      | What it does                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| --------------------------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Import Fortigate Policies**                 | Manual or schedule                           | Gets policies from the FortiGate connector and upserts them into the **Policies** module. Updates name, status, description, NAT, `reviewComplete`, `fortiGateSerial`, etc. After upsert, it calls **Link Policies to Firewall Assets by Serial**, computes stale policies for the current serial, and removes stale records while exposing the stale list in run output.                                                                                                                                                   |
| **PB_REF_LinkPolicyToFirewallAsset_BySerial** | Referenced by `Import Fortigate Policies`    | Finds the firewall Asset by `assets.serialNumber == policies.fortiGateSerial` (using the FortiGate serial from the current import run) and appends the matching Asset to each policy's `assets` relationship.                                                                                                                                                                                                                                                                                                               |
| **Archive Deleted Firewall Policies**         | Manual or schedule                           | Optional lifecycle playbook for environments that use soft-delete fields (`isDeletedOnFirewall`, `deletedDetectedAt`). Supports `retentionDays` and `dryRun`, prepares a visible archive list, and marks candidates as archived (`policyStatus = Archived`, `archivedAt`).                                                                                                                                                                                                                                                  |
| **Review Policy**                             | Manual (from Policies record)                | Presents a form for the SOC analyst: **Mark as Approved**, **Mark as Denied**, or **Email NOC team for additional input**. For **Mark as Denied**, runs **Disable Policy on FortiGate** (disables the policy and sets the comment), then stores the justification; for **Mark as Approved**, writes the justification to the record (which triggers **> Update comments on Fortigate**). After updating the record, runs **Refresh Firewall Policies** (re-runs Import Fortigate Policies) to sync state from the firewall. |
| **> Update comments on Fortigate**            | Field-based: `businessJustification` changed | Sends the policy’s **businessJustification** to the FortiGate as the policy comment, then marks the policy review complete (sets `reviewComplete`, `lastReviewedTime`, `nextReviewTime`, `auditStatus`).                                                                                                                                                                                                                                                                                                                    |
| **Enable Policy**                             | Manual (from Policies record)                | Enables a disabled firewall policy on FortiGate (`update_policy` with `status`: **Enable**), then runs **Refresh Firewall Policies** to re-import policies from the firewall.                                                                                                                                                                                                                                                                                                                                               |


## Mark as Denied and Refresh

- When the analyst selects **Mark as Denied**, **Review Policy** runs **Disable Policy on FortiGate** (FortiGate `update_policy` with `status`: `disable` and the analyst’s comment), then **Add justification to Policy Record**, then **Refresh Firewall Policies** (which runs the **Import Fortigate Policies** workflow to sync from the firewall).
- The **Refresh Firewall Policies** step in both **Review Policy** and **Enable Policy** references the **Import Fortigate Policies** workflow by UUID; no config change is needed for that step.

## Connector API (5.2.0 vs 5.4.0)

The **Update Comments on Policy** step uses the FortiGate connector’s **update_policy** with params suited to **5.4.0** (comment-only; no `action` or `status`). The **Disable Policy on FortiGate** step sends `status`: `disable` and `comment`; the **Enable Policy** playbook sends `status`: `Enable`. Connector **5.4.0** is recommended for all of these.

## Policy-to-Asset linking notes

- `Import Fortigate Policies` now stores `fortiGateSerial` on policy upsert and immediately calls the reference playbook `PB_REF_LinkPolicyToFirewallAsset_BySerial`.
- The reference playbook matches against **Asset field API key** `serialNumber` (label often shown as **Serial No**).
- If no Asset is found for the serial, no relationship is written.
- If multiple Assets match the same serial, the first returned record is used. For deterministic results, keep `serialNumber` unique for firewall assets.

## Stale policy lifecycle notes

- `Import Fortigate Policies` prepares a visible stale list (`Prepare Stale Policy Delete List`) before deleting stale policy records.
- Stale policy detection is scoped by current `fortiGateSerial` and compares existing `policyID` values against current imported policy IDs.
- If you prefer retention over immediate delete, use the optional `Archive Deleted Firewall Policies` playbook with soft-delete fields and a retention schedule.

## Recommended scheduler settings

Use these defaults for stable automated operation:

1. **Import Fortigate Policies**
  - **Enabled**: Yes
  - **Frequency**: Every `10` minutes (or `15` minutes for lower API load)
  - **Timeout**: Default
  - **Run mode**: Normal scheduled run
  - **Purpose**: Keep policy inventory current and apply linking/stale detection continuously.
2. **Archive Deleted Firewall Policies**
  - **Enabled**: Yes (after initial dry-run validation)
  - **Frequency**: Daily, off-hours (recommended `01:30` local time)
  - **Input params (recommended)**:
    - `retentionDays`: `30` (or `60`/`90` per policy)
    - `dryRun`: `true` for first 3-5 runs, then `false`
  - **Purpose**: Move long-stale deleted rules into archived state for retention governance.
3. **Operational guardrails**
  - Keep import schedule more frequent than archive schedule.
  - Do not run archive more than once per day unless required.
  - After changing retention days, monitor first run output (`Prepare Archive List`) before keeping changes.
  - If firewall API instability is observed, temporarily disable archive schedule and keep import schedule enabled.

## Global variable mode (recommended for scheduler runs)

Some FortiSOAR scheduler UIs do not expose playbook input params. In that case, configure retention via global variables:

- `policyArchiveDryRun` -> `true` or `false`
- `policyArchiveRetentionDays` -> `30`, `60`, or `90`

In playbook step **Set Retention Config**, use:

- `dry_run`
  - `{{globalVars.policyArchiveDryRun | default(true)}}`
- `retention_days`
  - `{{(globalVars.policyArchiveRetentionDays | default(30)) | int}}`
- `cutoff_ts`
  - `{{arrow.get().shift(days=-((globalVars.policyArchiveRetentionDays | default(30)) | int)).int_timestamp}}`

### Common error and fix

If you see:

- `bad operand type for unary -: 'str'`

then `policyArchiveRetentionDays` is stored as a string (for example `"60"`). Use the `| int` cast exactly as shown above in both `retention_days` and `cutoff_ts`.

## Import format notes

- In some FortiSOAR tenants, importing a single raw workflow JSON may show `The file type is invalid`.
- The playbook files in this repo are stored in `workflow_collections` wrapper format for compatibility with that import path.

## Related

- **README.md** – High-level pack overview and Policy playbooks pointer.
- **PACK_README.md** – Pack contents, installation, and the **Policy playbooks (FortiGate)** section (summary of this document).