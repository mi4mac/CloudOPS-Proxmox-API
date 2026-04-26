# FAZ Asset Ingest Production Runbook

This runbook hardens the following playbooks for production use:

- `Import FAZ Assets to FortiSOAR (Portable)`
- `Mark FAZ Duplicate Assets by DeviceUID`

## 1) Scheduling

- Start with an hourly schedule for 5-7 days.
- After baseline stability, tune to every 30-60 minutes.
- Stagger start time 5-15 minutes away from other heavy jobs.
- Watch runtime; if one run takes more than ~50% of interval, increase interval or reduce fetch limits.

## 2) Runtime scope

- Use one ADOM first via input `params.adom`.
- Keep traffic lookback at 1 hour for steady-state runs.
- Use larger windows only for controlled backfill runs.
- Pin the intended FortiAnalyzer connector config in production.

## 3) Failure handling and alerting

Alert on:

- any failed execution,
- zero fetched rows for N consecutive runs,
- sudden increase in `duplicate-candidate` tagged assets.

Track per run (in logs or summary variables):

- execution duration,
- managed devices processed,
- traffic rows fetched,
- assets created/updated (if counters are enabled).

## 4) Data hygiene

- Keep API keys and secrets only in credentials/vault, never in playbook JSON.
- Keep tags consistent: `faz`, `managed-device`, `observed-host`, `duplicate-candidate`, `faz-review`.
- Avoid writing oversized raw payload blobs unless explicitly needed.

## 5) Rollout test plan (before enabling scheduler)

1. Run import playbook manually once.
2. Spot-check 3-5 assets for expected fields:
   - `deviceUid`
   - `ip`
   - `macAddress`
   - `sourceData`
3. Run duplicate marker playbook once and review tagged records.
4. Run import again immediately; confirm no duplicate explosion.
5. Confirm changed network attributes (IP/MAC) still map to expected asset identity.
6. Enable scheduler only after steps 1-5 pass.

## 6) Rollback plan

1. Disable schedules for both playbooks.
2. Re-import last known-good playbook JSON files.
3. Review and clean `duplicate-candidate` tags before any delete operation.
4. Re-run manual validation before re-enabling schedules.

## 7) Day-2 operations

- Weekly: review duplicate-candidate queue and resolve.
- Monthly: re-check interval, limits, and FAZ API latency.
- After connector/FortiSOAR upgrades: re-run the rollout test plan once.

## 8) Current identity strategy

Identity is multi-VDOM aware and built around deterministic `deviceUid` values.

- Managed devices: `FortiAnalyzer|<adom>|<device-id>|<vdom>`
- Observed hosts: `FortiAnalyzer|<adom>|<devid>|<vdom>|<host-identifier>`

Host identifier fallback:

1. `srcmac`
2. `mastersrcmac`
3. `srcname`
4. `srcip`

## 9) Recent hardening updates

- Observed-host label normalization added in `Import FAZ Assets to FortiSOAR (Portable)`:
  - `name` and `hostname` are lowercased before write.
  - Purpose: prevent case-only duplicates (for example `MITC` vs `miTC`) when identity stays the same.
- New one-time cleanup helper added: `Mark FAZ Duplicates Keep Newest`.
  - Reads up to 5000 assets sorted by newest first (`$sort=-modifyDate`).
  - Keeps first record per `deviceUid` and tags older duplicates.
  - Applies non-destructive tags only: `duplicate-candidate`, `faz-review`, `keep-newest`.
- Temporary export workspace is now ignored by git:
  - `.tmp/service-mgmt-export/`
