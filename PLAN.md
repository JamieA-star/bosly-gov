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

[x] accord.service_worker_registration — verify enableNotifications
    registers a worker before awaiting ready.

[x] accord.payload_shape_contract — API routes accept the shape
    the client sends.

[x] accord.dead_ui_wiring — named state and handlers are rendered.

[x] accord.typecheck_clean — npx tsc --noEmit should report 0
    errors. Currently reports 9 pre-existing errors across:
    components/VaultProvider.tsx (userId missing in context value),
    components/workspace/ActivePill.tsx (decrypt arg count),
    components/workspace/FinancePill.tsx (takenDate, setMsg),
    lib/chat/helpers.ts (reasoning_content not on ChatCompletionMessage
    — DeepSeek extension), lib/crypto/dataBridge.ts (phraseToEntropy
    not exported, deriveAESFromPhrase missing, BufferSource type).
    Build passes; these are type-safety gaps, not runtime bugs.
    Also: tsconfig.json now excludes backups/, which removed 13
    noise errors — keep that in place.

[x] accord.invoices_encryption — Invoice and InvoiceLineItem
    currently store financial data in plaintext. Requires schema
    migration (add encryptedData Json?), route hardening on
    /api/invoices POST/PATCH to reject plaintext, client encryption
    in InvoiceEditor.tsx, and update to the standalone /invoice
    tool. Also affects /api/invoices/[id] and the LLM system prompt
    schema block. Tracked as a known gap by
    no-plaintext-leaves-client. When done, move the entry from
    known_gaps into routes in route-contracts.yml with class
    "encrypted".

[ ] accord.spaces_encryption — Shared spaces (connected workspaces
    for organisations and individuals) is a future feature. The
    route exists and works, but stores names in plaintext. Not
    currently enforced because the feature isn't shipped.
    Status: DEFERRED in route-contracts.yml.
    When spaces is ready to ship, do the encryption (schema change,
    route hardening, client encryption), then move /api/spaces from
    `deferred` to `routes` with class `encrypted` in
    route-contracts.yml.

[ ] gov.evolve_loop - usage-driven and feedback-driven evolution.
    Two halves, both reports rather than checks. Neither belongs
    in the fast-tier pipeline. Both belong in Gov as separate
    commands with a slower cadence (weekly or monthly).

    HALF 1 - USAGE:
      Read the AnalyticsEvent table and produce a periodic
      digest. Which pills get opened? Which flows start but do
      not finish? Which features are being ignored? Where is the
      friction? Data source: AnalyticsEvent (already captured by
      pill tracking and the /api/analytics/track route).
      Output: a report. Suggested cadence: weekly.
      Motivated by: bosly-evolve, which did this from a bash
      script reading the same data.

    HALF 2 - FEEDBACK:
      Aggregate chatbot feedback (written to feedback.jsonl) and
      surface it for review. Which items are open? Which have
      been addressed? Close the loop by telling the user when
      their feedback led to a change. Data source:
      feedback.jsonl (already captured by the ChatDrawer
      feedback flow, fixed 16 Sept).
      Output: a report plus a small tracking store (open /
      addressed). Suggested cadence: weekly.

    DESIGN NOTES:
      - Do not put either half in the fast tier. They read
        usage data, they do not verify invariants.
      - The usage digest should not identify individual users.
        Aggregate only. Consistent with the transparency
        principle: the user should know what is being measured
        and why.
      - The feedback loop is a two-way street. If a user takes
        the time to report something, they should be able to
        see that it was received and whether it changed
        anything.

[ ] accord.unlogged_invoice_prompt — chat-driven replacement for
    the retired email scanner and invoice upload route. When the
    user asks "have I sent any invoices I haven't logged?", a thin
    server route reads the Sent folder and returns metadata only
    (subject, date, recipients — never the body). The browser
    asks which to log, opens the editor for each. No server-side
    parsing of content.

[ ] accord.follow_up_prompt — chat-driven replacement for the
    retired cards/schedule auto-follow-up. When the user asks
    "which invoices need chasing?", the browser identifies overdue
    invoices from decrypted data, prompts to send follow-ups, and
    builds the emails client-side. Same pattern as the send route.

