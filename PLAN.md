BOSLY GOV — PLAN
Last updated: 26 September 2026 (evening — Friday prep)

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

[~] accord.typecheck_clean — UPDATED 3 Oct. tsc reports 0 errors,
    but over a partial codebase. tsconfig.json has sixteen
    `exclude` entries, several whole directories. Two of them —
    lib/calendar/providers/** and app/api/calendar/icloud/** —
    contained live code that had never compiled and never
    worked (sixteen errors, including session.user on a session
    that has no such field, and three schema fields that do not
    exist). Both excludes are now removed and those files are
    fixed. The other excludes have not been audited.

    The gap: tsc cannot tell "excluded because legacy" from
    "excluded because it had errors". A check should report
    which excluded directories contain live imports, so an
    exclusion of live code is visible rather than silent.
    See gov.tsconfig_excludes.

[~] gov.tsconfig_excludes — BUILT 3 Oct, report-only. checks/
    tsconfig_excludes.py lists every excluded tsconfig directory
    containing source, except a deliberate-list.

    First run: 3 flagged of 21 — app/api/spaces/**,
    app/api/connect/google/**, app/api/inbox/webhooks/sms/**.
    Un-excluding revealed 28 errors. Excludes restored; the
    three directories are unfixed.

    REGISTERED 3 Oct in manifests/checks.yml. Severity high.

    Original entry follows.
    A check that reads
    tsconfig.json's `exclude` list and, for each excluded
    directory, reports whether any live file imports from it.
    An exclusion of live code should be visible, not silent.

    Argument, 3 Oct. Two excluded directories (the iCloud
    calendar routes and provider) contained code that had
    never compiled and never worked. tsc said "0 errors"
    throughout, because it was not looking. Same shape as the
    Stripe webhook being redirected by middleware: a check that
    passes while the thing it describes is broken.

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

[x] accord.ceremony_interrupt_safety — DONE 21 Sept. Committed 2b1df67. The key ceremony could be closed mid-flight between generateKeys() and storeKeys(), losing the phrase permanently. Added a disclaimer sub-step before display, sessionStorage stash, and a resume UI. See pattern-20260921-plumbing-without-taps (this is the inverse: a vulnerability that had no check).

[x] accord.server_side_key_visibility — DONE 21 Sept. Committed 2219b73. The client was sending the exported AES key to /api/auth/update-key. Nothing read it server-side. Removed from signup and recovery. Route now accepts all fields as optional. The zero-access claim is true: the server never sees key material. The User.publicKey DB column still exists but new users get null.

[ ] [GATED] accord.spaces_encryption — UPDATE 3 Oct: the routes
    (app/api/spaces/**) are archived to legacy/api-dead-20261003/
    spaces/. They used three Prisma models (sharedSpace,
    spaceMember, sharedSpaceMember) that are not in
    schema.prisma, so they never compiled or ran — the directory
    was excluded from tsconfig, which hid it. When the feature
    ships, restore the routes with the schema.

    Original entry follows.
    Shared spaces (connected workspaces
    for organisations and individuals) is a future feature. The
    route exists and works, but stores names in plaintext. Not
    currently enforced because the feature isn't shipped.
    Status: DEFERRED in route-contracts.yml.
    When spaces is ready to ship, do the encryption (schema change,
    route hardening, client encryption), then move /api/spaces from
    `deferred` to `routes` with class `encrypted` in
    route-contracts.yml.

[x] accord.analytics_event_scope — DONE 21 Sept. prisma/schema.prisma now documents that AnalyticsEvent is marketing/lead-magnet analytics and UsageEvent is product usage. The two are distinct; the plan previously conflated them. clarify in code comments
    and the plan that AnalyticsEvent captures the standalone
    /invoice lead-magnet, NOT product usage. Product usage
    goes through UsageEvent. Two tables, two purposes. Named
    to prevent future confusion.

[x] accord.crypto_fix_1_rename_types — DONE 21 Sept. Committed 093ae57. Rename the crypto types
    and fields to stop lying about X25519. In lib/crypto/types.ts:
    drop KeyPair, replace with VaultKeyMaterial (one field for the
    base64 AES key). Rename StoredKeyMaterial.encryptedX25519Private
    Key to recoveryPhrase. Rename every caller. Verify: tsc --noEmit
    surfaces every call site — that list is the file-touch
    checklist for the following items.

[x] accord.crypto_fix_2_generatekeys_shape — DONE 21 Sept. Absorbed into crypto_fix_1 (the rename included the generateKeys() shape). Fix generateKeys() in
    lib/crypto/keygen.ts to return a symmetric key descriptor, not a
    fake keypair. Remove x25519PublicKey/x25519KeyPair fields. Keep
    deriveAESFromEntropy and deriveAESFromPhrase untouched — they
    are correct. Verify: manual call in a scratch script, confirm
    deriveAESFromEntropy(entropy) reproduces the same key bytes.

[x] accord.crypto_fix_3_recovery_path — DONE 21 Sept. Committed c4985bd. Invariant crypto_recovery_roundtrip passes. Fix app/signin/recover/
    page.tsx to call deriveAESFromPhrase() instead of the stub
    reconstructKeys(). Write the phrase itself (not a hash) into
    the renamed field, matching exactly what app/signup/keys/page.tsx
    writes at signup. Delete reconstructKeys() entirely from
    lib/crypto/keygen.ts. Verify: full phrase -> recover -> same key
    round trip (see accord.crypto_recovery_roundtrip invariant).

[x] accord.crypto_fix_4_update_key_contract — DONE 21 Sept. Committed 629cee7 (API rename) + 2219b73 (server-side key visibility fix). Fix app/api/auth/
    update-key/route.ts AND app/api/auth/key-backup/route.ts to
    stop requiring a "publicKey" field that nothing legitimate
    generates. The key-backup route currently returns 400 if
    publicKey is missing — that will break when Step 2 stops
    producing one. Grep the Prisma schema and any route reading
    User.publicKey before deciding what to persist. Verify:
    signup completes, both routes return 200, DB row inspected.

[x] accord.crypto_fix_5_remaining_callers — DONE 21 Sept. Zero remaining references found; absorbed into crypto_fix_1 and crypto_fix_4. Fix remaining readers
    of the old field names: components/VaultProvider.tsx (boot and
    recoverFromBackup), lib/crypto/dataBridge.ts (the includes(' ')
    check that discriminates phrase vs hex), components/MailKey
    AutoUnlock.tsx (scans all IndexedDB records). Verify: repo-wide
    grep for encryptedX25519PrivateKey / x25519PublicKey /
    x25519PrivateKey returns zero hits outside intentional
    back-compat.

    Migration note (21 Sept): both existing test accounts
    (jr-arnott@outlook.com, jarmario85@hotmail.co.uk) were
    DELETED on 21 Sept. When crypto_fix_1-3 land, the founder
    will sign up FRESH with the corrected flow and test end
    to end. No data migration is needed — there is no live
    user data to migrate. This is the test case for the fix.

[x] accord.crypto_fix_6_regression — DONE 24 Sept. Browser test completed end to end. Four flows: fresh signup → workspace → create contact → reload; sign out → sign back in; delete account; export data. All worked. Found two real UX bugs in the process, both fixed same day: (a) browser didn't offer to save the account password (missing autoComplete="new-password"); (b) the ceremony and vault reminders said 'Face ID recovery' when Bosly does no Face ID check — the PIN is what decrypts the backup. Both tracked separately.
    Four flows: (a) signup -> reload -> decrypts; (b)
    signup -> signout -> signin -> decrypts; (c) signup ->
    clear IndexedDB -> recover with phrase -> decrypts;
    (d) PIN backup recovery. Do this before 3 Oct. Run four flows end to end:
    (a) fresh signup -> reload -> data decrypts; (b) signup -> sign
    out -> normal signin -> data decrypts; (c) signup -> clear
    IndexedDB -> /signin/recover with phrase -> data decrypts;
    (d) PIN-backup recovery (recoverFromBackup) still works.
    Copilot-estimated 2-4 focused days total for steps 1-6.

[x] accord.user_deletion_cascade — DONE 21 Sept. Committed 674da01. Wrapped in $transaction; 13 missing tables added; failures now return errors instead of { ok: true }. The in-app delete route
    (app/api/user/delete/route.ts) attempts to delete from 35
    of the 40 tables that reference User(id). It misses:
    MemoryFact, DataHealthFinding, DataHealthScanRun,
    DataHealthSectionState, DataHealthSnapshot,
    MonitoredIdentity, ActivityEvent, CreditReportReminder.
    It also wraps each delete in an individual try/catch, so if
    any fail — including the final user.delete — the route
    still returns { ok: true }. Consequence: a user with a
    MemoryFact row who hits "delete account" sees success,
    gets logged out, and their data remains in the database.
    Found 21 Sept while trying to delete two test accounts
    manually. Fix: (a) add missing tables; (b) wrap the whole
    delete in prisma.$transaction(); (c) if the transaction
    fails, return an error; (d) prefer schema-driven cascade
    over a manual table list. Before the 3 Oct reel.

[x] accord.delete_route_coverage — DONE 21 Sept. Committed 674da01 as tests/invariants/delete-route-coverage.ts. Parses schema.prisma and the delete route, asserts every model with userId/ownerUserId is deleted. Currently PASSES. Gov check: every Prisma
    model with a userId or ownerUserId field must appear in
    the delete route's table list. Parses prisma/schema.prisma
    and app/api/user/delete/route.ts, diffs the sets, fails on
    any missing model. Fast-tier viable. Would have caught the
    eight missing tables found on 21 Sept. Motivates and
    supports accord.user_deletion_cascade.

[x] accord.crypto_recovery_roundtrip — DONE 21 Sept. Committed 5a3aba0 as tests/invariants/crypto-recovery-roundtrip.ts. Encrypts with signup-derived key, recovers via phrase, asserts byte identity. Currently PASSES. Invariant test in
    tests/invariants/. Encrypt known plaintext with the signup-
    derived AES key. Discard the key. Recover using only the
    24-word phrase via whatever path app/signin/recover uses.
    Decrypt. Assert plaintext matches, assert raw bytes of both
    keys are identical. File written 21 Sept; fails until step 3
    lands.

[x] accord.naming_honesty — DONE 26 Sept. Shipped as
    gov.naming_honesty, a fast-tier Gov check. Three rules:
    (A) Prisma schema fields matching /^encrypted[A-Z]/ whose
    name mentions a specific crypto primitive (X25519, RSA,
    ECDH, ChaCha) fail if that primitive is not used in
    lib/crypto/. (B) Source comments containing an admission
    phrase ('was a lie', 'actually stores', 'misnamed', etc.)
    fail unless allowlisted. (C) Interface fields ending in a
    primitive name fail if the same file contains no other
    reference to it. Allowlist has two entries, both the
    historical comments in lib/crypto/types.ts left after the
    21 Sept rename. Current result: 0 findings, 2 allowlist
    hits. Motivated by the 21 Sept rename (a field named for
    X25519 held the plaintext BIP39 recovery phrase) and by
    pattern-20260924-accord-vs-code-drift. Companion to
    gov.stub_detection. Original design note: flag any field
    or type whose name asserts a crypto primitive the code
    does not use. E.g. encryptedX* where the value is
    plaintext, x25519* where the value is AES. Cheap grep +
    type inspection. Fast tier candidate.

[ ] [LIVE] ops.founding_member_offer — The 2 Oct founding member
    ask goes out Friday. The offer is a Stripe promotion code
    (40% off, duration forever, max 21 redemptions — 20 for the
    post, 1 reserved for the founder's end-to-end test).

    Status as of 27 Sept:
      - Coupon created in Stripe: 40% off, duration forever. DONE.
      - Promotion code FOUNDER40 created: max redemptions 21. DONE.
      - Reel rewritten. The stale "free AI features for life" and
        "for life" language is gone; the reel now promises only
        what is true (20 spots, £15/mo instead of £25, feedback
        in exchange for a seat). DONE.
      - Publish-vs-private decided: PRIVATE. The code is not
        published on the site or in the post. It is sent only to
        people who comment IN or DM. The pinned comment keeps the
        fit framing ("I'd rather fill these with people who'll
        tell me what's broken than with whoever gets here
        first"). DONE.
      - End-to-end test: PASSED 2 Oct. Fresh signup, upgrade,
        FOUNDER40 applied, £15 confirmed (not £25), payment
        returned to the app, and every pill opened. Run once
        plain and once with the code.

    ACTION BEFORE POSTING: confirm the FOUNDER40 redemption
    count in Stripe. The cap is 21, reserved as 20 public + 1
    test. More than one test has now run. If the remaining
    count is not 20, either the post's number changes or the
    cap is raised. The post must state what is actually true.


[ ] [LIVE] accord.user_docs_prose_pass — Apply the new
    WORKING_AGREEMENT rule ("Writing for the reader") to the
    existing user-facing documents. The rule: no hash headers,
    no bullet dots, no lists pretending to be sentences.
    Written as paragraphs instead.

    Documents that need the pass:
      - app/(marketing)/safety/page.tsx — sections with
        bullet lists for what Bosly does and doesn't do.
      - app/(marketing)/terms/page.tsx if it exists — same
        check.
      - public/llms.txt and public/llms-full.txt — machine
        readable, but read by people too.
      - Any other page under app/(marketing)/.

    The privacy page is partly done (six edits on 26 Sept)
    but should be re-read against the rule.

    Internal documents (PLAN.md, WORKING_AGREEMENT.md,
    NOTES.md, memory) keep their structure. The rule is
    about the reader, not the writer.

    Estimate: 1-2 sessions depending on how deep the Accord
    edits go. The Accord is a constitution, not a brochure —
    some of its structure is load-bearing and should be
    preserved. Only the sections that read like a machine
    wrote them get rewritten.

[ ] [LIVE] accord.social_render_pipeline — The real social media
    image renderer is broken/corrupted. lib/social/render.ts
    currently exports a placeholder (renderSocialMediaImage
    returns a 1x1 transparent PNG; renderVariants returns
    placeholder variants) so that Next.js builds stay green.
    The comment at render.ts:27 says so explicitly. Nothing
    renders a real image; every social post that expects a
    rendered image gets the placeholder.
    Two decisions:
      (1) Restore the real renderer. It was working before it
          was corrupted; git history will have it.
      (2) Or accept the placeholder as the current state,
          document it in the Accord's Part III, and remove
          any user-facing claim that social posts render
          images.
    Allowlisted in gov.plan_tracks_known_gaps until resolved
    (see ALLOWLIST in checks/plan_tracks_known_gaps.py).
    Estimate: 1-2 sessions depending on whether the render
    pipeline is recovered from git or rebuilt.

[x] accord.stub_detection — DONE 26 Sept. Shipped as
    gov.stub_detection, a fast-tier Gov check. Flags any
    function whose name implies production capability
    (reconstruct, derive, generate, render, extract, parse,
    fetch, encrypt, decrypt, send, build, request) and whose
    body or adjacent comments admit it is a stub (stub,
    placeholder, TODO, FIXME, not implemented). Only fails
    when the function is called from live code — dead stubs
    are NOTEd, not failed. Three documented stubs allowlisted
    (the two workflow bridges and the social renderer).
    Calibration: 'for now' was in the admission list on the
    first draft and produced three false positives on working
    functions (sessionKeyStore, messageEncryption); removed.
    Current result: 0 failures, 2 notes. Motivated by the
    deletion of lib/inboxStore.js (24 Sept) and the dead
    mailparser block in the old enrich-contacts route.
    Original design note: flag any function whose body
    contains 'stub', 'placeholder', 'TODO', or 'not
    implemented', AND whose name suggests production
    capability (reconstruct*, derive*, generate*). Medium
    complexity. Fast tier candidate with calibration.

[x] accord.plaintext_message_fallback — DONE 26 Sept. The
    decision: document it, don't fix it today. The real fix
    is accord.inbox_pill_encryption, which moves message
    encryption to the client. Work done:

      - lib/email/messageEncryption.ts comment reworded. The
        old "for now" was a lie: the session key store is
        in-memory, so the fallback fires on every server
        restart, not only for users who haven't done ceremony.
      - docs/ACCORD.md Part III got a new section 3.3
        "Conditional encryption" naming the exception
        honestly. Part III used to be two categories
        (encrypted / plaintext-with-migration-planned);
        messageText was neither.
      - app/(marketing)/privacy/page.tsx got six corrections.
        The page described a Civo integration that no longer
        exists, and said communication data is "stored
        encrypted" when it's only encrypted while a session
        key is loaded.
      - WORKING_AGREEMENT.md got a "Writing for the reader"
        section: user-facing docs read as prose, internal
        docs keep their structure.

    Found 26 Sept by gov.stub_detection, which correctly did
    NOT flag the function as a stub but surfaced the comment.
    Related: accord.encrypt_all_pills, accord.inbox_pill_
    encryption, accord.user_docs_prose_pass.

[x] gov.plan_tracks_known_gaps — DONE 26 Sept. Shipped as
    gov.plan_tracks_known_gaps, a fast-tier Gov check. Scans
    source comments (//, /*, and JSDoc * lines only — string
    literals are skipped) for admission phrases ('this is
    broken', 'known bug', 'known issue', 'known limitation',
    "doesn't work", 'does not work', "won't work", 'will not
    work', 'broken since'). For each admission, checks whether
    the enclosing file is mentioned in PLAN.md or memory.json.
    If not, FAILS. Current result: 1 admission found
    (lib/social/render.ts:27), allowlisted. That admission is
    now tracked as accord.social_render_pipeline (added same
    day). Calibration: 'stub' is deliberately NOT in the
    admission list — gov.stub_detection owns that class.
    Motivated by VaultProvider.tsx:94 which acknowledged bug #3
    in a comment and was never tracked.
    Original design note: scan all source comments for phrases
    like 'this is broken', 'known bug', "doesn't work", 'stub',
    and cross-reference against PLAN.md and memory. Any
    acknowledgment in code that isn't tracked as an open plan
    item or a memory entry fails. Fast tier.

[x] accord.encryption_honesty_review — DONE 21 Sept. Committed 94e5e45. All encryption claims now true; three copy fixes (signup 'one step', landing 'free to use', notifications optional). Read the key ceremony copy
    in app/signup/keys/page.tsx and the landing copy in app/
    page.tsx. List every claim about encryption ("zero-access",
    "only you hold the keys", "encrypted"). Decide per claim:
    keep (provable), soften (not yet true), or remove. Currently
    can be resolved as "keep" IF the crypto_fix items land before
    3 Oct — otherwise soften to "your data is encrypted on your
    device before it reaches us". Do before the founding members
    reel.

[x] accord.beta_onboarding_simplification — DONE 21 Sept. The /onboarding/activate and /onboarding/success pages were dead code (nothing routed to them). Archived to legacy/onboarding/. The live upgrade path is BillingSettings.tsx -> /api/billing/checkout. For the 3 Oct
    launch: (a) delete app/onboarding/activate/page.tsx from
    the signup flow — the free tier is real, the £25 chatbot
    paywall is contextual; (b) make the key ceremony survive a
    tab close, or warn the user explicitly; (c) reframe the
    ceremony as the value moment; (d) update landing page copy
    to say free tier + £25 for chatbot and Social pill.

[x] ops.gov_copilot_teaching_loop — DONE 21 Sept. Added a Teaching Loop section to WORKING_AGREEMENT.md: Gov's Copilot improves the more it is used. Its file-reading, interaction log, and accumulated context are the mechanism. Session context (plans, memory, checks) feeds back as source of truth. The long-term direction is reducing reliance on external LLMs by building internal context. Bosly Gov's Copilot
    (via the terminal or the localhost UI) improves the more it
    is used. Every prompt sent to it, every response it
    produces, is a teaching moment. The workflow is: founder
    runs a terminal command containing the prompt, Gov's
    Copilot reasons and responds, founder pastes the response
    into the ongoing chat. This is deliberate, not incidental
    — Gov is meant to be learned from, not just queried. Any
    session that uses Gov's Copilot should note what was
    learned and whether it changed a decision.

[x] ops.working_agreement_workflow_doc — DONE 21 Sept. Added a Workflow section to WORKING_AGREEMENT.md: founder brings terminal output, chat reasons, Gov is source of truth read via filesystem commands. Gov's Copilot is localhost-only, reachable via SSH tunnel. Add a section to
    WORKING_AGREEMENT.md describing the actual workflow: user
    brings terminal output to the chat; the chat does the
    reasoning; Gov is the source of truth for state, read via
    filesystem commands. No separate "talk to Gov" step exists.
    Motivated by 21 Sept session confusion.

[x] ops.readme_accuracy — DONE 21 Sept. bosly-gov/README.md corrected: `bosly` prints orientation, does not launch a server or browser. The Gov UI runs on localhost:3102 and is reachable from another machine only via SSH tunnel. Fix bosly-gov/README.md. It claims
    `bosly` launches the server and opens a browser UI. It
    doesn't — `bosly` prints orientation only. Document that
    the Gov UI is localhost-only and requires an SSH tunnel
    from another machine.

[x] accord.usage_capture_wiring — DONE 21 Sept. Wired useUsageTracking into all nine workspace pills (active, finance, health, calendar, contacts, inbox, invoice-analytics, social, data-health). Removed the duplicate hook at components/useUsageTracking.ts. UsageEvent now captures product usage. Unblocks gov.evolve_loop. call useUsageTracking from
    each of the nine workspace pills so pill open/close events
    land in the UsageEvent table. The hook and the
    /api/usage/ping route both exist and work; they are simply
    never called. Also reconcile the duplicate hook copies at
    components/useUsageTracking.ts and lib/useUsageTracking.ts —
    pick one location, delete the other. Prerequisite for
    gov.evolve_loop. Discovered 21 Sept when checking whether
    the evolve loop had a data source.

[ ] [LIVE] gov.evolve_loop_feedback - feedback-driven evolution.
    Split from gov.evolve_loop on 28 Sept. The original item was
    gated on UsageEvent rows; that gate covers the usage half only.
    This half has real data and is buildable now.

    TWO FEEDS:
      feedback.jsonl — user sentiment on chatbot replies, written
      by the ChatDrawer feedback flow. Path:
      /mnt/bosly/bosly-data/logs/feedback.jsonl

      unknown-intents.jsonl — questions the chatbot could not
      answer, written by logUnknownIntent in
      lib/workflow/index.ts. Path:
      /mnt/bosly/bosly-data/.data/governor/unknown-intents.jsonl
      Surfaced in the orientation since 28 Sept (UNANSWERED
      QUESTIONS section), so the count is seen every session.

    What it does:
      Produce a periodic digest. Which questions recur? Which
      feedback items are open, which addressed? Close the loop
      by telling the user when their feedback led to a change.
      Output: a report plus a small tracking store (open /
      addressed). Suggested cadence: weekly.

    DESIGN NOTES:
      - Not a fast-tier check. It reads signal, it does not
        verify invariants.
      - The unknown-intents summary already appears in the
        orientation. The digest is the fuller version: grouping,
        recurrence, and the open/addressed tracking.
      - The feedback loop is a two-way street. If a user takes
        the time to report something, they should be able to
        see that it was received and whether it changed
        anything.
      - Path note (28 Sept): the two feeds use different path
        mechanisms. unknown-intents.jsonl hardcodes the mount
        path in lib/workflow/index.ts; feedback.jsonl uses
        dataPath("logs") in app/api/feedback/route.ts. Both
        resolve to the same mount today. If BOSLY_DATA_DIR is
        ever overridden, the unknown-intents log would not
        follow and the digest would read the wrong place.

[x] ops.archive_ai_era — DONE 3 Oct. The AI chat was replaced by the
    workflow engine on 24 Sept, but its routes and components were
    never removed. Archived to legacy/api-ai-20261003/: five routes
    (check-leads, next-action, orchestrator, reply, realtime), the
    lib/bosly-brain.ts, and three dead components (ChatAssistant,
    ChatWidget, BoslyChatWidget). All unreachable — the greps found
    no callers. 'realtime' was not AI at all: a local keyword search
    over chat-memory.txt, and a duplicate of bosly-brain.ts.
    Commits 5347025, f3ed729. The live chat is ChatDrawer.

[~] gov.orphaned_routes — BUILT 3 Oct, report-only. checks/
    orphaned_routes.py. UPDATE 3 Oct: down from 90 to 77 after
    two clusters archived — tasks (8 routes) and today /
    today-state / timeline / time-saved (4 routes).
    Original entry follows.
    checks/
    orphaned_routes.py lists every route whose path has no caller
    outside its own file. Server-only routes are allowlisted.

    FIRST RUN: 90 of 202 routes orphaned. Spot-checked three
    clusters and all are real — no reference anywhere in app/ or
    components/:
      - today, today-state, timeline, time-saved (4)
      - settings/connections/* (6)
      - tasks/* (8) — the briefing counts tasks by a direct
        Prisma query, not through these routes

    Other clusters in the 90: inbox (~12), finance future
    features (6 — gifts, pension, overview, status, tax-position,
    mtd), onboarding (3), messages (2), spaces (1), and the rest.

    NOT YET: registered in manifests/checks.yml — 90 findings
    would break the pipeline. And the allowlist is incomplete;
    some findings will be false positives.

    TO DO: work down one cluster per session. Classify each as
    dead (delete), deliberate (mark), or false positive (fix the
    check). Then register it.

    Original entry follows.
    A check that lists every API
    route and fails if one has no caller and is not marked
    server-only (cron, webhook, or an explicit comment). Nothing
    catches an orphaned route today; the code says nothing about
    whether its parts are still reachable.

    Argument, 3 Oct. Eight unreachable things were found by hand in
    one afternoon: five routes in app/api/ai/, lib/bosly-brain.ts,
    and two still open — app/api/user/usage/route.ts (no callers,
    hardcodes plan: "trial") and app/api/inbox/replies/suggest
    (no callers). A check would have caught each at the moment it
    became dead, not two weeks later.

    Shape: same as gov.paid_routes_gated — an explicit list,
    verified mechanically. Report-only first; fail the pipeline
    once calibrated.

[ ] [GATED] gov.evolve_loop_usage - usage-driven evolution.
    Split from gov.evolve_loop on 28 Sept.

    Read UsageEvent (product usage — pill open/close/duration
    events) and produce a periodic digest. Which pills get opened?
    Which flows start but do not finish? Which features are being
    ignored? Where is the friction?
    Data source: UsageEvent table.

    GATE: do not build until there are rows to read. accord.
    usage_capture_wiring is done (21 Sept), so the pills should
    write rows as the app is used — but the count has not been
    confirmed. A psql check on 28 Sept failed on a role that does
    not exist, so the gate is unverified rather than open. Confirm
    UsageEvent has rows before building.
    NOTE: do not confuse AnalyticsEvent (1678 rows) with product
    usage — it captures the /invoice lead-magnet, not the app.
    See fact-20260921-usage-event-empty.
    Output: a report. Suggested cadence: weekly.
    The usage digest should not identify individual users.
    Aggregate only — the user should know what is being measured
    and why.

[ ] [DECISION] gov.orientation_script_versioned — /usr/local/bin/bosly is
    outside version control. The script that generates every
    session's orientation has no git history; if it is corrupted
    or edited by accident, there is no recovery beyond a single
    .bak, which is itself deleted after each patch. Options:
    (a) move the script into bosly-gov/ (e.g. bosly-gov/bin/bosly),
    commit it, and symlink /usr/local/bin/bosly to it; (b) keep it
    in bosly-gov/ and install via a small install.sh; (c) accept
    the risk and document the decision here. Raised 27 Sept after
    the tail -20 fix showed the script is editable but untracked.

[ ] [DECISION] gov.memory_persistence — /mnt/bosly/bosly-data/copilot-knowledge/*/memory.json
    is not tracked by any git repo. Confirmed 27 Sept: bosly-1.0,
    bosly-keep, and bosly-gov do not track any path under
    copilot-knowledge. The memory files are the only place the
    lessons live — the plan records what to do, memory records
    what has been learned about how. If the mount fails or a file
    is corrupted, there is no history to recover from; the only
    copy is the one on disk, plus a single .bak that is
    overwritten on the next write. Same shape as
    gov.orientation_script_versioned (things that matter living
    outside version control), higher stakes. Options: (a) nightly
    cp to a different mount (e.g. /mnt/bosly/backups/memory/),
    keeping the last 30 days, run from the existing 5am cron;
    (b) symlink copilot-knowledge into a tracked repo; (c) accept
    the risk and document the decision here. Raised 27 Sept after
    a session wrote three entries and then discovered the file
    they went into was untracked.

