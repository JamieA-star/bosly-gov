# Ops Commands Audit

Date: 19 September 2026

The `/usr/local/bin/bosly-*` scripts predate the mini PC
migration and the current Gov architecture. Almost everything
was created on 9 August 2026 — a single day's work. Most were
never scheduled, never referenced, and never run.

This audit categorises each script: keep, retire, or wrap as a
check. Retired scripts are moved to
`/usr/local/bin/bosly-legacy-archive/` so they stay recoverable
but out of PATH.

---

## Keep — live in crontab

| Script | Reason |
|---|---|
| `bosly-monitor` | Scheduled daily at 3:15am |
| `bosly-backup-full.sh` | Scheduled daily at 3am |

## Keep — used by the app

| Script | Reason |
|---|---|
| `bosly-analytics` | Called from the app |

## Keep — pending replacement

| Script | Reason |
|---|---|
| `bosly-evolve` | Function moves to `gov.evolve_loop` |

## Keep — useful, worth wiring in

| Script | Reason |
|---|---|
| `bosly-clean` | Disk analysis |
| `bosly-feedback` | Feedback reader — feeds `gov.evolve_loop` |
| `bosly-housekeep` | Server housekeeping |
| `bosly-lockdown` | Emergency freeze of write operations |
| `bosly` | Orientation command |

## Wrap as check

| Script | Reason | New check |
|---|---|---|
| `bosly-secrets` | Secrets audit — broken paths, useful intent | `gov.secrets_audit` |
| `bosly-smoke-test` | Critical path verification — overlaps pipeline | Review overlap |
| `bosly-journey-test` | E2E test — overlaps existing e2e | Review overlap |
---

## Retire

All scripts below are from the Gov v2–v5 iteration period, or
superseded by the current pipeline. Their function either no
longer exists or lives in the current Gov at
`/home/bosly_accord/bosly-gov/`.

| Script | Reason |
|---|---|
| `bosly-agent` | Gov v2 conversational agent |
| `bosly-agent-core.js` | Gov v2 fallback classifier |
| `bosly-accord-check` | Superseded by the pipeline |
| `bosly-anomaly-check.sh` | Claims daily cron — not scheduled |
| `bosly-attest` | Deploy attestation — no longer referenced |
| `bosly-audit` | Superseded by the pipeline |
| `bosly-backup` | Superseded by `bosly-backup-full.sh` |
| `bosly-build` | Component builder — superseded |
| `bosly-build-v2.py` | Component builder v2 — superseded |
| `bosly-build-v3.py` | Component builder v3 — superseded |
| `bosly-call-llm.py` | Gov v2 tool-calling |
| `bosly-configure` | Gov v4 configuration doctor |
| `bosly-diagnose` | Diagnose v1 — superseded |
| `bosly-diagnose-v4.py` | Diagnose v4 — superseded |
| `bosly-diagnose-v5.py` | Diagnose v5 — superseded |
| `bosly-extend` | Gov v4 schema extender |
| `bosly-health` | Superseded by pipeline + monitor |
| `bosly-health-ping.sh` | Claims 9am cron — not scheduled |
| `bosly-index` | Codebase manifest — superseded by orientation |
| `bosly-integrity-check.sh` | Superseded by pipeline |
| `bosly-intent` | Gov v4 intent checker |
| `bosly-legacy` | Old Gov launcher — already broken |
| `bosly-log-cleanup.sh` | Claims daily cron — not scheduled |
| `bosly-login-monitor.sh` | Claims 5-min cron — not scheduled |
| `bosly-memory.py` | Gov memory — now in `bosly-gov/` |
| `bosly-outbox-processor.sh` | Claims 30-sec cron — not scheduled |
| `bosly-patch` | Original precision patcher — pattern now used manually |
| `bosly-prompt.txt` | Old system prompt |
| `bosly-prompt-oneline.txt` | Old system prompt |
| `bosly-run.py` | Structured command exec — superseded |
| `bosly-schema-audit` | Superseded by pipeline |
| `bosly-tasks.sh` | Task queue — never scheduled |

Total: 32 scripts.

---

## Notes

- All scripts were created 2026-08-09, except: `bosly-analytics`
  and `bosly-monitor` (2026-08-15), `bosly-audit` (2026-09-15),
  and `bosly-legacy` (2026-08-08).
- Only 2 scripts in `/usr/local/bin/` are in the crontab:
  `bosly-monitor` and `bosly-backup-full.sh`.
- No user crontab, no `/etc/cron.d/bosly`, no systemd timers
  reference any of the "runs via cron" scripts.
- Retired scripts are moved to
  `/usr/local/bin/bosly-legacy-archive/` — recoverable, not
  deleted.