[ ] accord.wellness_amount_check — client-side replacement for
    the "unusual invoice amounts" section removed from
    /api/bosly/wellness-check. The browser computes per-client
    averages from decrypted data and surfaces anomalies locally.

[ ] accord.email_relay_encryption — Option D for the email relay.
    Encrypt the email body client-side with a per-request
    throwaway key that the server decrypts in memory, uses for
    the SMTP call, and immediately discards. Server never holds a
    persistent view. Current state is Option B (documented
    transparently).

[x] gov.secrets_audit — check that .env.production is 600, no
    .env files in git-tracked directories, no secrets in PM2
    logs. Replaces the retired bosly-secrets script.

[x] ops.smoke_test_overlap — review bosly-smoke-test against the
    current pipeline. Keep what's not covered, retire the rest.

[ ] ops.monitor_runtime_checks — fold the runtime checks from
    bosly-smoke-test (app responding, security headers, PM2
    online, database reachable, page loads) into bosly-monitor.
    Retire bosly-smoke-test once done.

[ ] ops.journey_test_overlap — review bosly-journey-test against
    scripts/e2e-full-test.ts. Same treatment.

[x] ops.commands_cleanup — /usr/local/bin/ had 43 bosly-*
    commands from the August architecture. Most are pre-migration
    dead code. Audit each: keep, retire, or wrap as a check.
    Document the outcome. Note: bosly-audit, bosly-health,
    bosly-diagnose-v5 are superseded. bosly-monitor,
    bosly-analytics are kept. bosly-evolve is pending replacement
    (see gov.evolve_loop).