[x] gov.accord_as_source_of_truth — DONE 27 Sept. The Accord was
    described as the constitution ("it bends features, not the
    other way round") but it lived at bosly-gov/docs/ACCORD.md — a
    different repo from the app it governs. Nothing versioned it
    with the code; nothing checked it against the code. On 27 Sept
    an audit found it contradicting itself and the schema about
    which pills are encrypted.

    Both moves are done:
      (a) The Accord is at bosly-1.0/docs/ACCORD.md, committed with
          the app. The app repo's .gitignore ignored docs/
          wholesale; narrowed to docs/* with an explicit exception
          for the Accord. Commit e3cce86.
      (b) gov.accord_compliance is a fast-tier check that reads the
          encrypted-models marker from the Accord and compares it
          to prisma/schema.prisma. It passes: both lists name the
          same ten models. Committed in bosly-gov.

    The Accord's content was rewritten the same day to match the
    code: five pills encrypted (Invoicing, Contacts, Calendar,
    Finance, Health), four not (Active, Inbox, Social, Data
    health). Article 1.1 and Article 1.2 had contradicted each
    other; Part III was stale by three pills. All corrected.

    Known limit: gov.accord_compliance verifies the machine-readable
    marker, not the prose. If someone edits the prose and not the
    marker, the check will not catch it. That gap is human review.

[x] gov.claim_drift_audit — DONE 27 Sept. The six drifts found
    that day are all fixed. Recording them here, then fixing them,
    is what closed the loop the audit opened. Each is
    a surface claiming something the code does not do.

      1. app/page.tsx:267 — card says "AI is £25/month when you
         want it". The cloud AI was removed 24 Sept. False.
      2. app/page.tsx:263 and app/signin/page.tsx:260 — card says
         "Zero-access encryption" with no scope. True for five
         pills, not for Active, Inbox, Social, or Data health.
      3. app/(marketing)/safety/page.tsx — says "your data is
         encrypted before it reaches our servers" and never names
         the Social/Anthropic exception. The FAQ and the Accord
         both disclose it; the safety page does not.
      4. app/(marketing)/faq/page.tsx:35 — the £25 answer ends
         "No cloud AI, no third-party processor", two questions
         after the FAQ itself discloses the Anthropic connection.
         Self-contradictory.
      5. PLAN.md accord.encrypt_all_pills — lists six pills as
         needing encryption. Three (Contacts, Calendar, Finance)
         are already encrypted. Remaining: Active, Inbox, Social.
      6. PLAN.md accord.user_docs_prose_pass — says the Accord is
         "most likely to be read by someone deciding whether to
         trust Bosly". The Accord is internal, for the founder.
         It is not a customer-facing document. FIXED 27 Sept:
         removed from the prose-pass list.

    Fixing these by hand is the short version. The durable fix is
    gov.accord_compliance. This item records the instances.

[x] session-20260928-chat-loop — DONE 28 Sept. The chatbot's feedback
    loop, checked after the workflow-engine swap, was found half-built
    and disconnected: the engine logged unknown intents to a file and
    returned a cannot-help response, but the user was never told the
    question was noted, and nothing read the log. What was built and
    fixed:

    - buildCannotHelpResponse() rewritten. It said "I can't help with
      that yet" and ended "If you want to do it yourself", which read
      cold. Now: acknowledges the question, says it's been noted,
      frames the gap as how Bosly grows, keeps the capabilities list,
      ends by naming the floor. Commit 81731cc.

    - UNANSWERED QUESTIONS section added to the bosly orientation
      (/usr/local/bin/bosly). Reads unknown-intents.jsonl, shows total,
      last-7-days, and the most recent question. Always renders, even
      at zero, so absence is never ambiguous. The signal goes where the
      founder looks every session. 11 test rows cleared first.

    - evolve_feedback.py built (bosly-gov root). Read-only digest of
      unknown-intents.jsonl and feedback.jsonl. Groups unknown intents
      by normalised text; splits feedback by source. Drafted with
      Copilot, reviewed against the code. Commit 5e5b701.

    - gov.evolve_loop split into gov.evolve_loop_feedback [LIVE] and
      gov.evolve_loop_usage [GATED]. The original was gated on
      UsageEvent rows; that gate covers only the usage half.
      Commit c90ac86. References updated in PLAN.md and
      OPS_COMMANDS_AUDIT.md.

    - Two gaps recorded: accord.feedback_message_link (msgIdx taken
      but never sent) and the two-roots path note. Commit 54dd28e.

    Two things the loop revealed about itself: unknown-intents.jsonl
    held only 11 test rows and feedback.jsonl did not exist at all —
    both mechanisms were wired and neither had carried real data. And
    the two logs use different path mechanisms (one hardcodes the
    mount, one uses dataPath()); they agree today but could diverge.
    The first is the same shape as pattern-20260928-mechanism-without-
    input.

[ ] [DECISION] accord.export_decrypt_on_download — The export route
    (app/api/settings/export/route.ts) dumps raw table rows. Five
    pills export as ciphertext (Invoicing, Contacts, Calendar,
    Finance, Health); four export as plaintext (Active, Inbox,
    Social, Data health), plus the user record. The route's own
    note promises "in future, Bosly will decrypt this data for you
    before download so you can read it directly". The design note
    in this plan (see /api/settings/export) says the opposite:
    "Include encryptedData. User owns their export."

    Both positions are defensible. Raw export proves the server
    never held the key. Decrypted-on-download gives the user a file
    they can actually read — the vault key is already in the
    browser during the session, so it is a client-side operation.
    The two notes disagree and the promise is not tracked as work.
    Decide: (a) decrypt client-side on download, remove the beta
    note; (b) keep raw, remove the promise from the note; (c) keep
    raw, keep the promise, and build it later as its own item.
    Raised 27 Sept while auditing the export for accuracy.

[ ] [LIVE] accord.feedback_message_link — ChatDrawer.sendFeedback(msgIdx, text)
    takes the index of the bot message being flagged, but never
    sends it. The feedback payload carries rating, text, ts, and
    source, but not msgIdx. So a flagged reply cannot be traced
    back to which message it was flagging — the index exists at
    the call site and is dropped before the POST.
    Fix: include msgIdx (or a stable message id) in the payload,
    store it alongside the rating, and let the evolve feedback
    digest show which reply was flagged.
    Found by an external review on 28 Sept while designing the
    digest. Same shape as the claims-drift class: state that
    exists and is not carried to where it is needed.

[ ] [LIVE] accord.problem_report_flow — The old chatbot let a user
    say "the inbox isn't working", ask follow-up questions, and offer
    to log it for the developer. That lived in the retired
    chatWithTools path and was not ported to the workflow engine.
    Now such a message hits the engine, matches nothing, and falls
    into the generic "I don't have a way to answer that yet" response
    — which tells the user it's noted but gathers no detail.

    DESIGN (agreed with an external review, 28 Sept):
      - Engine first. If runEngine returns unknownIntent, do a
        second-pass check: does this sound like a problem report?
      - If yes, start a bounded state machine in the chat route,
        not in the engine. runEngine stays single-turn and stateless.
      - Two scripted follow-up turns, then a confirm-and-log step.
        No LLM, so every prompt is fixed, not generated.
      - State lives in a new file keyed by userId:
        /mnt/bosly/bosly-data/.data/governor/problem-report-state.json
        Complete on explicit user confirmation; expire on timeout.
        Never complete on silence.
      - The finished report is written to feedback.jsonl with
        source: "chat_report_flow", so the existing digest picks it
        up as its own category. No third log file.
      - Detection helper isLikelyProblemReport(message) lives in the
        route: phrases like "isn't working", "broken", "won't",
        "error", "failed", "stuck". Transparent rules, no scoring.

    The user-facing copy per turn is the founder's voice; the shape
    is: acknowledge, ask one focused question, summarise, offer to
    log, confirm.

    Found 28 Sept while checking the chatbot after the engine swap.

[ ] [LIVE] accord.waiting_well_page — A public "Waiting Well" resource
    page inside Bosly, linked from the Instagram bio. A lead magnet,
    not a product: it gives people something useful while they wait
    for an ADHD assessment, and points at Bosly as a tool for those
    who want one. The second unauthenticated public surface, after
    the standalone /invoice tool (see the lead-magnet note above).
    Static: holds no user data, so the encryption question does not
    arise.

    Purpose. In England, over 960,000 people are waiting for an ADHD
    assessment, some two years or more, with almost nothing offered
    while they wait. Healthwatch found people feel abandoned by the
    system during this period. The page fills that gap.

    The angle. Most waiting-well resources are clinical-adjacent,
    generic self-care, or US-focused. None is UK-specific, ADHD-tax-
    aware, and community-anchored. The ADHD tax angle is the unique
    contribution. It leads the page; Right to Choose comes second,
    because RTC is the system's frame and the tax is ours.

    Contents, in order:
      1. The ADHD tax while you wait — the lead. Money, invoices,
         deadlines, admin chaos, small systems to build now.
      2. Right to Choose explained — ask the GP for it by name, name
         the provider, do not accept a local referral. England only;
         the other nations have different routes.
      3. Your rights at work without a diagnosis — reasonable
         adjustments can be requested without a formal diagnosis.
      4. Helpful links — ADHD UK, AADD-UK, ADHD Foundation,
         ADHDadultUK, Healthwatch waiting-well guidance.
      5. Community — point at Instagram comments and posts.
      6. FAQ — built from what people actually ask in the comments.

    The bridge sentence (drafted and agreed 28 Sept, do not rewrite
    badly): "Bosly is a tool to help empower you and your ADHD — the
    admin side, the invoices, the keeping-track — and to help reduce
    the ADHD tax burden. Bosly is here if you need it."
    It appears once, near the end. Bosly is not mentioned anywhere
    else on the page. If the reader wants the tool they click; if
    not, they got real help and will remember it.

    Constraints:
      - Public, accessible without login. MUST be added to the
        middleware's isPublicRoute list, or it redirects to sign-in.
        See accord.middleware_public_routes.
      - Simple URL, e.g. bosley.app/waiting. Lives in the
        app/(marketing)/ route group with the other public pages.
      - Start as a plain page: text, links, headings. No chatbot,
        no quiz. Live and linked beats perfect.
      - Stays on the community and resources side of the line. Not
        clinical, not diagnostic, no implied medical judgment. The
        ADHD taskforce has recommended regulation and quality
        standards for ADHD service providers; the page must not look
        like one.
      - The page must not promise more than Bosly does today. It
        helps with what exists and points at a direction; it does not
        claim Bosly runs your admin yet. See
        accord.admin_assistant_direction.

    Success. Not thousands of users. A handful of the right people.
    Track clicks from the Instagram bio. Adjust framing if it is not
    used.

    DRIFT: external claims and links go stale. A check should verify
    the resource links resolve (HTTP 200) and that the waiting figure
    carries a source and date in a machine-readable marker. Advice
    quality and RTC correctness stay human review — same split as
    gov.accord_compliance, mechanical drift checked, prose reviewed.

    BEFORE BUILD: verify the external claims — the waiting figure
    and its source; the Right to Choose mechanics against current
    NHS England guidance; and that all five resource links resolve.

    SEQUENCING: build after the 3 Oct Founding Members reel, not
    before. The reel is the priority this week.

    Raised 28 Sept.

[ ] [DECISION] accord.admin_assistant_direction — Bosly should
    eventually do the admin, not just hold the data. Today the pills
    store and the chatbot answers counts, dates, and statuses. The
    direction is an assistant that acts: chases invoices, watches
    deadlines, drafts the boring replies, handles the follow-ups.
    This is the concrete form of the Accord's "liberation engine"
    line.

    Not built now, and not promised on any user-facing page. But it
    is the thing the Waiting Well page bridges toward, and it is the
    reason that page is worth building.

    Decide the shape before it appears in marketing: what "does your
    admin" means, concretely, and which pills it spans. Raised
    28 Sept.

[ ] [LIVE] ops.monitor_route_roster — bosly-monitor's route roster
    (the check labelled "Phase 3-8") drifted. On 30 Sept it emailed
    a failure: 6/7 route files present. The missing file was
    /api/bosly/preferences, deleted on purpose in 0b3f9d7
    ("fix(chat): remove dead preferences endpoint references"). And
    the roster did not know about /api/bosly/enrich-contacts, which
    exists. So the roster was wrong in two directions at once.

    The check fired correctly — something had changed — but the
    change was intentional and nothing updated the list. Same class
    as the Accord drift: a hardcoded list that nothing reconciles
    with reality. Fixed 30 Sept by correcting the list to the seven
    real routes and dropping the stale "Phase 3-8" label.

    DURABLE FIX (decide later): the roster names files. A roster
    that derives from the directory cannot go stale. If this
    happens again, derive the expected set instead of hardcoding it.
    Raised 30 Sept, from a bosly-monitor email at 03:15.

[x] accord.calendar_to_invoice — DONE 30 Sept. A past calendar event
    linked to a business contact has a Create invoice button. It
    builds a draft invoice from the event's hours (end - start,
    rounded to 0.25; all-day = 1) and the contact's hourly rate,
    carries the client's name/company, email and address, encrypts
    it client-side, and posts it to Finance as a draft. Found in
    Finance, editable, sendable. The first concrete piece of
    accord.admin_assistant_direction — the app acting, not just
    storing.

    Built alongside:
      - CalendarEvent.contactId (schema) and a contact picker in
        the event editor.
      - Contacts now save company and address (the payloads
        dropped them).
      - Contacts are decrypted in the calendar — the plaintext
        name column is "[encrypted]", a decoy.
      - Invoice editing: PATCH /api/invoices/[id], the editor
        PATCHes when it has an id.
      - The attached PDF draws the client email and address.

    Note: calendar invoices carry no VAT — the payload omits it.
    Set VAT by editing the invoice in Finance.

[x] session-20260930-calendar-invoice — DONE 30 Sept. Second half of
    the day. Built the calendar-to-invoice chain end to end, and
    fixed everything it exposed:

      - Contacts "merged" — actually all contacts looked identical
        because their plaintext name is "[encrypted]". Resolved by
        decrypting contacts in the calendar.
      - The contact PATCH rejected the client's payload
        (invalid_encrypted_payload) while the POST accepted it. The
        two routes had duplicate, drifted validators.
      - Contact company and address never saved — the payloads
        omitted them.
      - Calendar-invoice amounts were 0 — hourlyRate arrives as a
        Prisma Decimal, and `typeof === "number"` rejected it.
      - The attached PDF showed only the client name — no email, no
        address. Fixed.

    Lesson: the plaintext columns are decoys; decrypt first. And
    duplicated validators drift. See the two memory entries.
    Raised 30 Sept.

[x] accord.microsoft_oauth_hidden — SUPERSEDED 3 Oct. Microsoft
    was removed entirely: the routes, all three UI buttons (the
    email form, the calendar, and the connections page), and the
    social connections page. There is nothing to restore.

    Original entry follows.
    The Microsoft/Outlook
    OAuth button in the email connection form is hidden as of
    30 Sept. It pointed at /api/auth/outlook (no such route), and
    Microsoft OAuth is not configured: MICROSOFT_CLIENT_ID,
    MICROSOFT_CLIENT_SECRET, and MICROSOFT_TENANT_ID are absent
    from .env.production. To restore: create an Azure app, register
    the redirect URI (https://bosly.app/api/auth/microsoft/callback),
    add the three env vars, and remove the {false && ( } guard in
    EmailConnectionForm.tsx. Gmail, Yahoo, and custom IMAP (IONOS)
    all work via app password; only Microsoft OAuth is absent.
    Raised 30 Sept.

[ ] [LIVE] ops.monitor_alert_fallback — bosly-monitor's only alert
    channel is the nodemailer email, sent via node. The script loads
    nvm and sets PATH so node is found under cron, and that works
    today — the 29 Sept alert arrived. But if node were ever
    genuinely missing, the alert would be lost with only a stderr
    WARN that cron discards; the header comment acknowledges this
    ("Without node, the checks can still run but alerting is
    unavailable"). A monitor whose only alert channel can silently
    fail is fragile. Durable fix: also append failures to a log
    file, so a failure leaves a trace regardless of the email path.
    Not broken today — recorded 30 Sept while fixing the roster and
    the alert email's newline bug.
    Raised 30 Sept.

[x] session-20261001-full-day — DONE 1 Oct. A day that began as "help
    me before the reel" and became the free/paid boundary, the
    payment path, and a documentation audit. Kept as a capsule so a
    future session sees the arc, not just the outcomes.

    THE ARC:
      1. The boundary (morning). The app did not know what was free.
         A paying user had been told to pay again. Root: BillingSettings
         read the `plan` column (an onboarding answer) while the webhook
         wrote `subscriptionTier`. Fixed the read path. Then built the
         model: lib/tiers.ts, feature-based, not pill-based — Finance is
         a mix (manual invoicing free, transactions and tax pack paid).
         Wrote it into the plan as accord.free_paid_boundary.
      2. The gates (afternoon). Gated four UI surfaces — Social, the
         Finance transactions tab, the Calendar create-invoice button,
         Data health — and swept sixteen route handlers across nine paid
         routes onto requireAccord. Rewrote checks/paid_routes_gated.py
         from a prefix scan to an explicit route list (a prefix cannot
         express a boundary that cuts across prefixes). Registered it;
         the pipeline went from 11 checks to 12.
      3. The payment path (evening). A real payment was tested end to
         end. It worked — upgrade, Stripe, pay, return, Accord active.
         What looked like a bug was Stripe semantics: cancelling at
         period end keeps a subscription active, and a refund does not
         cancel a subscription. The app was right.
      4. The docs (evening). Found the machine-facing docs described a
         bot retired on 24 Sept: llms.txt and llms-full.txt claimed it
         books appointments, sends invoices, drafts emails. Rewrote
         against the workflow engine map, which records what each of the
         ten workflows actually computes. Same drift in miniature in the
         FAQ and the billing card (the inbox described as paid).

    THE SHAPE, for a future session: every bug today was a disagreement
    between two parts of the system. A reader watching a column a writer
    did not touch. A pill fetching a flag it never consulted. A check
    scanning prefixes when the boundary was features. Docs describing a
    product that was retired. A comment asserting a policy that had
    changed. None of it crashed. All of it was incoherence, and the
    pipeline was green throughout. Four findings on 1 Oct were this one
    class. That is the argument for gov.claim_invariants, recorded there.

    LESSONS (memory): pattern-20261001-read-write-column-drift,
    pattern-20261001-overloaded-column,
    pattern-20261001-checked-but-not-enforced,
    pattern-20261001-prefix-scan-cannot-see-a-mix,
    pattern-20261001-stale-comment-contradicts-code,
    pattern-20261001-build-error-above-the-fold,
    fact-20261001-stripe-cancellation-semantics,
    pattern-20261001-webhook-is-best-effort,
    fact-20261001-plan-column-fully-drained,
    pattern-20261001-docs-describe-a-retired-product.

    DEFERRED: accord.plan_column_layer2 (the column drop; the reads are
    gone), user/usage disposition (no callers, undecided),
    accord.tier_boundary_copy (ticked), the webhook reconciliation gap,
    the updated-does-not-clear-tier edge case, and gov.claim_invariants
    itself.

    TOMORROW: a fresh-account checkout entering FOUNDER40, to confirm
    the £15 founding-member price. Then the reel decision, with
    everything it claims now verified.

[x] session-20261003-full-day — DONE 3 Oct. A day that began as "help me
    before the reel" and became the free/paid boundary's second day, a
    documentation audit, three new checks, and a hygiene sweep. Kept as
    a capsule so a future session sees the arc, not just the outcomes.

    THE ARC:
      1. The boundary, continued (morning). Yesterday's billing fix held.
         This day found the rest: the Accord still said the inbox was
         paid; the README described an app that no longer exists; the
         welcome email claimed post-quantum encryption.
      2. The email password (early). encryptPassword derived a key and
         returned plaintext anyway. Fixed, migrated, verified — then
         five readers were found one at a time, because the sweep
         wasn't done first.
      3. The AI era (midday). The workflow engine replaced the AI chat
         on 24 Sept, but the routes and components stayed. Archived.
         Then Microsoft, then three dead directories, then a
         superseded connections page.
      4. The checks (afternoon). Three built: orphaned_routes (90
         found), tsconfig_excludes (3 hidden directories, all broken),
         claim_invariants (the free-pill list). Two registered.
      5. The hygiene batch (evening). Ten .bak files, a committed .tmp,
         a cron script pointing at a Mac, five one-off scripts, a
         README reduced 193 lines to 152.

    THE SHAPE, for a future session: every bug today was two parts of
    the system disagreeing, and every one passed every check. A reader
    watching a column the writer didn't touch. A migration that updated
    one reader of five. A feature excluded from type-checking. Docs
    describing a retired product. A button pointing at a deleted route.
    None of it crashed. All of it was incoherence, and the pipeline was
    green throughout.

    The answer was not more care. It was three checks that make the
    hidden visible. Two are registered and green. The third is
    report-only with 77 findings left to work.

    LESSONS (memory):
      pattern-20261003-ask-what-else-after-every-fix — the method
      pattern-20261003-excluded-means-unchecked — the tsc blind spot
      pattern-20261003-doc-drift-recurs — five documents, one claim
      fact-20261003-reader-sweep-discipline — grep the readers first
      pattern-20261003-pointer-to-something-that-isnt-there

    Plus, from 1 Oct: pattern-20261001-read-write-column-drift,
    pattern-20261001-hidden-not-removed (3 Oct), and ten others across
    the two days.

    CHECKS BUILT:
      gov.orphaned_routes — 90 routes with no caller; 77 remain
      gov.tsconfig_excludes — registered, 0 flagged
      gov.claim_invariants — registered, checks the free-pill list
    The pipeline went from 11 checks to 15.

    DEFERRED: accord.cross_pill_propagation (a) — the real code work
    left; accord.password_reset_ui; the iCloud calendar UI;
    accord.connection_providers; keep.scripts_typecheck_excluded; the
    dead OAuth columns; and 77 orphaned routes to work down in clusters.

    TOMORROW: cross_pill_propagation (a) wants a fresh head — every
    pill's write emits an event, every list listens, one shared module
    for the names.

[x] session-20260930-full-day — DONE 30 Sept. One session that began
    as "check the chat feedback loop" and became a full user-path
    audit of the app, then a payment fix, then a repo cleanup. Kept
    as a capsule so a future session sees the arc, not just the
    outcomes.

    THE ARC:
      1. Chat loop (morning). The chatbot said "I can't help" coldly
         and the unknown-intent log was empty. Rewrote the message;
         surfaced the count in the orientation; built
         evolve_feedback.py.
      2. App testing (afternoon). Walked the app as a user. Found the
         vault PIN blocked on iOS by a WebAuthn probe (a launch
         blocker), the logo upload failing (middleware + formData),
         the landing page untracked, the sign-in cards stale, the
         metadata carrying the removed-AI claim, Microsoft OAuth
         pointing at a missing route. Fixed all.
      3. Calendar to invoice (evening). Built the whole chain: event
         -> draft invoice -> edit -> send, with the client's details,
         from the user's own account. Found decoy plaintext columns,
         drifted validators, dropped company/address, Decimal
         hourlyRate.
      4. Payment + tier (night). A real £25 payment did not activate.
         Root: the middleware redirected the Stripe webhook to
         /signin (303) — every delivery failed. Fixed; added
         gov.public_routes_are_public. Swept the stale AI claims from
         terms, privacy, changelog, billing. Built requireAccord +
         paid_routes_gated (34 ungated routes, defined for the
         sweep).
      5. Inbox + cleanup (late). The inbox seeded demo emails and its
         "add account" wrote to a mock. Removed both; real connect
         now works, with the free=1/Accord=5 limit that was already
         built. Then archived the dead root, removed 48 debris files,
         4 dead components, 69 .bak.

    THE SHAPE, for a future session: every real bug today was found
    by USING the app, not reading it. The pipeline was green
    throughout. Checks verify invariants, not that a flow works.
    When you change a flow, walk it.

    LESSONS (memory): pattern-20260930-user-path-testing,
    plaintext-columns-are-decoys, duplicated-validators-drift,
    middleware-public-routes, mock-beside-real.

    DEFERRED: accord.tier_enforcement_sweep (34 routes, defined by
    paid_routes_gated), accord.tier_boundary_copy (docs say Inbox is
    paid; the model is 1 email free), the £25 re-test,
    accord.email_password_plaintext.

    Raised 30 Sept.

[x] accord.inbox_stubs_removed — DONE 30 Sept. The inbox had two
    stubs beside real code:

      - app/api/inbox/list seeded demo messages on first run and
        when the file was empty, writing fake emails to the user's
        real inbox file. A new user's inbox contained fake emails,
        persisted. Now returns empty; the UI says connect your
        email.
      - AddAccountModal tested an account (real IMAP/SMTP test),
        then POSTed to /api/inbox/accounts — a mock that ignored
        the credentials and wrote to an in-memory array. Nothing
        persisted, so "add account" never connected anything. Now
        posts to /api/email-connection, the real ConnectedEmail
        path.

    Removed app/api/inbox/accounts/route.ts and lib/inbox/mock.ts.
    Kept accounts/test (the IMAP test). Commit 6b7f24c.

[x] accord.tier_boundary_copy — DONE 1 Oct. The FAQ and the
    billing card said the inbox was part of the £25 tier; both
    corrected (be1f91d). Free includes one connected email
    account, Accord raises it to five. Matches
    accord.free_paid_boundary.

    Original entry follows.
    The one-email-free model is
    already built: /api/email-connection POST enforces "free = 1
    connected email, Accord = up to 5". But the marketing and
    billing copy says "Inbox is part of the £25 tier" (FAQ, pricing
    copy, billing page), which is now wrong — a free user gets one
    inbox. The docs must say: free = 1 email account plus the five
    free pills; Accord = up to 5 email accounts plus the paid
    pills and chatbot. Update FAQ, accord.tier_copy, the billing
    page, and any pricing line that implies Inbox is paid
    outright. Raised 30 Sept.

    SCOPE CHANGE for accord.tier_enforcement_sweep: the inbox is
    NOT gated wholesale. The tier limit is on the number of
    connected accounts, enforced in /api/email-connection. So the
    sweep gates Finance, Social, and Data health routes, not inbox
    routes — and the inbox is free with one account. The
    paid_routes_gated check must be updated: inbox routes are
    either gated or exempt-by-design (the inbox is free for one
    account). Revised 30 Sept.

[x] accord.free_paid_boundary — AGREED 1 Oct. The single source
    of truth for what is free and what belongs to Accord.
    The boundary is drawn around FEATURES, not pills. Finance
    is the clear case: manual invoicing is free, transactions
    and the tax pack are paid.

    FREE — Active, Contacts, Calendar, Health, and manual
    invoicing (the Finance Invoices tab). The inbox, for one
    connected email account.

    ACCORD — everything free, plus: the Calendar "create
    invoice" button, Finance transactions and the tax pack,
    Social, Data health, the chatbot, and additional connected
    email accounts (up to 5).

    In code: lib/tiers.ts holds FREE_FEATURES / PAID_FEATURES
    and isAccordTier(). requireAccord.ts is its server-side
    mirror.

    Both layers enforce it. UI: Social, the Finance transactions
    tab, the Calendar create-invoice button, Data health. Routes:
    nine paid routes, sixteen handlers (e0838d6), enforced by
    gov.paid_routes_gated in the fast tier.

    The docs copy was corrected 1 Oct (be1f91d): the FAQ and the
    billing card no longer say the inbox is paid.

    Raised 1 Oct, after the Stripe test showed the app did not
    know which pills were free.

[x] accord.tier_enforcement_sweep — DONE 1 Oct. requireAccord is
    now the first statement in every handler of the nine paid
    routes (sixteen handlers): finance/categories, finance/ftx,
    finance/import-transactions, finance/parse-statement,
    finance/transactions, finance/tax-pack,
    social/generate-captions, social/generate-ideas,
    data-health/identities. Committed e0838d6.

    checks/paid_routes_gated.py was rewritten as an explicit
    route list (a prefix scan cannot express a boundary that
    cuts across prefixes — Finance is a mix). It is registered
    in the fast tier (bosly-gov acae57b) and passes 12/12.

    Original entry follows.
    READY TO EXECUTE. The
    helper (lib/requireAccord.ts) and the check
    (checks/paid_routes_gated.py) exist, but the check is NOT
    registered in manifests/checks.yml — which is why the
    pipeline is green. Running it standalone on 1 Oct: 36
    routes, 33 ungated.

    SCOPE — corrected 1 Oct against accord.free_paid_boundary.
    The sweep gates the transaction and tax-pack routes in
    Finance, the social routes, and the data-health routes.
    It does NOT gate the invoice routes (manual invoicing is
    free, the lead magnet) and it does NOT gate the inbox
    (count-gated in /api/email-connection, free for one
    account). The earlier scope — "all of inbox, finance,
    social, and data-health; 34 of 37" — was wrong twice.

    BLOCKER: checks/paid_routes_gated.py lists `inbox` in
    PAID_PREFIXES and treats each prefix as atomic. Both are
    wrong for the corrected scope. Fix the check before
    registering it.

    Steps:
      1. Add `const gate = await requireAccord(req); if (!gate.ok)
         return NextResponse.json({ error: gate.error }, { status:
         gate.status });` to each of the 34 routes. Exempt webhooks
         and cron (the check already exempts them).
      2. Add the check to manifests/checks.yml (fast tier).
      3. Run the fast tier — green means every paid route is gated.
      4. The UI: a paid pill, when the user is not Accord, shows a
         "part of the full workspace" state with an upgrade link,
         not a hard wall. "Discovery, not selling."

    Not wired yet: the check fails until step 1 is done, and a
    failing check breaks the green pipeline. Raised 30 Sept.

[ ] [LIVE] accord.plan_column_layer2 — UPDATED 1 Oct. The reads
    are gone. `plan` is no longer read as a tier anywhere
    (commit b7acb0f): auth/me and user no longer select it;
    data-health/check reads subscriptionTier only. What remains
    is the column itself and the migration to drop it.

    Remaining:
      - app/api/onboarding/save/route.ts is dead (nothing
        references it). It was the only writer of `plan`.
        Archive to legacy/ per the /onboarding/activate
        precedent (21 Sept).
      - Drop the `plan` column in a migration, backed up first.
      - app/api/user/usage/route.ts has no callers and
        hardcodes plan: "trial". Whether it is dead or a future
        feature is undecided (1 Oct). Nothing reads it, so it
        does no harm; decide when the feature is next touched.
    Then drop the `plan` column in a migration, backed up first.

    Durable fix: a gov check that fails if any tier decision
    reads `plan`. Same class as gov.naming_honesty — a name that
    asserts a meaning the column does not have.
    Raised 1 Oct.

[x] accord.webhook_middleware_public — DONE 30 Sept. The Stripe
    webhook at /api/billing/webhook was not in the middleware's
    public routes, so Stripe's POST was redirected (303) to
    /signin before the route ran. Every webhook delivery failed
    (all six in the Stripe dashboard). A real £25 payment
    succeeded at Stripe and the tier never activated — the
    subscription showed INCOMPLETE and subscriptionTier stayed
    null. Added /api/billing/webhook to the public prefixes.
    curl now returns 400 (invalid signature, route reached).
    Commit 0521fd7. Same class as /uploads (logo, 30 Sept) —
    middleware breaks public routes that are not listed.

[x] accord.billing_ui_incomplete — DONE 1 Oct. The billing UI was
    already complete (cancel, resume, portal, period dates). The
    real bug was the read path: BillingSettings.tsx and
    /api/billing/subscription read the `plan` column — an
    onboarding answer, default "starter" — while the Stripe
    webhook writes `subscriptionTier`. So a paying user saw the
    paid card as "Available". Both reads now point at
    subscriptionTier; the tier check is case-normalised and
    accepts trialing; the card states the £15 founding-member
    price. UPDATE 1 Oct: the full checkout flow was walked end
    to end — upgrade, Stripe, pay, return, Accord active. The
    path works. Remaining: the same flow on a fresh account
    entering FOUNDER40, to confirm the £15 founding-member price.
    Original entry follows.
    The billing area is
    half-built. There is no cancel button (the /api/billing/cancel
    route exists), and no activation feedback: after paying, the
    chatbot still says "go to billing and activate". Stripe routes
    exist (cancel, portal, resume, success) but the UI does not
    connect them. A founding member who pays must see their tier
    active and be able to cancel. Raised 30 Sept.

[x] gov.public_routes_are_public — DONE. Running in the fast tier
    and passing (11/11 on 1 Oct). The plan entry was stale — the
    check shipped but was never ticked.
    Original entry follows.
    A check that verifies
    known-critical routes are in the middleware's public list, so
    a new one is not forgotten. The middleware has broken three
    things in one day: /uploads (logo), the branding upload body,
    and /api/billing/webhook. Each was a route that needed to be
    public (or carry a body) and was not accounted for. The check
    asserts a declared set — /api/billing/webhook, /api/cron,
    /api/auth, /uploads — is present in the public prefixes.
    A regression guard, not a full derivation. Raised 30 Sept.

[x] accord.inbox_dismiss_not_persistent — DONE 3 Oct. Three
    causes, found in sequence:
    1. app/api/inbox/delete passed ciphertext to IMAP, so
       marking SEEN failed auth (fixed, d3b63a2).
    2. Not a store mismatch — the pill reads the cache, and
       dismiss writes it.
    3. addMessageToCache re-added dismissed messages: dismiss
       pushed the uid to cache.dismissedUids, and the IMAP
       worker re-imported it on the next sync. Guard added in
       the one function that writes the cache (cd88dc0).

    Original entry follows.
    Dismissed emails in
    the inbox reappear after a page refresh. There is a Dismiss
    button; what it persists is not yet known. The dismissal is
    evidently not written to the source the list reads from (the
    IMAP \Seen flag, or the local cache), so a reload re-fetches
    them as unread. Worse than not dismissing at all, because the
    user believes they are gone.

    First step: read the dismiss handler and the inbox list source,
    establish what the button does and where the list reads from.
    Then persist the read/hidden state there. Raised 30 Sept, on an
    iOS (IMAP) account.

[~] accord.cross_pill_propagation — PARTIAL 2 Oct. Half (b) is done. Writes in one pill do
    not update readers in another, or even elsewhere in the same
    pill, until a full page reload. Seen 30 Sept: a calendar-created
    invoice did not appear in Finance until reload (fixed with a
    bosly:invoice-created event); a new contact did not appear in
    the calendar picker; a new calendar event did not appear in the
    day view. The pattern is a window CustomEvent
    (bosly:invoice-created, bosly:open-invoice-editor), but it is
    applied ad hoc — most writes do not emit and most readers do
    not listen.

    Two halves:
      (a) PROPAGATION — every create/update/delete emits an event;
          every list that shows the data listens and reloads. One
          shared module of event names and helpers, not ad-hoc
          strings (see pattern-20260930-duplicated-validators-drift
          — the same "copied, then drifted" risk).
      (b) REFRESH — DONE 2 Oct (bosly-1.0 318b99a). A home-screen
          PWA does not reload itself, so a deploy was invisible
          until the app was deleted and re-added. components/
          UpdateBanner.tsx checks /api/version on mount and on
          focus; if the build differs from the one the app
          loaded, it shows a refresh banner. Half (a), the
          cross-pill event propagation, remains open.

    Affects multiple pills — needs a sweep of the whole app, not a
    single fix. Raised 30 Sept.

[ ] [LIVE] accord.invoice_aggregates_client_appointments — The
    calendar-to-invoice button creates one invoice from one event.
    The founder's actual workflow is multiple appointments for one
    client across a month, invoiced once. The button should
    aggregate a client's unbilled appointments, not one event.

    Design (agreed 30 Sept): aggregate by contactId over a
    calendar month, with an editable date range. So the default is
    the current month; the user can widen or narrow it.

    The crux: a billed state. CalendarEvent needs invoicedAt or
    invoiceId, set when an event is included in an invoice, so a
    second press does not double-bill the same hours. Without it,
    invoicing a client twice bills the same appointments twice.

    Also needed: a UI to show which appointments are included
    (and their total) before creating the invoice, rather than
    silently summing.

    Current state: one event -> one invoice. The feature works but
    does not match how invoicing is done. Raised 30 Sept.

[x] accord.email_password_plaintext — DONE 3 Oct. The password
    is now encrypted at rest with ENCRYPTION_KEY (bosly-1.0
    b9489df). The PLAINTEXT: bypass is removed from both the
    writer (encryptPassword now throws if the key is missing
    rather than falling back to plaintext) and the reader
    (sendMail's fallback branch). The one existing row was
    migrated, and sending from it was verified end to end.
    gov.email_password_plaintext now guards it in the fast
    tier (bosly-gov 00fde1e).

    This is encryption at rest, not zero-access — the server
    decrypts to send on the user's behalf. The inbox is
    documented as not-yet-zero-access, so the copy is true.

    Original entry follows.
    The connected email
    account password is stored in plaintext in the database
    (ConnectedEmail.password, prefixed "PLAINTEXT:"). Found 30 Sept:
    a SELECT showed "PLAINTEXT:xxxxxxx" for the IONOS account
    info@greengayte-co.co.uk. This contradicts Bosly's core promise
    — the Accord says the server cannot read user data, but the
    email password is fully readable, and a database leak exposes
    every connected email account. sendMail.ts even has an explicit
    `password?.startsWith("PLAINTEXT:")` fallback, so the plaintext
    path is known. Fix: encrypt connected passwords with the user's
    key (or at minimum ENCRYPTION_KEY), migrate existing rows,
    remove the PLAINTEXT branch. Audit whether any other secret is
    stored the same way. Raised 30 Sept.

[x] ops.secrets_plaintext_audit — DONE 3 Oct. Audited every
    credential-shaped column. Four findings, all fixed:
    ConnectedEmail.password (encrypted, verified with a fresh
    connection); CalendarSyncState.syncToken (encrypted);
    User.passwordResetToken and User.verificationToken (SHA-256
    hashed). The OAuth token columns have no writer — dead.

    Original entry follows.
    accord.email_password_plaintext
    found one secret stored in plaintext (the connected email
    password). Its own fix called for auditing whether any other
    secret is stored the same way. That audit has not been done.

    Look at: every column in prisma/schema.prisma whose name
    suggests a secret (password, token, key, secret); every
    route that writes one; every config value in .env.production
    that is a credential; and the `PLAINTEXT:` pattern itself,
    which may appear elsewhere.

    Raised 3 Oct, split from accord.email_password_plaintext.

[x] accord.invoice_send_from_user — DONE 3 Oct, as a side effect of
    accord.email_password_plaintext. Verified: an invoice sent from
    the user's own connected account (info@greengayte-co.co.uk), not
    from contact@bosly.app. No code change was needed for this item.

    The entry's stated cause was wrong: there is no SMTP_HOST-first
    branch in sendMail.ts (grep returns nothing). The real cause was
    that the stored password could not be decrypted — it was plaintext,
    and the reader tried to decrypt it — so the per-user send failed
    and fell back. Encrypting the password fixed it.

    Original entry follows.
    Email sending always
    uses the server-wide SMTP account (SMTP_HOST in .env.production),
    because getTransporter in lib/email/sendMail.ts checks
    `if (process.env.SMTP_HOST)` FIRST and returns there. The
    per-user path — sending from the user's own connected account —
    is only reached when SMTP_HOST is unset, so it never runs. Every
    user's invoice sends from contact@bosly.app, not from their own
    address, which looks like spam to a client. Fix: prefer the
    user's connected account, fall back to the server SMTP.
    NOTE 3 Oct: the per-user path depends on decrypting
    ConnectedEmail.password, which was plaintext until 3 Oct
    and is now encrypted (accord.email_password_plaintext, done).
    So the blocker may be gone — decrypting a properly encrypted
    password now works, as the verified send test showed. Re-check
    whether the SMTP_HOST-first branch is still the reason invoices
    send from contact@bosly.app. Raised 30 Sept.

[x] accord.invoice_send_preview — DONE 30 Sept. Sending an invoice
    opened the POST directly with an auto-built email; the user never
    saw or approved it, and handleSend swallowed errors. Now a
    dialog opens: it shows the client, an optional note box, the
    sender picker (when more than one account is connected), and
    "Invoice-INV-001.pdf will be attached". Pressing Send builds the
    full invoice PDF client-side and posts note, fromAccountId and
    pdfBase64. Success and errors are shown. Commits ce8fcc7,
    38b42aa, a264774, 4d88c8d.

[ ] [LIVE] accord.invoice_sender_picker — The send dialog has a
    sender picker, shown when more than one connected account
    exists. Built 30 Sept but only exercised with one account;
    the dropdown path is unverified. When a second account is
    connected (e.g. a personal one), test that choosing it sends
    from that address. The backend (getTransporter fromAccountId)
    is done and rejects an unknown account rather than falling
    back. Raised 30 Sept.

[x] session-20260930-app-testing — DONE 30 Sept. The day began as a
    check of the chat feedback loop and became the first real
    user-path test of the whole app. Every bug found was found by
    USING the app — signing up, unlocking the vault, uploading a
    logo, sending an invoice — not by reading code. The pipeline
    stayed green (10/10) throughout.

    Found and fixed:
      - Vault PIN unlock blocked on iOS by a WebAuthn probe. Every
        iPhone user with a PIN backup was locked out. Removed the
        probe. Commit 27feca6.
      - Add-to-home-screen prompt showed the wrong icon and assumed
        Safari's old layout. Made generic. Commit 86e9c46.
      - Logo upload failed: middleware ran crypto on a request with
        a body, breaking formData; then the file input was hidden in
        a way iOS ignores. Fixed both. Commits 3faf854, 8b5d7fa.
      - Landing page recorded no analytics — arrivals invisible.
        Added page_view. Commit 1fc26d9.
      - Sign-in page carried stale cards, duplicated from the
        landing page. Fixed. Commit 21c1a01.
      - Metadata carried the removed "AI digital butler chatbot"
        claim. Fixed. Commit 8b9f8c5.
      - Microsoft OAuth button pointed at a route that never existed
        and OAuth was unconfigured. Hidden. Commit 3d072c8.
      - Email sent from contact@bosly.app, not the user's account.
        Now prefers the user's account; server fallback removed
        entirely. Commits a918a00, 440f575.
      - Invoice email carried bank details and attached nothing. Now
        a short covering note with the full invoice PDF attached,
        built client-side. Commits a264774, 4d88c8d.

    Security finding: connected email passwords stored plaintext
    (accord.email_password_plaintext).

    Lesson: a green pipeline verifies invariants, not that a flow
    works. Every real bug this day was invisible to the checks.
    See pattern-20260930-user-path-testing.

[ ] [DECISION] accord.unlogged_invoice_prompt — Chat-driven invoice detection. ORIGINALLY designed as: user asks "have I sent any invoices I haven't logged?", a server route reads the Sent folder and returns metadata only, the browser asks which to log. NEEDS RE-FRAMING: the chatbot is now a workflow engine without an LLM. Two options: (a) a workflow engine recipe that asks the browser to scan the Sent folder client-side; (b) wait for the local model. Lean: (a), since it's a deterministic pattern (read emails, count, ask browser to compare).


[ ] [DECISION] accord.follow_up_prompt — Chat-driven follow-up. ORIGINALLY: user asks "which invoices need chasing?", the browser identifies overdue invoices from decrypted data, prompts to send, builds emails client-side. NEEDS RE-FRAMING: same shape as above. This is a workflow engine recipe, not an LLM feature. The browser does the identification; the workflow engine handles the intent.


[ ] [LIVE] accord.wellness_amount_check — Client-side anomaly check. ORIGINALLY: the browser computes per-client averages from decrypted data and surfaces anomalies locally. This is a workflow engine pattern. No LLM needed. Still valid as designed — the browser does the computation.


[ ] [LIVE] accord.email_relay_encryption — Option D for the email relay.
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

[x] accord.no_cwd_for_data — invariant check that no code writes
    persistent data via process.cwd(). Motivated by the 54-file
    fix on 19 Sept 2026 (Next.js standalone chdir).
    Done 20 Sept. Written as tests/invariants/no-cwd-for-data.ts,
    the 10th sub-check of accord.invariants. Flags a file only if
    it has both process.cwd() and a write-ish call, and does not
    import @/lib/dataDir. First run found one offender:
    lib/pa/store.ts. Resolved by archiving PA to legacy/ (46
    files). Also caught three live components fetching archived
    PA routes (route-referential-integrity), which led to a
    ChatDrawer cleanup. See fact-20260920-no-cwd-invariant-scope
    and pattern-20260920-archive-reveals-coupling.


[x] ops.monitor_runtime_checks — fold the runtime checks from
    bosly-smoke-test (app responding, security headers, PM2
    online, database reachable, page loads) into bosly-monitor.
    Retire bosly-smoke-test once done.
    Done 20 Sept. Also fixed a separate defect: the monitor
    script's shebang was on line 3 (two leading blank lines),
    so the kernel had been running it via dash since 15 Aug.
    It exited at `set -o pipefail` and did nothing. Silent for
    36 days. See incident-20260920-monitor-shebang-silent-failure.
    The five folded checks all pass on current state.

[x] ops.scripts_dir_audit (Accord) — DONE 21 Sept. scripts/ had
    25 files across multiple eras. Three live (test-fast.ts,
    migrate.sh, postbuild.sh). Retired 16 to legacy/scripts/:
    three production-affecting test scripts (e2e-full-test.ts,
    accord-test.ts, seed-test-data.sh), three superseded
    (bosly-monitor.sh, command_router.py,
    behavioral-checksum.sh), and ten probably-dead. Deleted
    __pycache__/ and three 1-byte .bak files. Same pattern as
    the /usr/local/bin/bosly-* audit on 17 Sept.

[x] ops.scripts_dir_audit (Accord) — DONE 21 Sept. scripts/ had
    25 files across multiple eras. Three live (test-fast.ts,
    migrate.sh, postbuild.sh). Retired 16 to legacy/scripts/.
    Deleted __pycache__/ and three 1-byte .bak files. Same
    pattern as the /usr/local/bin/bosly-* audit on 17 Sept.

[ ] [LIVE] accord.seo_ai_discoverability — Make Bosly discoverable
    to AI systems and search engines. Priority order, highest
    value first:

    1. [DONE 23 Sept] Cloudflare crawler check. Found GPTBot
       and ClaudeBot returning 403 from Cloudflare's edge
       (blocked before the request reached the site, despite
       robots.txt explicitly allowing them). Unblocked all AI
       crawlers, then selectively re-blocked Bytespider
       (ByteDance) and CCBot (Common Crawl). Current state,
       verified by curl 23 Sept:

         ALLOWED: GPTBot, ClaudeBot, PerplexityBot,
                  Google-Extended, OAI-SearchBot, ChatGPT-User,
                  Claude-User, Applebot, Applebot-Extended,
                  DuckAssistBot, MistralAI-User, Meta-ExternalAgent
         BLOCKED: Bytespider, CCBot

       Cloudflare's "always allowed" list (configured under
       the block response settings) includes /robots.txt,
       /llms.txt, /llms-full.txt, /sitemap.xml, and
       /.well-known/*. Even blocked crawlers can read those.
       Note: /mcp (Model Context Protocol) is also on the
       default list.

       Impact: the site was unreachable by GPTBot and ClaudeBot
       for an unknown period. It's now visible to every major
       AI crawler and assistant. This is step 1 of 4.

    2. llms.txt + llms-full.txt. Static files in public/.
       Emerging standard. Low cost, low risk, forward-looking.

    3. JSON-LD schema markup:
       - Organization on the homepage
       - SoftwareApplication on the product page
       - FAQPage if there's an FAQ section
       - Product/Offer if pricing is shown

    4. RSS/JSON feeds — deferred until there's a blog or
       changelog. Check whether /changelog is a real page
       before deciding.

    llms.txt + schema are the highest value for the least
    effort. The Cloudflare check is the gate.

[ ] [LIVE] accord.middleware_public_routes — The middleware's
    isPublicRoute list is a manual enumeration of every public
    URL. It drifts as the app grows: /sitemap.xml was added as
    a route but never added to the list, so crawlers got
    redirected to sign-in for an unknown period. Same class as
    the delete route's manual table list. Options: (a) make
    public routes declarative (everything in a marketing/ route
    group is public, for example); (b) add a check that flags
    new routes not on the list. Motivated by the 23 Sept
    sitemap discovery.

[x] ops.crlf_line_endings — DONE 23 Sept. 57 files had CRLF line endings and/or UTF-8 BOMs. All normalised to LF, no BOMs. Most importantly: deploy.sh and restore-bosly.sh had CRLF, so their shebangs were '#!/bin/bash\r' — the kernel reads that as 'bash\r' and refuses to run them. Same class as the bosly-monitor shebang bug. Verified: zero CRLF, zero BOMs, typecheck clean. Some shell scripts in the repo
    have Windows line endings (CRLF). scripts/postbuild.sh has
    them: its trailing || true guards fail with "$'true\r':
    command not found". Cosmetic for the cp commands, but the
    guards are broken. Check all .sh files and normalise to LF.

[ ] [GATED] accord.social_claude_disclosure — The social media
    drafting tool sends the content brief the user writes to
    Anthropic's Claude API (app/api/social/generate-ideas and
    generate-captions, using CLAUDE_API_KEY). This was live
    for months and no document mentioned it. The privacy
    page, the FAQ, the README, and the Accord all claimed no
    cloud AI of any kind. All four were corrected 27 Sept.
    What still needs doing:

      - Decide whether to sign a data processing agreement
        with Anthropic. Until one is in place, the privacy
        page says the text is processed under Anthropic's
        standard API terms, which is true. With a DPA in
        place, the page can state Anthropic does not train
        on the data.

      - Check whether any other feature has an undisclosed
        external AI or third-party connection. The lesson
        from this one is that we assumed, we did not audit.

      - Decide whether the local model replaces the Claude
        connection (per Article IV 4.9), or whether the
        Claude connection stays and Article IV 4.9 is
        revised.

    Related: accord.doc_consistency_audit, gov.claim_invariants
    (which would catch this class of drift if it existed).
    Estimate: half a session for the DPA decision and the
    audit of other connections.

[~] gov.claim_invariants — BUILT 3 Oct, registered in the fast
    tier. checks/claim_invariants.py checks the free-pill list:
    it extracts the list from five docs (ACCORD.md, the FAQ,
    llms-full.txt, llms.txt, layout.tsx) and compares each to
    lib/tiers.ts FREE_FEATURES. It checks structured claims —
    lists, names — not prose. First run: 0 disagreements.

    It would have caught the Accord's inbox line, which said the
    inbox was paid; fixed an hour before this check existed.
    That was the fifth instance of this class in two days.

    Next claim families to add: the encryption scope (five of
    nine pills), the paid-pill list, and any route names stated
    in docs. All structured; all mechanical.

    Original entry follows.
    A new class of Gov check: verify
    that the documentation matches the code. The docs (privacy,
    terms, safety, transparency, llms.txt, llms-full.txt, FAQ)
    make overlapping factual claims. The code changes underneath.
    Nothing catches the drift. Report-only initially; fail the
    pipeline once calibrated. Predecessor to accord.doc_
    consistency_audit. Motivated by the Kyber discovery (below).

    ARGUMENT, 1 Oct. Four findings in one day, all this class:
      - the FAQ and billing card said the inbox was paid
      - llms.txt / llms-full.txt described a bot retired 24 Sept
      - parse-statement and tax-pack comments said "free"
      - the tier-sweep plan entry said the check was not
        registered when it was
    None was a crash. Each was two parts of the system
    disagreeing, invisible to the checks. This is the check
    that would catch them. Build it.

[~] accord.password_recovery_gap — PARTIAL FIX 24 Sept. The
    autoComplete="new-password" attribute was added to the signup
    form, and a warning about saving the password. Browser now
    offers to save. Remaining: the recovery flow still requires
    the account password, so a user who loses it cannot recover
    even with the phrase. Options: (a) recovery flow also resets
    the password after phrase verification; (b) password reset by
    email, independent of the phrase. (b) is probably correct but
    needs SMTP-from-server work. See accord.face_id_recovery for
    the related design.

[ ] [GATED] accord.face_id_recovery — Build Face ID + PIN recovery as
    a real feature. Currently "Face ID recovery" in the
    ceremony and vault reminders describes the browser's
    password manager prompting for Face ID to autofill the
    PIN. Bosly itself never does a Face ID check; the PIN is
    what decrypts the backup. The copy has been corrected 24
    Sept to say so. Building the real feature would mean a
    WebAuthn credential registered alongside the PIN backup,
    used to authorise the decrypt-with-PIN flow without the
    PIN ever being stored in a password manager. Bigger than
    it sounds: passkey registration, server-side verification,
    re-flow of the recovery UI. Not on the 3 Oct path.

[x] accord.bot_security_hardening — DONE 24 Sept. Four
    plaintext-exposure holes in the bot closed:

      db-query.ts:
        - Removed 'User' from allowed models. Querying it
          exposed password hashes, OAuth tokens, password-
          reset and email-verification tokens, and the key
          backup.
        - Forced the session user's ID into the where clause.
          Previously the code only set it if the LLM hadn't
          supplied one, so the LLM could override.
        - Removed 'include'. It bypassed the model allowlist
          by permitting arbitrary relation traversal.

      tools.ts:
        - Added an endpoint allowlist to api_call. Previously
          it could hit any internal route, including
          /api/inbox/messages/get (full email body),
          /api/settings/export, and /api/user. Now limited to
          eight write-only actions.

      memory.ts:
        - Stopped writing plaintext to ChatMemory.summary and
          .keyFacts. The function is now a no-op. The encrypted
          ChatMemory.encryptedMessages path is untouched.
        - Stopped writing and reading plaintext MemoryFact
          entries.

    This is interim hardening, not the redesign. The bot is
    narrower but not yet correct. The real work is
    accord.zero_access_bot_design (below).
    Motivated by Copilot's 24 Sept audit, which found that
    three of four bot tools exposed plaintext.

[x] accord.workflow_engine — DONE 24 Sept. Committed across six steps (a4f4beb, 915806f, 3c9ae6a, d31e879, 8328f48, 8a330a1). The engine replaces chatWithTools with a deterministic workflow dispatcher. Nine workflows live: today, hours-this-week, overdue-invoices, briefing, relationships, wellness-check, check-conflict, scan-inbox, enrich-contacts. All metadata-only where content isn't read. No LLM. No cloud AI. Three callers: /api/chat (all nine), the calendar editor (check-conflict), the inbox pill (scan-inbox), the contacts pill (enrich-contacts). Tests: scripts/test-all-workflows.ts, scripts/test-check-conflict-pill.ts, scripts/test-scan-inbox.ts, scripts/test-enrich-contacts.ts. Engine passes the fast tier (11/11 invariants).
    Original task description:
    Build the server-side deterministic layer that answers most user questions without an LLM. This is the product, not the chatbot. It handles: intent classification (expand from the current 4-class version in lib/chat/helpers.ts), the workflow catalogue (every known task Bosly can do), metadata arithmetic (counts, sums, comparisons over plaintext metadata), the vault bridge (how the engine asks the browser for content), and the response format. The chatbot becomes one interface to this engine, not the thing itself. No cloud AI. No Civo. When the local model exists, it plugs in as a fifth action: phrase(context, intent). Predecessor for accord.encrypt_all_pills and accord.tier_enforcement. Estimate: 2-4 focused days.
    INPUT: bosly-gov/docs/WORKFLOW_ENGINE.md — the map of
    all ten workflows, their current state, and their
    metadata requirements.
    from "reads the database" to "composes queries, the
    browser executes them, the bot reasons about outcomes."
    The shape:

      db_query      -> browser_query (aggregate only)
      api_call      -> propose_action (fixed commands)
      email_search  -> browser_search (opaque IDs)
      propose_invoice -> keep, tighten

    Also: move ChatMemory.summary and .keyFacts to the
    browser. The server holds only opaque references.
    Deliverable: a protocol spec, not code.
    Predecessor for accord.encrypt_all_pills.
    Estimate: 2-4 focused days of design.

[ ] [GATED] accord.encrypt_all_pills — Extend client-side encryption
    to the six remaining pills. Each pill's migration preserves
    the METADATA schema (Category A operational + Category B
    analytical) and encrypts everything else (Category C
    content). The schema is defined in the Accord Part III and
    in the design doc from 24 Sept. Six pills:
      - Contacts   (plaintext: status, kind, isBusiness,
                    lastContactAt)
      - Calendar   (plaintext: startTime, endTime, isAllDay,
                    status, isDone)
      - Cards/tasks (plaintext: status, priority, dueDate,
                    dueAt, completedAt)
      - Finance    (plaintext: date, type, category, book,
                    reviewed)
      - Inbox      (plaintext: date, accountId, isRead,
                    hasAttachment, kind) — most complex, email
                    is on the IMAP server. NOTE 24 Sept: the
                    inbox cache currently uses a SERVER-side key
                    (ENCRYPTION_KEY), not the user's vault key.
                    Migrating this pill changes the encryption
                    model, not just the metadata schema. See
                    accord.inbox_pill_encryption below.
      - Social     (plaintext: platform, status, scheduledAt)
    Each migration follows the invoice pattern: schema change
    (add encryptedData Json?, delete content columns), route
    hardening, client-side encryption in the pill, LLM/workflow
    prompt update, contract file update.
    BLOCKED ON: accord.workflow_engine. Do not migrate a pill
    until the workflow engine's metadata requirements for that
    pill are finalised.
    Estimate: 6 sessions, one per pill.


[x] accord.accord_revision — DONE 24 Sept. ACCORD.md bumped to v1.3.0. Added Part III — Where Bosly Is Today, listing what's encrypted (invoices, health, chat memory), what's plaintext (contacts, calendar, cards, finance, conversations, client patterns), what the bot can and can't do post-hardening, and what's not yet built. Existing parts shifted: What's Planned is now Part IV, Amendment is Part V. Also updated the Preamble, Article 1.1, and Article 6.2. The document now reads as a target with an honest progress marker. Revise the Accord to reflect
    the direction: keep the target (everything encrypted),
    add a "where Bosly is today" section listing what's
    migrated and what isn't. The Accord is a promise with
    a progress marker, not a description of the current
    state.
    Estimate: half a day.

[ ] [GATED] accord.inbox_pill_encryption — Move the inbox cache to
    encryption with the user's vault key. Currently the cache
    at dataPath('.data', 'inbox', 'cache') is encrypted at
    rest with ENCRYPTION_KEY — a server-side key. The server
    can read every email subject whenever it wants. The
    InboxPill fetches subjects in plaintext and holds them
    in useState.
    This is not just a schema migration. It changes the
    encryption model of the pill. After this:
      - The cache is encrypted with the user's vault key
      - The browser decrypts on demand
      - Phase 1 of scan-inbox moves to the browser
      - The route-level reads become ciphertext-only
    BLOCKS: the browser-side scan-inbox (Phase 2 — a future
    improvement, not the current shipping version). The
    server-side scan-inbox workflow (Phase 1) shipped 24 Sept
    as workflow #8, reading subject lines from the encrypted
    cache. It does not need this migration. The migration is
    still worth doing for the encryption-model reason above.
    Part of: accord.encrypt_all_pills (the Inbox entry).
    Estimate: 2 sessions (schema + client + route).

[ ] [DECISION] accord.kyber_status_decision — The immediate doc
    problem is fixed. The "quantum-resistant encryption"
    claim was removed from llms.txt and llms-full.txt on
    23 Sept, and from README.md on 26 Sept (was still in the
    Accord summary list as if it were a current feature; now
    says "Planned. Not yet wired into any user flow"). The
    README also gained a short paragraph above the list
    explaining that the Accord describes a direction, not a
    current state.

    Doc fix half DONE 23-26 Sept. Remaining: the decision
    itself — options (a)/(b)/(c) below.

    The decision itself is still open. lib/crypto/kyber.ts
    exports a full API (generateKyberKeyPair, encapsulate,
    decapsulate, isKyberAvailable) and is not called from
    anywhere. The encryptedKyberPrivateKey field is written
    as "" at signup. No user data is protected by Kyber.
    Options remain: (a) finish wiring it up; (b) leave the
    claim out until it's wired; (c) soften to
    "quantum-resistant encryption available". Lean was (b)
    now, (a) as a future item. The (b) half is done; the
    decision is whether to commit to (a) as a scheduled
    feature or drop it from the Accord entirely.

    Original finding (23 Sept): the claim appeared in
    llms.txt, llms-full.txt, and possibly elsewhere. The
    kyber code exists but no user data is protected by it.

[ ] [LIVE] ops.ico_registration — Register with the ICO. Not done yet.
    When done, update /privacy and the FAQ to state it. Until
    then, both documents must not claim registration.

[~] accord.doc_consistency_audit — SECOND PASS 26 Sept. The privacy page still described a Civo integration that stopped existing on 24 Sept, and said communication data is "stored encrypted" when it is only encrypted while a session key is loaded. Six corrections to privacy/page.tsx. The FAQ pricing answer and the BillingSettings cancel copy also described an AI assistant that no longer exists; both corrected. The README summary list was corrected as well.

    Remaining: (a) re-add ICO registration claim once ops.ico_registration completes; (b) the kyber decision (see accord.kyber_status_decision) affects whether the quantum claim ever returns; (c) full history of findings: Read every document that
    makes factual claims about Bosly (privacy, terms, safety,
    transparency, llms.txt, llms-full.txt, FAQ) and produce a
    table: claim, where it appears, is it true. Fix the ones
    that aren't. Immediate predecessor to gov.claim_invariants.
    Findings so far (23 Sept):
      - /safety says "EU data residency (Ireland AWS)" — stale,
        should say UK, self-hosted mini PC.
      - /safety says "31-table cascade audit trail" — the
        delete route now covers 47 tables in a transaction.
      - /privacy says "Message content you process through
        Bosly's AI features may be sent to Civo's API" — needs
        to clarify that this is chat messages, not encrypted
        user data.
      - llms.txt / llms-full.txt claim quantum-resistant
        encryption — see accord.kyber_status_decision.
      - No document currently claims ICO registration — correct,
        because it isn't done.

[x] accord.faq_page — DONE 23 Sept. /faq built with 24 questions across five sections. FAQPage JSON-LD embedded. Added to sitemap, linked from llms.txt, added to middleware public routes (which was itself a bug — see accord.middleware_public_routes). Content is honest about the current state: no ICO claim, no quantum-resistant claim, honest Civo wording. Will be updated as accord.doc_consistency_audit fixes each of the underlying claims. Content drafted 23 Sept.
    Must be built AFTER the doc consistency audit, so it
    reflects true claims, not aspirational ones. Add FAQPage
    JSON-LD. Add to sitemap. Link from llms.txt.

[x] accord.tier_enforcement — DONE 1 Oct. Duplicate of
    accord.tier_enforcement_sweep, which is now complete. The
    free/paid split is enforced at both layers: the UI gates
    (Social, Finance transactions, Calendar create-invoice, Data
    health) and the routes (nine paid routes, sixteen handlers).
    See accord.free_paid_boundary.

    Original entry follows.
    Enforce the free/£25 split in
    code. Free tier: Active, Contacts, Calendar, Health,
    Invoicing. £25 tier: all of the above plus Inbox, Finance,
    Social, Data health, Chatbot. What "enforcement" means:
    the four free pills (plus Active) are always available;
    the others show a "part of the full workspace" state when
    the user isn't subscribed. No hard wall, no nag — a calm
    explanation and a link. Matches the design principle
    "discovery, not selling".
    Depends on: the pricing decision (24 Sept) being final.
    Estimate: half a day.

[x] accord.pricing_update — CLOSED 3 Oct. The premise was stale
    (no dedicated pricing page). The live tier copy is the FAQ,
    corrected 26 Sept and again 3 Oct for the inbox boundary.
    See accord.tier_copy.

    Original entry follows.
    PARTIAL. The premise is stale:
    /onboarding/activate and /onboarding/success were archived
    on 21 Sept (accord.beta_onboarding_simplification) because
    they were dead code. The live upgrade path is
    BillingSettings.tsx -> /api/billing/checkout. There is no
    dedicated pricing page.

    Done 26 Sept: the FAQ answer for "What does £25/month get
    me?" now describes the 24 Sept tier split honestly (free
    is five pills, paid adds Inbox, Finance, Social, Data
    health, and the chatbot) and no longer calls the chatbot
    an AI. The BillingSettings cancel confirmation was
    reworded from "AI features will stop" to describe the
    paid pills and chatbot. The checkout route now passes
    allow_promotion_codes: true so Stripe shows its promo
    code field.

    Still open: decide where the tier description lives
    publicly. Either a dedicated pricing page, or a section
    on the existing marketing pages. Copy for both tiers
    (accord.tier_copy) is separate and still open.
    Estimate: 2-3 hours after the placement decision.

[ ] [LIVE] gov.accord_compliance — A check that verifies the
    Accord's Part III against the code, so the Accord can be the
    source of truth rather than a document that drifts.

    FIRST VERSION (buildable now, not gated): read the pill list in
    Accord Part III, read every model with an encryptedData field
    in prisma/schema.prisma, and fail if they disagree. Confirmed
    27 Sept: the schema has encryptedData on Contact, CalendarEvent,
    Invoice, FinanceTransaction, and six Health models — five pills.
    The Accord and the plan both disagree with that list. This check
    catches the disagreement.

    SECOND VERSION (after accord.encrypt_all_pills): verify the
    metadata schemas stated in Part III match the columns left
    plaintext. Verify no content column is plaintext that Part III
    says is encrypted.

    THIRD VERSION (after gov.accord_as_source_of_truth): extend
    beyond Part III to the marketing claims — every route that calls
    an external API is named on the safety page; no user-facing
    pricing copy claims an AI feature that no longer exists.

    Runs in the fast tier. Fails when the code drifts from the
    Accord.
    Estimate: 2-3 hours for the first version.

[x] accord.workflow_catalogue — DONE 24 Sept. The workflow map at bosly-gov/docs/WORKFLOW_ENGINE.md documents all ten workflows: briefing, check-conflict, relationships, wellness-check, scan-inbox, preferences, enrich-contacts, and three fast-paths in lib/chat/helpers.ts. Each entry has what it computes, what it reads, and the verdict. UPDATE 24 Sept (evening): the engine shipped. Nine workflows live as code. preferences was confirmed dead and removed. scan-inbox Phase 1 (the original blocker) shipped as a rule-based workflow reading subject lines only. enrich-contacts shipped as the same shape. The catalogue is now the design doc for a system that exists, not a plan for one. The map also contains the user-facing transparency statement about what the server can and cannot see.
    the engine can run without an LLM. Examples:
      - "What's on today?" (calendar metadata)
      - "How many overdue invoices?" (invoice metadata)
      - "Who's overdue for a follow-up?" (contact metadata)
      - "Am I over budget this month?" (finance metadata)
      - "Is my tax deadline coming up?" (date arithmetic)
      - "What needs attention?" (Active pill aggregation)
    Each workflow is a deterministic recipe. The catalogue
    is what the chatbot uses to answer. Anything not in the
    catalogue is either deferred to the future local model,
    or handled by the browser opening a view.
    Part of: accord.workflow_engine. Tracked separately
    because the catalogue is the specific deliverable.
    Estimate: half a day to define, ongoing additions.

[ ] [GATED] accord.tier_copy — Write the pricing copy for both
    tiers. Free: "Five pills, forever free. Encrypted. No
    tracking. Run your business on it." £25: "The full
    workspace. Ten pills. Replaces five apps. Sovereign by
    design." Neither tier promises AI. Copy must be honest
    (see accord.encryption_honesty_review).
    Depends on: accord.pricing_update.
    Estimate: 2 hours.


[ ] [LIVE] ops.legal_compliance_payment — Legal basics for when
    Bosly takes payment. Not needed before 3 Oct, but on the
    plan so it doesn't become a panic when the first payment
    lands.

    To review:
      - Terms and conditions: do they cover SALES (not just
        use)? Payment, delivery of service, refunds,
        cancellation.
      - Privacy policy: covers payment data? (Stripe handles
        card details; the policy should say so.)
      - Cookie notice: accessible before checkout?
      - All three accessible BEFORE the user commits to pay,
        not only in the footer.

    To add to the site:
      - Legal business name
      - Trading address
      - Contact information
      - (UK online business requirement — Companies Act and
        Consumer Contracts Regulations.)

    To write into policy:
      - Refund and cancellation policy.
      - UK consumers have a 14-day right to cancel online
        purchases (Consumer Contracts Regulations 2013).
      - NEW: subscription contracts regime coming spring 2027
        (Digital Markets, Competition and Consumers Act) —
        more cooling-off periods, refund obligations, renewal
        notices. The current "7-day free trial, cancel
        anytime" language will likely need review.

    Threshold awareness:
      - VAT registration threshold: £85k/year. Nowhere near
        it yet.
      - ICO registration: already on the plan.

[ ] [LIVE] ops.search_visibility_basics — Connect the site to
    search engines. Free. About an hour. Flying blind
    without it.

    To do:
      - Google Search Console: verify ownership, submit
        sitemap.
      - Bing Webmaster Tools: verify ownership, submit
        sitemap.
      - Bing matters specifically because ChatGPT and Copilot
        draw from Bing's index.

    Also:
      - Check whether at least one external link points at
        bosly.app. Google needs a link from another site to
        start indexing properly. A single relevant link gets
        you indexed within hours.

    Hygiene, not growth. Stops you getting bitten; doesn't
    make people buy.

[ ] [LIVE] gov.cron_sanity_repo_wide — Extend checks/cron_sanity.py to
    scan every *.sh file in the repo (not just cron-invoked
    scripts and /usr/local/bin/bosly-*). deploy.sh and
    restore-bosly.sh both had CRLF-broken shebangs and were
    not covered by the current check. Motivated by the 23 Sept
    CRLF fix.

[x] ops.repo_root_cleanup — DONE 30 Sept. The root went from
    60+ items to the live configs, docs, and the app.

    Deleted (48 files, commit 8953452): zero-byte strays (=,
    bosly@0.1.0, bosly.db, .critical.tmp, next, node), the August
    fix-*.sh one-off scripts, 16 test-*.ts scratch files,
    tasks-*.json planning artifacts, tsconfig.tsbuildinfo, and the
    old backup dirs (_bak_accent_*, snapshots, .v2-restore-baks,
    bosly-gov-v4, .tmp). Also 69 .bak files across both repos.

    Archived, not deleted, to legacy/2026-09-30-root-cleanup/
    (commits f4c05cc, be9853f): the old v2/v3 app (src/), the
    retired PA tooling (tools/), bin/, the stray pp/ route,
    server.js/server.cjs, build-prod.sh (the type-skipping build),
    eval.ts, the August PA artifacts (PA-audit-report.md,
    pa-*.appdpa.json, pa-polish-*.txt), and the duplicate
    postcss.config.cjs.

    Removed 4 dead components (commit b796079): AddToHomeScreen
    (root version), DemoDataProvider, UsageStats, CapabilityToggles.

    Left in place: tsconfig.json's _DETACHED and _ATTIC excludes
    (both nonexistent — harmless; remove when next editing
    tsconfig).

[ ] [LIVE] ops.journey_test_outbox_check — The retired bosly-journey-test
    had one unique check: that POST /api/messages/send returns
    { pending: true } (the outbox delay). The original plan was to
    fold it into scripts/e2e-full-test.ts — but that script was
    retired on 21 Sept. So there is no host for this check. Options:
    (a) write it as a source-level check in tests/invariants/ that
    reads app/api/messages/send/route.ts and asserts the POST path
    returns pending: true; (b) close as won't-do, since the delay
    is tested implicitly every time an email is sent.
    Lean: (a). It's small and it closes the gap.

[x] ops.cron_sanity — DONE 23 Sept. checks/cron_sanity.py. Verifies every cron-invoked script has a shebang on byte 1, and every binary it calls is either on cron's PATH or provided by the script's own PATH loading. Checks /usr/local/bin/bosly-* shebangs too. Currently 19/19 passing. Registered in manifests/checks.yml. Would have caught the bosly-monitor 36-day silent failure on day 1. invariant check that every script in
    /usr/local/bin/bosly-* and every cron-invoked script in the
    repo has a shebang on byte 1, and that every external binary
    it calls (node, pm2, psql, curl) is reachable under cron's
    minimal PATH. Motivated by the 2026-09-20 bosly-monitor
    incident. See incident-20260920-monitor-shebang-silent-failure.

[x] ops.journey_test_overlap — review bosly-journey-test against
    scripts/e2e-full-test.ts. Same treatment.
    Reviewed 20 Sept. Result: journey-test is 90% redundant —
    landing page, signup, session, and onboarding are all covered
    by e2e-full-test.ts. One check is unique: POST
    /api/messages/send must return { pending: true } (outbox
    delay). Nothing else asserts that. Archived to
    bosly-legacy-archive/. The outbox check is scheduled as
    ops.journey_test_outbox_check.
    See decision-20260920-retire-journey-test-preserve-outbox-check.

[x] ops.commands_cleanup — /usr/local/bin/ had 43 bosly-*
    commands from the August architecture. Most are pre-migration
    dead code. Audit each: keep, retire, or wrap as a check.
    Document the outcome. Note: bosly-audit, bosly-health,
    bosly-diagnose-v5 are superseded. bosly-monitor,
    bosly-analytics are kept. bosly-evolve is pending replacement
    (see gov.evolve_loop_usage).

[ ] [LIVE] accord.connection_providers — UPDATE 3 Oct:
    app/api/connect/google/** is archived to
    legacy/api-dead-20261003/connect-google/. It was unreachable
    after the calendar's Google button was removed, and broken
    besides. Rebuild it with the rest of the providers if Google
    is worth configuring — and decide where OAuth tokens live
    first.

    Original entry follows.
    The old social connections
    page (app/(settings)/connections/page.tsx) was removed 3 Oct,
    with its app-settings card and two overpromising copy lines.
    It offered Facebook, Google, Microsoft, and WhatsApp; all four
    were dead:

      - Google calendar: the callback writes ChannelAccount fields
        that do not exist (provider, accessToken, refreshToken,
        tokenExpiresAt) and a composite key the schema does not
        define. Needs a decision first: where do OAuth tokens live?
      - Microsoft: routes deleted with the Azure integration 3 Oct.
      - Facebook / WhatsApp (Meta): abandoned — as painful to set
        up as Azure. The WhatsApp guide linked to
        developers.workspace.com, which is not a real domain.

    The live connections page is the Connections pill in /settings,
    which renders the email form. Rebuild each provider against the
    current schema if it is ever worth configuring. Raised 3 Oct.

[ ] [LIVE] accord.password_reset_ui — A signed-out user who has
    forgotten their password cannot recover. The API exists and
    works: POST /api/auth/password-reset generates a token and
    emails it; PUT verifies and sets a new password. The token is
    now SHA-256 hashed (3 Oct). But nothing in the app reaches any
    of it.

    Specifically:
      - No 'Forgot password?' link on /signin.
      - No page consumes the token. The email links to
        /signin?reset=TOKEN, and /signin reads only `reason`,
        not `reset`.
      - grep for passwordResetToken / resetToken in app/ and
        components/ returns nothing.
      - app/signup/page.tsx:137 says it plainly: 'Bosly can't
        reset it if you lose it.'

    What exists: change-password while signed in (via settings).
    What does not: reset while signed out.

    To build: a reset page (e.g. app/signin/reset/page.tsx) that
    reads ?token=, posts to PUT /api/auth/password-reset, and
    redirects to /signin; a 'Forgot password?' link on /signin;
    the email link corrected to the new page; the page added to
    the middleware's public list.

    Raised 3 Oct. A founding member who forgets their password is
    locked out, so this matters before the offer grows.

[ ] [LIVE] accord.legacy_js_audit — there is a substantial body of
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
TOWARD A CLEAN, LEGIBLE SYSTEM
================================================================

Not a plan item. A direction. Everything else in this plan
serves it.

The goal: Bosly's code, documentation, and behaviour should say
the same thing. Where they don't, that difference should be
visible and tracked. Not because the code will be published —
because a system that says what it does and does what it says
is the foundation everything else sits on.

This is the work that makes Bosly safe to grow.

----------------------------------------------------------------
1. THE WEEKLY HEALTH REPORT
----------------------------------------------------------------

[ ] [LIVE] gov.weekly_health_report — A single email, every Sunday
    evening, telling the whole story of the system. It always
    arrives. A quiet week is still reported as a quiet week.
    Silence is ambiguous — a report that sometimes doesn't
    show up is indistinguishable from one that failed, and
    three systems this month have silently stopped (bosly-
    monitor, the memory orphans, usage tracking). Arrival is
    information.

    The email is detailed, not a summary — the point is that
    reading it means not having to go and find the report
    elsewhere. Seven sections:

      Pipeline state:  every check, pass/fail, duration
      Runtime state:   is the app up, is the database
                       reachable, did email sync run, did
                       the monitor run last night
      Data state:      user count, row counts per major
                       table, anomalies (test data, orphaned
                       rows, tables empty that should have
                       data)
      Doc state:       every factual claim in the docs,
                       checked against the code
      Plan state:      open items, done-but-untested, items
                       older than 30 days
      Memory state:    new entries this week, anything
                       flagged
      Change log:      commits, deploys, config changes
                       this week

    Cadence: Sunday evening. Email to the founder. Not on the
    fast tier — it reads and reports, it doesn't verify.
    Build it in one focused pass, not incrementally.

----------------------------------------------------------------
2. THE CLAIM CLASS OF CHECKS
----------------------------------------------------------------

The class that has produced eight findings in two days. Each
of these closes one instance.

[x] accord.delete_route_coverage — DONE. The template for
    this class: parses the schema, parses the route, diffs
    the sets.
[x] gov.cron_sanity — DONE. Shebang and PATH verification
    for cron-invoked scripts.
[~] accord.doc_consistency_audit — FIRST PASS DONE.
• gov.claim_invariants — see the primary item above.
• accord.naming_honesty — see the primary item above.
• accord.stub_detection — see the primary item above.
• gov.plan_tracks_known_gaps — see the primary item above.
• accord.middleware_public_routes — see the primary item above.
• gov.cron_sanity_repo_wide — see the primary item above.

----------------------------------------------------------------
3. CLEANLINESS FOR LEGIBILITY
----------------------------------------------------------------

Work that adds no features and fixes no bugs. It makes the
system readable.

• ops.repo_root_cleanup — see the primary item above.
• accord.legacy_js_audit — see the primary item above.
[x] ops.scripts_dir_audit_keep — DONE 3 Oct. Of the 16 files in
    Keep's scripts/, five were archived (clean-universe, fix-snapshots,
    reset-asset-flags, reset-fresh, expand-universe — referenced by
    nothing). Kept, after reading each: update-prices (in package.json
    dev), run-tests.sh (in package.json test), seed-full-universe
    (fresh-DB seeding), seed-activities and tag-activities (seeding and
    the correction tool), policy-report (read-only ethical report), and
    test-prices (a price-feed diagnostic, not a test). Also removed
    cron-daily.sh (pointed at a Mac that no longer exists) and
    update-prices.ts.tmp (54 bytes, committed in August). Keep's
    tsconfig now excludes legacy/ so archived code is not typechecked.
    Commits d92e8204, 3ea316ad, b1371dc0.

[x] ops.scripts_dir_audit_gov — NON-ITEM 3 Oct. bosly-gov/scripts/ is
    empty. Nothing to audit.

[x] ops.bak_file_sweep — DONE 3 Oct. Ten .bak/.backup files removed
    across the three repos. None was tracked by git, and .bak is
    gitignored in bosly-1.0 and bosly-gov, so they will not return.

[x] ops.readme_accuracy_all — DONE 3 Oct. bosly-1.0/README.md reduced
    from 193 to 152 lines: the tech stack, paths, pill order, LLM chat,
    and tier model had all drifted (AWS, Facebook, an AI chat that was
    retired, £15 instead of £25). Reduced to the mission, the Accord's
    principles, the design system, and the lessons. bosly-keep/README.md
    was already accurate and is unchanged. bosly-gov/README.md was fixed
    21 Sept. Commit 611cab3.

[ ] [LIVE] keep.scripts_typecheck_excluded — Keep's tsconfig.json
    excludes `scripts`, so the verify suite
    (scripts/diagnostics/verify-*.ts) is never typechecked by tsc. The
    tests pass and assert, so nothing is broken — but a type error in a
    verify script would not surface until runtime. Same shape as the
    app's excluded directories (gov.tsconfig_excludes). Decide:
    un-exclude and fix what surfaces, or record why it stays.

----------------------------------------------------------------
THE PRINCIPLE
----------------------------------------------------------------

A system that says what it does and does what it says is not
a feature. It's the foundation. Every product decision, every
new pill, every user, sits on top. If the foundation is soft,
everything above it is at risk.

This is the work that makes Bosly safe to grow.

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
  - Confirmed 27 Sept: five pills export as ciphertext (Invoicing,
    Contacts, Calendar, Finance, Health); four export as plaintext
    (Active, Inbox, Social, Data health), plus the user record.
    Any description of "your export" must account for both.

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
                      pipeline. See gov.evolve_loop_feedback and
                      gov.evolve_loop_usage below.

Retirement is by neglect - the scripts stay on disk but stop
being referenced or run. When the replacement lands, remove.

Note: none of these commands were being used regularly, because
they had to be run manually. The pipeline runs automatically at
5am. That alone justifies the transition.

================================================================
SOCIAL MEDIA PLAN
================================================================

Cadence: Friday reel (default). Saturday reel optional — a
different format from Friday's. No Saturday if energy is low.

Format guide:
  - Talking head = personal stories (Thread A)
  - Path walk + voiceover = arguments (Thread B)
  - Don't stack two of the same in a weekend. They compete.

Review: Thursday evening for Friday's post. Saturday morning
for Saturday's post, if posting. Otherwise, walk away.

Engagement: post, stay active 30 min, check at 1hr and 2hr,
reply to every comment in that window, then leave it alone.

Hashtags: 3-5 max, specific to the post, front-load the caption
with natural keywords before the tags.

================================================================
POSTED (keep for recycling — earliest recycle March 2027)
================================================================

29 Aug (Fri) — Product intro
  First reveal. What Bosly does. Not on the app stores.

4 Sept (Sat) — Car impounded / pulled over
  Got pulled over, car impounded. ADHD tax.
  Strongest post so far.

5 Sept (Sat) — Path walk, data privacy
  Walking a path, voiceover. Argument that our data isn't
  really ours despite the laws. 231 views. Format worth
  keeping for arguments.

12 Sept (Fri) — Meds inconsistency
  Taking meds, forgetting, sometimes double-dosing.
  Asked for advice. Audience gave real, specific advice.
  Strongest engagement. Proof that the audience participates
  when asked for a specific kind of help.

19 Sept (Fri) — Intro repost
  Reposted the intro reel. Neurodiverse gardener, building
  Bosly, not on app stores because 30%. Added a pin comment.

================================================================
SCHEDULED
================================================================

26 Sept (Fri) — Unsent invoice / lost client
  Format: talking head
  Four weeks angry at a client for not paying.
  Sent follow-up. Nothing. Sent another. Less patient.
  Nothing. Drafting angry emails in my head.
  She replied: "I never got your invoice."
  Checked drafts. It was sitting there. Never sent.
  Lost the client.
  Cost: not the money. The relationship.
  Comment bait: "Tell me your worst version of this — the
  thing you were self-righteous about, then found out was
  your fault. And if you've got a system that stops you
  doing it, share it. Mine clearly isn't working."

2 Oct (Fri) — Founding Members ask
  Format: talking head
  Context: audience knows Bosly exists. This isn't a reveal.
  Been working on it. Running my own life through it.
  Need to know if it works for other ADHD brains.
  Looking for 20 people to help shape what it becomes.
  What they get: free AI features for life. £15/mo instead
  of £25. Not a discount — a seat at the table.
  What you get: real feedback from real users before launch.
  Framing: same shape as the meds post. Asking for help
  with a specific thing, not selling.
  Comment bait: "If you're ADHD and running your own thing,
  comment 'IN' or DM me. Tell me which of my fuck-ups you
  related to most — that's how I know you're the right fit."
  Note: this post goes up on Stories too. Repeat it over the
  following week in different forms.

10 Oct (Fri) — Path walk, no app stores
  Format: path walk + voiceover
  Argument: app stores ask for 30% and a hundred pages of
  terms nobody reads. The trade is your data for convenience.
  Bosly isn't on them because that trade breaks the promise.
  Not about the 30% alone — about what agreeing to it means.
  Turn: the data never leaves your control. That's the whole
  reason.
  Optional comment bait: "Would you give up an app store
  listing to keep your data private? Genuine question."

17 Oct (Fri) — Path walk, quantum readiness
  Format: path walk + voiceover
  Argument: most apps encrypt with today's standards. Quantum
  computers will break those in 10-15 years. Data stored
  today in plain AES becomes readable in 2040.
  Bosly encrypts with post-quantum cryptography. Not because
  it matters now. Because it will matter then.
  Turn: building for 2040, not 2026.
  Optional comment bait: "Do you care about encryption that
  survives the next 15 years, or is today's enough?"

================================================================
BACKLOG
================================================================

Strong — pick from these first
--------------------------------

Almost deleted the app
  Broke it trying to fix a build issue. Hours on it. Nearly
  gave up. Restored from git and rebuilt. Works now.
  Lesson: git is the safety net, panic is not the plan.

Found my own app was lying
  Discovered invoices were stored in plaintext despite the
  encryption promise. Fixed it. The discovery was worse than
  the fix.

"I run the server. I still can't read your data."
  Root access. Can see the database. Can't read a single
  invoice, message, or health record. Design, not accident.

Moved off AWS to a mini PC
  Moved the whole thing to a box in the spare room. Not
  about cost alone. About control and knowing where the
  data lives.

Passwords in my own logs
  My code was printing credentials into a log file. Had
  been for weeks. Found it by accident. Fixed it. Now
  there's a check.

Building with AI — what it actually feels like
  Six months of working with an AI to build software.
  Honest version. The good, the frustration, the
  symbiosis.

The day I realised I wasn't going backwards
  Felt like I was losing ground. Then realised I was
  seeing reality for the first time. Different thing.

Good — solid material
----------------------

Audit score 53% → 157%
  A code quality tool gave me 53% in July. Today it's
  157%. Number went up because I stopped guessing and
  started checking.

66 tests, all passing
  Wrote a test suite from scratch. Six months ago I didn't
  know what a test was. Runs every night now.

The warrant canary
  A page on the site that updates daily. If it stops,
  that's a signal. Most people don't know what it is.

Wrote 24 posts in one sitting
  Hyperfocus. Got it all done. Didn't post any of them
  for weeks. The writing isn't the hard part.

The first viral reel
  One post got 2,770 views. Usual posts get 200. The one
  that worked was the most embarrassing.

The free invoice tool
  Built a standalone invoice tool. No signup, no email,
  no catch. It's on the site. Why it's built that way.

Later — when the audience is bigger
----------------------------

423 test users
  Database has 423 users. Nearly all robots from the test
  script. Funny. Also a real point about testing.

The 10-clients batch flow
  Designed a flow where the AI can't see client names but
  can still help you invoice. Novel. Worth a post once
  people understand the encryption model.

The chatbot explains what it can't see
  The transparency principle as a feature.

Ethical investing in Keep
  Second product. Won't let you buy certain companies.
  Why.

30-day build summary
  Moved off AWS, built a test pipeline, found 40 bugs,
  cleaned six months of debt. What I learned building
  alone.

Every week, find the moment you were wrong about
something. Post about it. That's the whole strategy.

================================================================
RECYCLING
================================================================

Earliest safe recycle: March 2027 (6 months after the
first posts).

Ideal: 12 months.

When recycling, do NOT repost exactly. Reframe with a
new caption, or re-record the same story with a different
angle.

================================================================

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

Session 21 Sept 2026 (evening):
  - CRITICAL PATH FOR 3 OCT COMPLETE (code side)
  - crypto_fix_1 through 5 done, committed, pushed
  - user_deletion_cascade done
  - delete_route_coverage invariant added to fast tier
  - ceremony_interrupt_safety done
  - encryption_honesty_review done
  - beta_onboarding_simplification done (dead /onboarding
    pricing pages archived to legacy/onboarding/)
  - server_side_key_visibility fixed: client no longer sends
    exportedKey; server never sees key material
  - Remaining: crypto_fix_6 (browser test, manual)

Session 21 Sept 2026 (afternoon):
  - Both test accounts deleted (jr-arnott, jarmario85)
  - Browser IndexedDB cleared on founder's Mac
  - Fresh signup is the test case for the crypto fix
  - Delete-route bug found: misses 8 tables, returns
    { ok: true } even when the delete fails. See
    incident-20260921-delete-route-silent-failure.
  - New plan items: accord.user_deletion_cascade,
    accord.delete_route_coverage
  - NOTE: the fast tier currently FAILS on
    tests/invariants/crypto-recovery-roundtrip.ts.
    This is by design — the test proves the recovery
    bug is real. It will pass once crypto_fix_3 lands.
    Do not panic at the pipeline output.

Session 24 Sept 2026:
  - Bot security hardening: four plaintext-exposure holes
    closed (User model, session scope override, arbitrary
    include, plaintext memory). Copilot audit.
  - Product decision: no Civo, no cloud AI. Five free pills,
    ten paid. Names are metadata, content is encrypted.
  - Accord revised through v1.2.0, v1.3.0, and v1.4.0.
    Five-part structure. Part III: where Bosly is today.
  - Workflow map created (bosly-gov/docs/WORKFLOW_ENGINE.md):
    ten workflows documented, eight now metadata-only.
  - Five metadata-only patches landed (briefing,
    check-conflict, relationships, wellness-check, today
    fast-path).
  - scan-inbox Phase 2 (cloud LLM call) removed.
  - preferences route removed entirely (dead code).
  - enrich-contacts dead signature parser removed.
  - Discovery: the inbox cache uses a server-side key, not
    the user's vault key. New item:
    accord.inbox_pill_encryption.

Session 21 Sept 2026 (morning + midday):
  - bosly-monitor DB-check bug found and fixed (nested sudo)
  - UsageEvent confirmed empty — usage_capture_wiring added to plan
  - Crypto recovery flow found broken (3 defects, 14 ref sites)
    See incident-20260921-crypto-recovery-broken in bosly-accord
    memory. Fix plan: accord.crypto_fix_1 through 6. Invariant
    test written: tests/invariants/crypto-recovery-roundtrip.ts.
  - Gov's README identified as misleading (claims `bosly`
    launches a browser UI; it does not)
  - Workflow clarified: no terminal command talks to Gov;
    terminal reads files, chat reasons, Gov is source of truth
  - Two test users will be deleted before crypto fix lands

Session 20 Sept 2026:
  - accord.no_cwd_for_data added (10th sub-check of
    accord.invariants)
  - PA subsystem archived to legacy/ (46 files)
  - ChatDrawer and providers.tsx stripped of PA-suggestion code
  - bosly-monitor fixed: shebang, PATH, and folded runtime
    checks from bosly-smoke-test
  - bosly-monitor had been silently broken for 36 days —
    see incident-20260920-monitor-shebang-silent-failure
  - bosly-journey-test retired to bosly-legacy-archive/;
    its unique outbox check scheduled as
    ops.journey_test_outbox_check

Session 18-19 Sept 2026:
  - Full invoice encryption migration
  - Orientation command built
  - Working agreement written
  - Memory cleaned and standardised
  - 32 legacy scripts retired
  - gov.secrets_audit added

Next: accord.spaces_encryption - same pattern as invoices,
smaller surface. Then gov.evolve_loop_feedback and
gov.evolve_loop_usage. Manual invoice test
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
