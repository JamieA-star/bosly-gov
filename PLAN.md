BOSLY GOV — PLAN
Last updated: 15 September 2026

================================================================
WHAT BOSLY GOV IS
================================================================

Bosly Gov is the custodian of the integrity of two production apps:
Bosly Accord and Bosly Keep. It exists so the founder can spend 30–60
minutes a day on maintenance rather than hours hunting for bugs.

Its job is to:

- Verify the constitution is being kept (encryption, privacy, ethical
  exclusion, crypto posture)
- Catch silent failures before users do
- Hold the whole picture
- Report only when something is wrong
- Document everything it does
- Evolve with the system
- Reduce its reliance on external LLMs over time

================================================================
THE TRUST CONTRACT
================================================================

Bosly Gov's relationship with the founder is governed by a trust
contract. This is not a feature. It is the rule that shapes every
other rule.

1. Nothing changes without explicit consent. Gov may investigate,
   propose, and explain freely. Gov may not modify files, run
   migrations, restart services, delete data, or change configuration
   without explicit approval of that specific action.

2. Consent is per-action, not per-session.

3. Gov teaches while it works.

4. Gov reports its own behaviour, including uncertainty.

5. Gov cannot evolve itself without consent.

6. Everything is logged and reversible.

7. Uncertainty means stop and ask, never guess.

8. Gov is honest about what it can't do.

Trust is learned, not assumed. Gov earns it incrementally. The
founder's trust grows as demonstrations accumulate.

================================================================
THE PROBLEM BEING SOLVED
================================================================

Twelve-plus silent bugs have been found across both apps in the last
ten days. The code looked like it worked and didn't. Examples:

- GBp currency conversion valued UK stocks 100x too high
- Ethical score-drop sell path never fired
- navigator.serviceWorker.ready hung forever without a registered worker
- Client/server payload shape mismatch returned silent 400s
- Dead UI code with state and handlers but no JSX
- NEXT_PUBLIC_* referenced in client code but never in the build bundle

Manual testing doesn't scale. Both apps are too big for one person to
hold in their head.

================================================================
THE ARCHITECTURE
================================================================

Three layers:

1. Project-local invariant tests. Small, fast, deterministic. Live in
   each repo. Catch the bug classes that have actually happened.

2. Central orchestration in Gov. Schedules, runs, aggregates, reports,
   alerts. Does not duplicate tests.

3. Constitution checks. The highest-value promise checks: encryption,
   privacy, ethical exclusion, crypto posture, quantum readiness,
   consent gating.

================================================================
WHAT EXISTS TODAY (15 SEPTEMBER 2026)
================================================================

Bosly Keep:
- scripts/diagnostics/verify-*.ts — 6 scripts, ~44 tests
- scripts/run-tests.sh — runner, runs typecheck then verify scripts
- npm test gated into deploy:keep
- This is the reference implementation.

Bosly Accord:
- NO invariant tests exist.
- scripts/accord-test.ts — training/scenario simulator, NOT a test
  runner. Runs 50 iterations, generates test data, calls LLMs.
- scripts/e2e-full-test.ts — E2E suite, runs at 4am daily.

Bosly Gov:
- Command routing (health, diagnose, audit, evolve)
- Memory files per project
- Context orchestration
- NO dedicated check runner.

Cron jobs already running:
- sync-email every 10 minutes
- backup daily at 3:00am
- monitor daily at 3:15am
- e2e-full-test daily at 4:00am

Existing tooling on the server:
- /usr/local/bin/bosly-audit — 1000-line bash script, 15+ sections
  of infrastructure checks. Takes ~10 minutes. Not scheduled.
- /usr/local/bin/bosly-monitor — daily monitoring script.
- /usr/local/bin/bosly-diagnose-v5.py, bosly-health, bosly-evolve,
  and others — manual-only.

================================================================
PHASE 1 — BUILD THE PIPELINE
================================================================

Goal: prove the pipeline works end to end with one invariant check.
Then add more.

[x] Step 1 — Create bosly-1.0/tests/invariants/ (flat, no
    subdirectories).

[x] Step 2 — Write env-public-vars.ts. Scan client code for
    process.env.NEXT_PUBLIC_* references, compare against
    .env.production and .env.example, fail if any referenced
    variable is missing from either.

