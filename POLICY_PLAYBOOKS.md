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

The **> Update comments on Fortigate** playbook has a step **Update Comments on Policy** that calls the FortiGate API. That step is stored with a **placeholder config UUID** (e.g. `a18df41f-7370-42b3-b2c2-c21162eadd07`). Config UUIDs are **instance-specific**—they differ on every FortiSOAR deployment. You must point the step to your own connector and config.

**Steps:**

1. In FortiSOAR go to **Playbooks** → **00 - Policy Playbooks** → **> Update comments on Fortigate**.
2. Edit the playbook and open the **Update Comments on Policy** step.
3. Set **Connector** to your FortiGate connector and **Configuration** to the config that targets the firewall you want to update (the one whose policies you import and review).
4. Save the playbook.

After this, when a SOC analyst completes a review and adds a justification, the **> Update comments on Fortigate** playbook will push the comment to the correct FortiGate policy.

## Playbooks

| Playbook | Trigger | What it does |
|----------|---------|----------------|
| **Import Fortigate Policies** | Manual or schedule | Gets policies from the FortiGate connector and upserts them into the **Policies** module. Updates name, status, description, NAT, `reviewComplete`, etc. |
| **Review Policy** | Manual (from Policies record) | Presents a form for the SOC analyst to add comments and next steps (e.g. Mark as Approved, Email NOC). Writes to the policy record; when **businessJustification** is set, **> Update comments on Fortigate** is triggered automatically. |
| **> Update comments on Fortigate** | Field-based: `businessJustification` changed | Sends the policy’s **businessJustification** to the FortiGate as the policy comment, then marks the policy review complete (sets `reviewComplete`, `lastReviewedTime`, `nextReviewTime`, `auditStatus`). |

## Connector API (5.2.0 vs 5.4.0)

The **Update Comments on Policy** step uses the FortiGate connector’s **update_policy** operation with params suited to **5.4.0**:

- Params include: `comment`, `policyid`, `vdom`, and the usual address/service args; they do **not** include `action` or `status`.
- In connector **5.2.0**, the same operation could expose optional `action` and `status` (often sent empty for comment-only updates). In 5.4.0 those keys are omitted for this use case.

## Related

- **README.md** – High-level pack overview and Policy playbooks pointer.
- **PACK_README.md** – Pack contents, installation, and the **Policy playbooks (FortiGate)** section (summary of this document).
