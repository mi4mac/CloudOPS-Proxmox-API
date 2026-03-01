# Policy playbooks (FortiGate)

This document describes the **00 - Policy Playbooks** collection and the **Policies** module included in the CloudOPS Proxmox pack: what each playbook does, prerequisites, and **post-import configuration** (config UUID replacement).

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

| Playbook | Trigger | What it does |
|----------|---------|----------------|
| **Import Fortigate Policies** | Manual or schedule | Gets policies from the FortiGate connector and upserts them into the **Policies** module. Updates name, status, description, NAT, `reviewComplete`, etc. |
| **Review Policy** | Manual (from Policies record) | Presents a form for the SOC analyst: **Mark as Approved**, **Mark as Denied**, or **Email NOC team for additional input**. For **Mark as Denied**, runs **Disable Policy on FortiGate** (disables the policy and sets the comment), then stores the justification; for **Mark as Approved**, writes the justification to the record (which triggers **> Update comments on Fortigate**). After updating the record, runs **Refresh Firewall Policies** (re-runs Import Fortigate Policies) to sync state from the firewall. |
| **> Update comments on Fortigate** | Field-based: `businessJustification` changed | Sends the policy’s **businessJustification** to the FortiGate as the policy comment, then marks the policy review complete (sets `reviewComplete`, `lastReviewedTime`, `nextReviewTime`, `auditStatus`). |
| **Enable Policy** | Manual (from Policies record) | Enables a disabled firewall policy on FortiGate (`update_policy` with `status`: **Enable**), then runs **Refresh Firewall Policies** to re-import policies from the firewall. |

## Mark as Denied and Refresh

- When the analyst selects **Mark as Denied**, **Review Policy** runs **Disable Policy on FortiGate** (FortiGate `update_policy` with `status`: `disable` and the analyst’s comment), then **Add justification to Policy Record**, then **Refresh Firewall Policies** (which runs the **Import Fortigate Policies** workflow to sync from the firewall).
- The **Refresh Firewall Policies** step in both **Review Policy** and **Enable Policy** references the **Import Fortigate Policies** workflow by UUID; no config change is needed for that step.

## Connector API (5.2.0 vs 5.4.0)

The **Update Comments on Policy** step uses the FortiGate connector’s **update_policy** with params suited to **5.4.0** (comment-only; no `action` or `status`). The **Disable Policy on FortiGate** step sends `status`: `disable` and `comment`; the **Enable Policy** playbook sends `status`: `Enable`. Connector **5.4.0** is recommended for all of these.

## Related

- **README.md** – High-level pack overview and Policy playbooks pointer.
- **PACK_README.md** – Pack contents, installation, and the **Policy playbooks (FortiGate)** section (summary of this document).