[ ] accord.legacy_js_audit — there is a substantial body of
    .js code tracked in the repo alongside the .ts/.tsx source:
    app/config/*.js, app/sw-client.js, lib/imap.js, lib/user.js,
    lib/social.js, lib/social/*.js, lib/inboxStore.js,
    lib/email/safeHeaders.js, components/*.tsx.js, plus
    app/robots.txt/route.js and app/sitemap.xml/route.js.
    Some may be live (imported from .ts files), some dead. The
    all-source-tracked check ignores .js, so this is invisible to
    the pipeline. Determine live vs. dead; remove if dead; migrate
    to .ts if live. Discovered 17 Sept 2026 during the
    all_source_tracked false-positive analysis.

[x] keep.payload_shape_contract — mirror of accord.payload_shape_contract.
    Assert every client fetch() that mutates sends the content-type
    and body the route expects. Deferred: Accord first, Keep once
    the Accord check has proven itself. See FUTURE FEATURES >
    feature.ai_receptionist for the pattern this class of bug
    belongs to.

[x] keep.currency_gbp_shortcircuit — toGBP(x, "GBP") should not
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


----------------------------------------------------------------
feature.voice_dumping
----------------------------------------------------------------

Type:       feature (small build)
Plan:       base plan (£25/mo) — input tool, feeds AI learning
Status:     planned — ready to schedule
Blocked by: decision on STT approach (browser vs server)

Motivation:
  Voice is the lowest-friction input for ADHD brains. The chat
  interface currently accepts typed text only — there is no
  voice capture. Making voice dumping a first-class input
  increases engagement with the chatbot, which increases memory
  density, which improves the AI learning engine. Same reason
  it stays in the base plan: more use = more data = smarter
  system.

WHAT IT ACTUALLY IS
-------------------

Greenfield. Voice capture does not currently exist in the chat.
Three pieces:

  1. Capture — a mic button in ChatDrawer that records speech
     and transcribes it into the existing input field
  2. Discoverability — users are told the chatbot accepts voice
     and what dumping is for
  3. Awareness — the chatbot's system prompt acknowledges voice
     input and responds to rambling rather than demanding
     structure

PRINCIPLES (locked — must not be violated)
------------------------------------------

1. No silent recording. Voice capture only happens when the
   user explicitly presses the mic. No always-on listening.

2. Zero-access where possible. If the server handles audio or
   transcripts, the provider must be contractually excluded
   from training, and any stored transcript goes through the
   existing encrypted chat path — not a parallel one.

3. Same trust model as Accord. Voice dumping uses existing
   chat memory and encryption.

4. Honest UI. The mic button says what it does. No pretending
   it's something else.

FOUNDATION QUESTIONS (decide at build time)
-------------------------------------------

- STT approach: browser Web Speech API (free, no server, Chrome
  and Safari only, lower accuracy) vs MediaRecorder + server
  Whisper (cost, privacy considerations, works everywhere)?
- Where does the mic button live — inside the input field, or
  next to send?
- Does a voice dump go straight to send, or does the transcript
  land in the input field for review before sending?
- Does the system prompt need a specific note about voice
  input, or is the existing "user may ramble" handling enough?

ACCEPTANCE (for when it's built)
--------------------------------

- A user can press a mic button, speak a rambling thought, and
  have it land in the chat as text without leaving the drawer
- The chatbot responds to a voice dump the same way it would
  to a typed one, without demanding structure
- Nothing about voice capture is hidden or surprising

OUT OF SCOPE
------------

- Separate voice UI (the chat is the UI)
- Wake words / always-on listening
- Bosly Voice (the stopped process) — unrelated
- Voice output / TTS responses


================================================================
TRANSPARENCY AS A FIRST-CLASS PRINCIPLE
================================================================

Locked 17 September 2026. Part of the Accord.

Every interaction with the LLM explains itself. Not as
boilerplate, not as a privacy disclaimer — as the way the
assistant speaks.

Three layers, adapted to context:

  1. What happened        "I've drafted the invoices."
  2. What I saw / didn't  "I can see there are 10. I can't
                          see who they are."
  3. Why                  "Because your data's encrypted on
                          your device."

The LLM composes the wording from facts and principles. The
facts are locked. The wording adapts. A first-time user gets
the full explanation. A familiar user gets a one-line
reminder. The truth never changes; the phrasing does.

WHY THIS IS THE USP
-------------------

Every AI assistant explains what it does. Almost none explain
how they work with your data. Bosly's model is the inverse of
the industry:

  - Industry: collect everything, explain nothing, hope
    nobody asks.
  - Bosly:    see nothing sensitive, explain everything,
              invite the awkward question.

The user doesn't just trust Bosly. They understand it.
Understanding is stickier than trust, because trust is a
feeling that can be shaken and understanding is a fact that
can't.

WHAT THE LLM CAN, CANNOT, AND WILL NOT DO
-----------------------------------------

The chatbot answers questions about itself honestly, in the
same voice it uses to work:

  CAN      - counts, statuses, dates, actions signalled to
             the browser, metadata.
  CANNOT   - client names, amounts, encrypted message bodies,
             health content, anything encrypted client-side.
  WILL NOT - soften the promise, invent capabilities,
             pretend to see data it can't, or hide behind
             vagueness.

If a user asks "what can you see?", the LLM answers plainly.
It never deflects. It never over-promises. It explains the
encryption model and how each interaction flows through the
browser.

APPLICATION
-----------

Applied feature-by-feature as each feature gets its encryption
pass. Invoicing is the first full instance (see the invoicing
implementation plan below). The pattern extends to: inbox,
calendar, health, finance, spaces, and any future feature.

  [ ] accord.transparency_in_llm_responses - once invoicing
      proves the pattern, audit every LLM interaction for
      compliance with this principle.


================================================================
accord.invoices_encryption - IMPLEMENTATION PLAN
================================================================

Status: designed 17 Sept 2026. Ready to execute.
Scope: two sessions - one to design (done), one to build.
Depends on: transparency principle, LLM conductor
principle (see memory).

CURRENT STATE
-------------

Invoice and InvoiceLineItem store financial data in plaintext:
  - Invoice: clientName, clientEmail, amount, taskDescription
  - InvoiceLineItem: description, quantity, unitPrice, total

The LLM was already blocked from seeing this data on 16 Sept
(tool schema + helper hardening). But the storage layer still
holds plaintext. Anyone with database access can read it.

Approximately 35 test invoices in the database. All test data
("Test Client", INV-001, £450). Safe to delete.
InvoiceLineItem table is empty (0 rows).

Tracked in route-contracts.yml as a known_gap. Once fixed,
move to routes with class: encrypted.

NEW SCHEMA
----------

model Invoice {
  id                  String   @id @default(cuid())
  userId              String
  user                User     @relation(fields: [userId], references: [id])
  invoiceNumber       String
  @@unique([userId, invoiceNumber])

  // Encrypted client-side. Contains:
  //   { clientName, clientEmail, amount, taskDescription,
  //     businessName?, lineItems: [
  //       { description, quantity, unitPrice, total }
  //     ] }
  encryptedData       Json?

  // Metadata - safe in plaintext
  currency            String   @default("GBP")
  issueDate           DateTime @default(now())
  dueDate             DateTime
  status              String   @default("draft")
  paidAt              DateTime?
  paymentInstructions String?
  taskId              String?
  sentAt              DateTime?
  createdAt           DateTime @default(now())
  updatedAt           DateTime @updatedAt
}

DELETED MODELS
  - InvoiceLineItem (line items live inside encryptedData.lineItems[])

DELETED COLUMNS on Invoice
  - clientName, clientEmail, amount, taskDescription

THE INVOICING FLOW (end to end)
-------------------------------

Batch flow, designed 17 Sept:

  1. User: "Bosly, September invoicing."
  2. Browser: decrypts contacts (hourlyRate) and calendar
     events (hours worked per client this month). Identifies
     clients with billable work not yet invoiced. Computes
     the count.
  3. Browser -> LLM: "10 clients have billable work."
  4. LLM: "You've got 10 clients needing invoices. I can't
     see their names or amounts - your data's encrypted on
     your device. But I can see there's work to do. Want me
     to draft them?"
  5. User: "Yes, do all 10."
  6. LLM: "No problem." [Full explanation first time. Brief
     reminder on subsequent runs.]
  7. Browser: for each client, computes line items
     (hours x hourlyRate), encrypts payload, POSTs to
     /api/invoices.
  8. LLM: "Done. 10 drafts in the finance section."
  9. User reviews and amends in the app.
 10. User: "I've checked them, send them all."
 11. LLM: "On it. The browser will build and send each
     email - I'm just relaying them, I never see the
     contents."
 12. Browser: for each invoice, decrypts, builds email HTML
     client-side, POSTs to /api/invoices/[id]/send with
     { to, subject, htmlBody, invoiceId }.
 13. Server: relays via SMTP, updates sentAt.
 14. LLM: "All 10 sent."

Single invoice flow is a subset: browser identifies one
client instead of ten.

ROUTE CHANGES
-------------

/api/invoices POST
  - Require encryptedData. Reject plaintext with 400.
  - Compute invoiceNumber server-side (metadata).
  - class: encrypted

/api/invoices GET
  - Return metadata + encryptedData.
  - class: encrypted

/api/invoices/[id] PATCH
  - Require encryptedData for content edits.
  - Allow metadata-only patches (status, dueDate) without.
  - class: encrypted

/api/invoices/[id]/send POST
  - Accept { to, subject, htmlBody, invoiceId }.
  - Server relays. Never inspects body content.
  - Updates invoice.sentAt.
  - class: metadata (relay only)

/api/invoices/[id]/paid POST   -> class: metadata
/api/invoices/[id]/delete POST -> class: metadata
/api/invoices/status GET       -> class: metadata

/api/invoices/draft-intent POST
  - Extend to accept batch: { clientIds?: string[], count?: number }
  - Signals browser to build drafts.
  - class: metadata

/api/invoices/suggestions GET
  - REWORK: move computation client-side, or return count only.
  - class: metadata

READ CONSUMERS TO UPDATE
------------------------

/api/briefing
  - Drop clientName, amount. Keep id, invoiceNumber, dueDate,
    status.

/api/bosly/briefing
  - Same fix.

/api/bosly/relationships
  - Currently selects clientName, amount for per-client stats.
  - REWORK: cannot compute server-side after encryption.
  - DECISION PENDING (Session 2)

/api/bosly/wellness-check
  - Has "unusual invoice amounts" section reading
    clientName, amount.
  - REWORK: drop section or move client-side.
  - DECISION PENDING (Session 2)

/api/finance/transactions
  - Reads paidInvoices with clientName, amount.
  - Likely drop financial fields. Verify what it uses.

/api/settings/export
  - Include encryptedData. User owns their export.
  - Note in export header explains encryption.

/api/user/delete
  - Just delete invoice (line-item table gone).

DELETE (dead code)
------------------

  - app/api/finance/invoices/route.ts
  - app/api/finance/invoices/[id]/route.ts
  - app/api/quickadd invoice branch

LLM SYSTEM PROMPT - NEW SECTION
-------------------------------

"Invoicing and the encryption model" - see transparency
principle. Fluid phrasing, locked facts.

CONTRACT FILE UPDATE
--------------------

route-contracts.yml:
  - Move /api/invoices from known_gaps to routes
    (class: encrypted)
  - Add /api/invoices/[id]/send (class: metadata)
  - Add /api/invoices/[id]/paid (class: metadata)
  - Add /api/invoices/[id]/delete (class: metadata)
  - Add /api/invoices/status (class: metadata)
  - Add /api/invoices/draft-intent (class: metadata)
  - Add /api/invoices/suggestions (class: metadata)
  - Remove /api/finance/invoices/* entries (dead)
  - Remove /api/quickadd invoice reference

Standalone /invoice tool:
  - New class: standalone
  - Note: "Unauthenticated lead magnet. Not encrypted.
    User data stays in their browser. If they want
    encryption and zero-access, they sign up to Accord."

ORDER OF EXECUTION (Session 2)
------------------------------

  1. Delete dead code
  2. Schema migration (backup DB first, delete 35 test
     invoices, db push, regenerate Prisma client)
  3. Route changes
  4. Client changes
  5. LLM system prompt update
  6. Contract file update
  7. Re-run checks (no-plaintext-leaves-client should pass,
     0 failures, 0 known gaps)
  8. Manual test (create -> check DB -> reload -> send)
  9. Commit in layers

OPEN DECISIONS FOR SESSION 2
----------------------------

  - /api/bosly/relationships
  - /api/bosly/wellness-check
  - /api/invoices/suggestions

Decided with the code open, not on paper.


================================================================
OPS COMMANDS vs PIPELINE
================================================================

Six /usr/local/bin/ scripts predate Bosly Gov's check pipeline.
Status assessment, 17 September 2026.

  bosly-audit         SUPERSEDED by the check pipeline. Retire
                      after the pipeline has run reliably for a
                      fortnight. 1000 lines of bash doing what
                      nine TypeScript checks now do faster and
                      with structured reports.

  bosly-monitor       KEPT. Runtime health - disk, memory,
                      process, API. Different job to the
                      pipeline. Runs at 3:15am, unchanged.

  bosly-health        SUPERSEDED. Retire with bosly-audit.

  bosly-diagnose-v5   SUPERSEDED or wrap-as-check. Retire when
                      we have confirmed nothing is lost.

  bosly-analytics     KEPT. Aggregates usage events. Not a
                      check. Becomes input to the evolve loop.

  bosly-evolve        PENDING REPLACEMENT. Two halves -
                      usage-driven evolution and feedback-driven
                      evolution. Neither is a check. Both belong
                      in Gov as reports, not in the fast-tier
                      pipeline. See gov.evolve_loop below.

Retirement is by neglect - the scripts stay on disk but stop
being referenced or run. When the replacement lands, remove.

Note: none of these commands were being used regularly, because
they had to be run manually. The pipeline runs automatically at
5am. That alone justifies the transition.

================================================================
CURRENT STATUS
================================================================

Phase 1 COMPLETE (15 Sept 2026). Pipeline runs nightly at 5am.
Alerts by email on failure, silent on success.

Phase 2 COMPLETE. Phase 3 COMPLETE. Phase 4 IN PROGRESS.

Fast-tier checks live (5, all passing, ~15s total):
  - accord.invariants - 8 sub-checks:
      env vars, service-worker guards, payload shape contract,
      LLM-financial-data leak, route referential integrity,
      no-plaintext-leaves-client, LLM prompt route refs,
      all source tracked
  - keep.invariants - verify scripts + ethical exclusions +
    payload shape contract + 65 tests
  - gov.memory_schema
  - gov.consent_gating (severity: critical)
  - gov.secrets_audit (severity: high)

Constitution checks COMPLETE:
  - LLM never sees financial data (verified)
  - Keep ethical exclusions enforced (verified)
  - Gov never writes without consent (verified, critical)
  - No plaintext leaves client (verified for enforced routes)
  - Secrets not exposed (verified)

Invoice encryption migration COMPLETE (18 Sept 2026).
Five phases: schema, routes, client, LLM prompt, contract.
Only /api/spaces remains a known gap.

Operational tooling COMPLETE:
  - /usr/local/bin/bosly - orientation command
  - WORKING_AGREEMENT.md - how we work
  - docs/OPS_COMMANDS_AUDIT.md - 43 scripts audited
  - memory cleaned: 216 to 103 items

Session 18-19 Sept 2026:
  - Full invoice encryption migration
  - Orientation command built
  - Working agreement written
  - Memory cleaned and standardised
  - 32 legacy scripts retired
  - gov.secrets_audit added

Next: accord.spaces_encryption - same pattern as invoices,
smaller surface. Then gov.evolve_loop. Manual invoice test
pending (create, verify DB, reload, send, mark paid).

When a step is done, tick the box and update this section.

================================================================
MEMORY UPDATES
================================================================

2026-09-16: memory entries written during the session.

  bosly-accord:
    - incident-20260916-llm-financial-leak-three-layers
    - decision-20260916-llm-is-conductor-not-bookkeeper
    - pattern-20260916-tsconfig-excludes-before-typecheck
    - pattern-20260916-read-code-not-comments

  bosly-gov:
    - pattern-20260916-new-checks-need-calibration
    - fact-20260916-invariant-glob-asymmetry
    - fact-20260916-layer3-alongside-layer1

Read these before working on: LLM chat features, new invariant
checks, or any audit that verifies a promise.

2026-09-16 (continued): more entries.

  bosly-gov:
    - pattern-20260916-note-pattern-in-checks

2026-09-16 (continued): three more entries from the route work.

  bosly-accord:
    - pattern-20260916-parent-route-forgotten
    - pattern-20260916-missing-route-or-dead-code
    - pattern-20260916-read-write-path-drift

2026-09-17: six entries written during the design session.

  bosly-gov:
    - pattern-20260917-environment-fragility-family
    - pattern-20260917-design-before-build-migrations
    - pattern-20260917-read-consumer-audit

  bosly-accord:
    - fact-20260917-env-loading-set-a-source
    - pattern-20260917-dead-routes-in-prompts
    - pattern-20260917-parser-dead-code

[x] accord.llm_prompt_route_refs — scan app/api/chat/route.ts
    and lib/chat/ for /api/... path references. Assert each
    points to a route that exists. Same class as
    route-referential-integrity but for prompt strings rather
    than fetch calls. Motivated by /api/quickadd remaining in
    the tool schema after the route was deleted (17 Sept).


2026-09-17 (continued): accord.all_source_tracked written.

  [x] accord.all_source_tracked — every .ts/.tsx in app/,
      components/, lib/, types/ is tracked by git. Written
      after discovering types/pill.ts and types/social.ts had
      never been committed (a "types/" line in .gitignore was
      silently excluding them). Now in the pipeline as the 9th
      sub-check of accord.invariants.

2026-09-17 (continued): four entries written after the light session.

  bosly-accord:
    - pattern-20260917-gitignore-substring-trap
    - pattern-20260917-dead-files-import-deleted-modules

  bosly-gov:
    - pattern-20260917-source-file-hygiene
    - fact-20260917-tscheck-diagnostic-order

2026-09-17 (continued): two entries about the evolve loop.

  bosly-gov:
    - fact-20260917-evolve-is-not-superseded
    - fact-20260917-command-word-status

2026-09-18 (continued): memory hygiene cleanup.

  bosly-accord: deleted 114 legacy session-transcript entries
    (from the pre-format consolidator). Kept 20 standard entries.

  bosly-gov: renamed 2 principle- entries to decision-.
    Deleted 1 stale gap- entry (already fixed).

  bosly-keep: renamed 13 seed- entries to fact-20260901-seed-*
    so they fit the convention and sort as baseline knowledge.

  Backups: memory.json.bak-20260918 in each slug directory.

2026-09-18 (continued):

  [x] ops.working_agreement — WORKING_AGREEMENT.md
  [x] ops.orientation_command — /usr/local/bin/bosly

  Memory cleanup finished:
    - bosly-accord: 114 legacy entries deleted (20 kept)
    - bosly-gov: 2 principle- renamed to decision-, 1 stale
      gap- deleted
    - bosly-keep: 9 seed- renamed, 1 gap- deleted, 2 principle-
      renamed, 1 requirement- renamed

  All memory files now use standard prefixes only.