[x] Step 3 — Write bosly-1.0/scripts/test-fast.ts. Find all
    tests/invariants/*.ts, run via npx tsx, aggregate results,
    exit non-zero on fail.

[x] Step 4 — Create bosly-gov-v4/manifests/checks.yml. One file
    listing both projects' fast-tier checks. Accord calls
    test-fast.ts, Keep calls run-tests.sh.

[x] Step 5 — Create bosly-gov-v4/runners/run_checks.py. Reads the
    manifest, runs each check, writes JSON reports to
    /mnt/bosly/bosly-data/reports/YYYY-MM-DD/, prints a summary.

[x] Step 6 — Test all of it manually. Prove the pipeline works.

[x] Step 7 — Add one cron entry: nightly at 5:00am.

[x] Step 8 — Add email-on-failure. Gov reads SMTP creds from
    .env.production, sends via Python's smtplib.

================================================================
WHAT COMES AFTER PHASE 1
================================================================

Phase 2 — Add more invariant checks. One per bug class:
- currency conversion
- ethical score drop
- service worker registration
- payload shape
- dead UI code
Each maps to a bug that has actually happened.

Phase 3 — Constitution checks. Encryption actually encrypts. Privacy
actually holds. Ethical exclusions actually enforced. These trace to
Trust document commitments.

Phase 4 — Drift checks. Crypto posture, dependency age, post-quantum
readiness. Slower cadence, weekly or monthly.

Phase 5 — LLM reduction. Track the ratio of memory-first to
LLM-fallback decisions. Trend it downward over time. Eventually run
core reasoning without external models.

================================================================
PHASE 2 — PROGRESS
================================================================

Add one invariant check per bug class. Each check maps to a bug
that has actually happened.

[x] gov.memory_schema (Gov) — memory files, well-formed items.
    Found 113 items in bosly-accord memory missing project_slug.
    Backfilled.

[x] keep.verify-fk-integrity (Keep) — every row referencing
    Asset.id points at a real asset.

[x] keep.verify-currency-pence (Keep) — GBp/GBX handling in
    toGBP and fromGBP. The bug that inflated UK stocks 100x.

[ ] accord.service_worker_registration — verify enableNotifications
    registers a worker before awaiting ready.

[ ] accord.payload_shape_contract — API routes accept the shape
    the client sends.

[ ] accord.dead_ui_wiring — named state and handlers are rendered.

[ ] keep.currency_gbp_shortcircuit — toGBP(x, "GBP") should not
    fetch live FX rates. Small refactor.

================================================================
WHAT NOT TO DO
================================================================

- Don't build a general-purpose testing framework. Keep it small.
- Don't make every check cross-repo. Project-local first.
- Don't start with expensive browser suites. Small deterministic
  tests first.
- Don't build dashboards before reports are solid.
- Don't invent a policy DSL. Manifests and plain scripts are enough.
- Don't make alerting noisy. Report only failures.

================================================================
FUTURE FEATURES
================================================================

Feature entries lock in principles. They do not specify
implementation. When build starts, read the principles first —
they are not negotiable.

----------------------------------------------------------------
feature.ai_receptionist
----------------------------------------------------------------

Type:       feature
Plan:       paid toggle (£50-75/mo)
Status:     FOUNDATION ONLY — not building yet
Blocked by: ICO registration, privacy policy update, telephony
            vendor decision.

Motivation:
  75% of UK small business owners say calls interrupt other work;
  ~40% lose up to 2 hrs/day to the phone. Real cost of a UK
  receptionist is roughly £35,046/yr. RingCentral AI Receptionist
  validated the market (3,000+ US businesses, UK launch Sept 2025).
  Strong fit for ADHD sole traders who lose work to unplanned calls.

PRINCIPLES (locked — must not be violated when built)
------------------------------------------------------

1. Zero-access encryption. Call recordings and transcripts are
   encrypted client-side. The server never sees plaintext. Same
   keystore and key ceremony as Accord — one trust model, not two.

2. No training on user data. Any third-party STT/TTS/LLM provider
   must be contractually excluded from using call data for training.
   If terms can't be guaranteed, use a provider that can, or run
   local.

3. Consent as a first-class object. Two consents, both logged:
     - Caller consent for recording (captured at call start)
     - Client consent for processing on their behalf (at setup)
   Stored via the existing consent flow, not a parallel system.

4. Client becomes a data controller. During setup, the client is
   explicitly told they are a controller and prompted to register
   with the ICO. Not optional. Not buried in a ToS.

5. Transparency by default. Callers are told they're speaking to an
   AI assistant, and that the call may be recorded, before any
   capture begins.

6. Retention is explicit and user-configurable. No silent "keep
   forever". Default retention stated in the UI, adjustable per
   workspace.

7. Deletion is complete. Every table with userId or ownerUserId is
   cleaned on account deletion. Extends the account-deletion fix
   from 28 Aug — not a new pattern.

8. One codebase, toggled per workspace. Feature flag
   ai_receptionist, off by default. No client-specific forks.

9. No hard dependency on a single telephony vendor. Abstract the
   telephony layer so the provider can be swapped without a
   rewrite.

FOUNDATION QUESTIONS (decide at build time — not now)
----------------------------------------------------

- Telephony: Twilio / Vonage / SIP / other?
- STT/TTS: local Whisper vs API? Training-exclusion terms verified?
- UK call recording: one-party or two-party consent for this use
  case, and how is it captured and evidenced?
- Number provisioning: per-workspace number, or shared pool with
  routing?
- Call storage: EBS path, encryption envelope, default retention?
- Cost model: does £50-75/mo cover telephony + STT + LLM at
  realistic call volumes, or does the toggle need a usage component?
- Onboarding: how is the client walked through ICO registration
  without it feeling like homework?

ACCEPTANCE (for when it's built)
--------------------------------

- Call answered when the client is busy or after hours
- Caller name, number, and reason captured
- Appointment booked directly into the client's calendar
- Summary delivered to the client's workspace
- All of the above with zero plaintext leaving the client, and all
  consents logged

OUT OF SCOPE FOR THE FOUNDATION ENTRY
-------------------------------------

- Choice of telephony vendor
- Choice of STT/TTS engine
- UI design
- Pricing tier finalisation (sketch exists in the blueprint)
- Number provisioning mechanics


================================================================
CURRENT STATUS
================================================================

Phase 1 COMPLETE as of 15 September 2026. Pipeline runs nightly at
5am. Alerts by email on failure, silent on success.

Phase 2 STARTED same day. Three fast-tier checks live:
  - accord.env_public_vars
  - keep.invariants (8 verify scripts, 65 tests)
  - gov.memory_schema

Total pipeline runtime ~9 seconds. Four Phase 2 checks still to
write; see PHASE 2 — PROGRESS above.

Next: write accord.service_worker_registration, the check that
would have caught the six stacked push notification bugs.

Next action: create tests/invariants/ and write env-public-vars.ts.

When a step is done, tick the box and update this section.
