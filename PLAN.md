BOSLY GOV — PLAN
Last updated: 23 October 2026

================================================================
THE SHAPE OF BOSLY  (read this first)
================================================================

Bosly Limited is the company. Five products, one platform. This
block is here so that, when you open this file and have forgotten
everything, the shape is the first thing you see. Every entry below
hangs from one of these.

  BOSLY LIMITED  (registered company, Companies House)
  │
  ├─ BOSLY ACCORD ........... THE PLATFORM. One app, three products.
  │    .vault  — public, encrypted, no assistant. The safe one.
  │    .manage — sold to small businesses: the base (£25/mo) plus
  │              toggles (the Executive, the receptionist).
  │    .founder — the founder's own instance: the whole ecosystem,
  │              the Custodian Executive, not for sale.
  │    A client logs into Accord and turns on the products they've
  │    paid for. Accord is the foundation; the rest are features of
  │    it. This is what the consultancy sells.
  │
  ├─ BOSLY EXECUTIVE ........ THE CHIEF OF STAFF. The conversation.
  │    Talk to it. Plan with it. It holds the whole of the digital
  │    side of the business — email, calls, clients, projects,
  │    leads, admin — so the founder's ADHD doesn't have to.
  │    The interface to everything. Acts, proposes, remembers.
  │    CANNOT verify its own work — see Bosly Custodian.
  │    Priority: build first. It's the founder's tool and the
  │    model for the client version.
  │
  ├─ BOSLY RECEPTIONIST ..... THE FIRST CLIENT TOGGLE. Bounded
  │    workflow: answer the call, transcribe, classify intent,
  │    book or route, log it. Built per client, priced against
  │    the human equivalent: £1,000–£1,500 build + £250–£500/mo
  │    ongoing, versus £1,200–£1,500/mo for a human receptionist.
  │    Priority: build second. January deadline.
  │
  ├─ BOSLY KEEP ............. WEALTH AND INVESTMENT. Personal now,
  │    product later. Your own portfolio tool. Cannot be sold
  │    until it is registered and compliant — years away. Needs
  │    spare money and proper testing. NOT on the critical path
  │    for January. Its bugs are interesting, not urgent.
  │
  ├─ BOSLY CUSTODIAN ........ (was Bosly Gov). THE CHECKS. The
  │    plan, the memory, the invariants, the verification.
  │    Reads what the Executive does and says whether it's true.
  │    Does NOT act. Does NOT decide whether a plan was good —
  │    only whether what was done matches what was said.
  │    Standalone, independent, un-editable by the Executive.
  │
  └─ THE GARDENING BUSINESS .  Existing income. Not a branch of
       growth — the thing the consultancy replaces. Runs on
       Bosly Accord internally, which is how Accord gets built.

THE BALANCE OF POWERS. The Executive has judgment but no restraint.
The Custodian has restraint but no judgment. Together they're a
whole. The rule:

  - The Executive proposes and acts.
  - The Custodian verifies and reports.
  - The Executive cannot verify its own work.
  - Every Executive action runs through Custodian checks.
  - When the Custodian says no, the Executive reports it. It does
    not route around it.
  - When the Executive wants to do something the Custodian has no
    check for, that is a NEW CHECK, not a bypass.

This is the same principle as the trade-idempotency fix and the
memory-schema fix: the builder wrote something that looked right,
the check caught it. The Executive will be a much more prolific
builder, and will need the Custodian more, not less.

How to use this map: find the product you are working on, then
look for entries with that prefix. Accord is accord.*. Keep is
keep.*. Custodian is gov.*. The consultancy (front door and sales)
is ops.consultancy*. The Executive is ops.bosly_executive. The
Receptionist is ops.bosly_receptionist. The principles and the
hardware plan are ops.architecture and ops.hardware_plan.

================================================================
PRODUCT DESIGN — DECIDED 20 OCTOBER 2026
================================================================

These decisions were made in conversation and are recorded here in
full, because they define what Accord is and what it is not.

ACCORD — TWO PRODUCTS, TWO PROMISES

  ACCORD VAULT — as it stands now. Nothing changes. Fully
  encrypted, the user owns their data, the developer is blind.
  Anyone can sign up and feel safe. No hosted assistant runs
  against it, so the promise stays true. Includes the health pill.

  ACCORD MANAGED — for consultancy clients from Day Zero. Bosly
  sets it up, hands over the passwords, strongly recommends the
  client changes them, and keeps backend access to monitor and
  maintain — not to read business content.

    INCLUDED IN THE BASE (£25/month):
      active, calendar, contacts, finances, settings

    IN SETTINGS, AS TOGGLES, EACH AN EXTRA COST:
      the Executive
      the AI receptionist
      anything built thereafter

    THE PRINCIPLE: the base is one product at one price. Every
    toggle is a separate product, priced per client against the
    human it replaces or the value it adds.

    THE HEALTH PILL IS NOT PRESENT in the managed instance. Not
    "switched off" — not there. Health is a vault feature. A
    business instance holds business data; the owner's medical
    records are not business data. This removes special-category
    data from the managed product entirely, which simplifies the
    ICO registration, the DPIA, and the privacy notice.

    DATA HEALTH (the security scan — leaked credentials, breaches,
    dark web) IS in the managed base, and the Executive can read
    it. It is about the business's safety, not the owner's body.

THE EXECUTIVE IS THE CHATBOT, NOT A NEW SCREEN

  Accord already has a chatbot: a conversation window in the PWA,
  client-side, with the key in the session. ChatDrawer.tsx already
  calls useVault() and decrypt() in the browser — the decryption is
  client-side today.

  The Executive is that same chat window, in managed mode, with
  tools:
    Vault: read-only. Answers questions about the user's data,
      which it can read because it is in their session. NO tools.
    Managed, Executive toggle ON: the same chat gains tools —
      read the calendar, draft the email, save a thing, call the
      scout, read the ecosystem. It acts in the client's session,
      with the client's key.
    Managed, Executive toggle OFF: the vault chatbot again.

  THE TOGGLE IS THE GUARD: tools are present only in managed mode,
  and only when the Executive is on. A vault chat can never gain a
  tool. That is what keeps the vault promise true.

THE ONE THING THAT MOVES: THE MODEL CALL

  Today the chat posts to /api/chat, a server route, so the prompt
  (and the decrypted content) goes to the server for the model
  call. Decryption is client-side; the model call is not.

  The target: the model call moves out of the server. Through a
  proxy for now (the prompt leaves the device; the key does not).
  A local model on the client's device is the direction, when the
  hardware exists.

  THE HONEST CAVEAT: a PWA's memory is not a hardware enclave. A
  determined attacker with the device unlocked could in principle
  read the key while the Executive runs. The promise is "the
  server cannot see it" — true. It is not "no one can."

THE RECEPTIONIST IS HYBRID

  A phone call needs a server to answer it. The receptionist hears
  the call, and the transcript is encrypted immediately with the
  client's key. The Executive reads it in the PWA. The server sees
  the audio; it never holds the plaintext transcript. Stated, not
  hidden.

THE TRANSPARENCY STATEMENT, shown in the managed instance

  "This is a managed Accord. The person who set it up for you —
  Bosly — can access the areas you switch on, to support you and
  adapt your products. You can see exactly what is on, switch any
  of it off, change your passwords, or remove Bosly's access
  entirely. We do not read your data unless you ask us to, and
  every access is logged."

THE CLIENT MUST BE ABLE TO LEAVE

  Change password, revoke access, and the managed instance becomes
  a vault. If they cannot, it is not consent, it is lock-in.

NOT YET

  the toggle table, the audit log, the revoke flow, the per-mode
  privacy notice, the client-side model call, the pricing per
  toggle.

THE BUILD, IN ORDER

  1. Move the model call out of /api/chat into the browser, via a
     proxy. Decryption is already client-side.
  2. Managed mode: the same chat, with the tool loop added when the
     Executive toggle is on.
  3. The tools, client-side: read_file, draft_email, save_thing,
     ecosystem_state. The server holds ciphertext and routes.
  4. The receptionist: hybrid, with the transcript encrypted
     immediately.

## FOUND — 26 Oct

[ ] gov.ingest_summary — FOUND 2 Nov. The founder works in a chat
    session as well as with the butler, and the chat writes summaries
    the butler never sees. The transition needs a door: paste a summary
    into the butler and have it PROCESS it, not swallow it — read each
    part, decide what it is (decision, finding, client, lesson), write
    it to the right store with save_memory / save_thing / plan_write,
    and REPORT what was filed and where. Refuses duplicates by id, the
    way plan_write(missing_only) does: the tool selects, so the model
    carries no list. THE CHECK: paste a known summary, assert the right
    entries appear with the right ids, run it twice, assert nothing is
    added the second time — processed, not stored.


[ ] gov.corrections_become_checks — FOUND 2 Nov. The founder is the
    tester. When the butler builds or fixes something and it is wrong,
    the founder says so. That correction is the learning event, and it
    works only if it is captured: what was wrong, why, and — where
    possible — a check that would have caught it. A wrong build that is
    not recorded is a wrong build that happens again. THE FIX: one tool,
    record_correction, that writes a memory entry typed as a correction,
    writes the cause if known, and adds or changes the check. THE CHECK:
    a correction produces a memory entry and, where possible, a check —
    or says why there is not one. This is what makes the butler learn
    from being wrong the way the founder described: it becomes more
    trustworthy every time it is corrected.


[ ] gov.plan_file_needs_splitting — FOUND 2 Nov. PLAN.md is
    400,525 bytes and read_file refuses anything over 400,000. The
    self-test found it: it read the plan to prove dispatch and got
    'PLAN.md is 400525 bytes (max 400000)'. plan_query still works — it
    derives rows in code — but any path that reads the plan WHOLE is
    now blind: a capsule writer, a human, a future tool. The plan is
    the archive and the archive is the thing that must stay readable.
    THE FIX: split. PLAN.md keeps the index, the current quarter and the
    open items; PLAN-archive.md holds the closed items and their
    evidence; plan_query reads both. The archive is not deleted — it is
    moved to where it can be read. Same rule as gov.one_pile: one pile
    is manageable, and a pile past the ceiling is a backlog nobody
    reads. THE CHECK: PLAN.md stays under the read_file ceiling, and a
    closed item is findable in the archive when plan_query asks for it.


[ ] accord.invoices_organised_by_month — FOUND 3 Nov. THE FILING
    SYSTEM. The finance invoice list is one flat list capped at 50
    (accord.invoice_list_capped_at_50). It cannot keep growing — six
    September invoices, a full October, and by next spring it is a list
    nobody reads. The founder's ask: a month/year row above the list so
    the current month is what you see, and the archive is one click
    away. NOT a filing system that moves invoices — a FILTER that groups
    them. issueDate is a plain column, so this is a server-side query,
    not a client-side scan of encrypted data. No migration, no new
    store, nothing to break.

    THE SPEC — small enough for a first butler build, real enough to
    matter:
    (1) Replace the Suggested invoices block (FinancePill.tsx ~1409)
        with ONE ROW of chips: the months that have invoices, newest
        first, plus "Suggested (n)" and "All". No taller than the block
        it replaces.
    (2) Selecting a month filters the list. The default on open is the
        CURRENT month, so Finance opens on October, not everything.
    (3) The API: GET /api/invoices?month=YYYY-MM filters on issueDate
        server-side; the 50-cap becomes per-month, so a month's list is
        complete. No month means All (paged or a higher cap).
    (4) Suggested invoices becomes a chip, not a block — the same feed,
        one click away, not always on screen.
    (5) Nothing is moved, copied or deleted. The archive is the same
        rows, filtered.

    THE STEPS (the butler builds these one at a time, each with its
    check):
      1. API: ?month= on /api/invoices, filtered on issueDate, with a
         count-returning test. Check: a month's query returns only that
         month's rows.
      2. API: the month list — GET /api/invoices/months returns the
         distinct YYYY-MM present with counts. Check: matches the rows.
      3. UI: the chip row replacing the suggested block; renders from
         the months endpoint. Check: the row renders in the same height
         and the current month is selected.
      4. UI: selection filters the list; default is the current month.
         Check: opening Finance shows the current month; clicking All
         shows everything.
      5. UI: Suggested becomes a chip that opens the suggestion list as
         before. Check: the suggestions are still reachable.
      6. The 50-cap is per-month, and All says so if it is capped.
         Check: a month with more than 50 returns its complete count.

    MUST NEVER: touch the invoice data, change a number, move a row,
    delete anything, or alter the encryption. Read and filter only.

    STOP AND ASK: if the chips need a new store, if the API shape needs
    to change, if the suggested feed turns out to be used elsewhere, or
    if anything needs the invoice data moved. The founder decides; the
    build waits.

    THE BUILD IS DONE WHEN: Finance opens on the current month; the
    chips filter; the archive is reachable; the suggestions are still
    there; the invoice data is untouched; and the checks above pass.

    THIS IS THE FIRST BUTLER BUILD. It is small, real, self-contained,
    has a clear done state, and the founder can test it. It is the
    proving ground for the build loop, not the receptionist.


[ ] gov.the_butler_says_it_checked_without_checking — FOUND 3 Nov.
    FOUNDER-REPORTED as 'gash I have run out of claude credits' — and
    found in the log. Asked 'let's name the invoice chips the October
    view', the butler replied 'I have no context for this in this
    conversation, the plan, or the business memory' — and the tool log
    shows the only call was answer_cache. It did not read the plan, did
    not search the pile, and said it had. The cache miss led straight to
    a model answer, and the model guessed its own context. This is the
    confident-and-wrong case the tool log exists to catch, and it was
    caught: 'tool call: answer_cache' with no read_file, no plan_query,
    no find_things. THE FIX: a rule — before saying you have no context,
    call plan_query and find_things; the founder's words may not be the
    plan's words ('invoice chips' is accord.invoices_organised_by_month)
    and the only way to connect them is to look. THE CHECK: a reply that
    says it checked the plan or memory must be preceded by a plan_query
    or find_things call in the same turn — readable from the tool log,
    which is why the logging came first.


[ ] gov.overnight_build_uses_batch — BLOCKED 3 Nov (needs the build loop). The build loop runs
    at night; nothing is waiting on the response. Route each turn
    through the provider's batch API for 50% off, stacking with the
    cache. THE CATCH: batch cannot do multi-turn tool use inside one
    entry, so the loop still runs turn by turn — it is each turn that is
    batched, not the whole build. THE CHECK: a batch build completes and
    its cost is logged at half the synchronous equivalent.


[ ] gov.scenario_compilation — BLOCKED 3 Nov (needs the batch and the build loop). THE LONG GAME. When a build
    pattern repeats — a Keep fix, a chip row — the butler writes the
    PROCEDURE, not the code: the steps and the checks that proved it.
    The second time, it runs the procedure deterministically; the model
    plans the first build and the procedure handles the second. This is
    how the founder's style of building becomes cheap. Deferred until
    the build loop exists; named now so it is not lost.


[ ] gov.plan_has_a_status_view — FOUND 3 Nov. The founder felt
    anxiety at "86 open items". The number is real but it is not the
    to-do list: of 103 items, 58 are LIVE (decided and parked), 10
    GATED, 4 BLOCKED — the genuinely active list is about 16 open and
    15 in progress, and several of those are already done and unticked.
    The anxiety comes from a display bug: the front door and the
    orientation count everything as "open", so an archive reads as a
    backlog. THE FIX: the headline reads "Active: N open, M in
    progress; Parked: X live, Y gated, Z blocked." LIVE and GATED are
    never in the headline count. A plan that is honest about what is
    parked is a plan the founder can look at without dread. THE CHECK:
    the orientation output and NEXT.md never show LIVE or GATED items
    in the active count.


[ ] gov.build_loop — FOUND 3 Nov. THE BUILDER. A build lives on
    disk: a spec, a list of steps, and a state file that says where it
    got to and what it needs. run_build does one step per turn through
    run_with_tools, runs the step's check from the manifest, ticks on
    pass with the check's output as evidence, retries once on fail,
    marks it stuck on a second fail, and parks with a question when the
    model replies NEEDS_FOUNDER. Three tools (build_start,
    build_status, build_run) let the butler start and see a build.
    THE STOP-AND-ASK is what makes unattended work safe, and it is
    tested without a model call. THE NEXT STEP: the invoice chips as the
    first build — its spec is in accord.invoices_organised_by_month and
    its steps need check_ids. Then the night job.

[ ] gov.plan_updates_have_no_anchor — FOUND 26 Oct. append_plan_entry
    appends to the end of PLAN.md; it cannot attach an update to the
    item it names. Asked to record progress on accord.butler_knows_today,
    the butler produced a true status block 7,000 lines from the entry —
    the plan read false at the item and true at the tail. The tool does
    what it says (append) and not what the plan needs (update). Same
    family as the write-dead fields: a structure that promises "here is
    this item's status" and a tool that delivers "here is a new line at
    the end". Fix is an anchored update capability, or a settled
    convention that each item's status lives in the item. Do not rely on
    append for status.


[ ] gov.jarvis_shape — FOUND 26 Oct. THE DESTINATION, named so the
    next sessions point at it and do not re-derive it. A digital butler
    that holds the pile, does the decided work, and keeps a record that
    is TRUE. The truth is the product; the overnight runs are the
    labour; the morning report is the handoff. The aim is that ideas
    compound instead of disappearing, and that the founder's head is
    free for the decisions only the founder can make.

    THE RAMP, IN ORDER. Each step is useful on its own.
    1. BACKLOG — a quiet home for the dump (a thought, a bug, a "this
       isn't working", a "I want it to do X"). Low-friction, never lost,
       not the plan. The plan is for decided work; the backlog is where
       undecided work waits. Smallest build, biggest relief, and every
       later step reads from it.
    2. READING HABITS — the butler in the app reaches for PLAN.md,
       memory, and the transcript at the start of a conversation, the
       way this session did, unprompted. Today's UI test showed it can
       once told; this is making it a habit.
    3. ONE WATCHED ITEM — one plan item run with its check, by the
       butler, with the founder reading the diff. The gate proven once.
    4. THE RUNNER — a checkpointed, one-item-at-a-time, check-gated
       executor. One item per bounded conversation; a checkpoint after
       each; a check as the gate; stop on failure, not continue.
    5. THE REPORT — a short email on completion or failure (what was
       done, what passed, what failed, what to look at) plus the full
       run-state record. The email is the view; the record is the truth.

    THE LOW-DAY RULE. On a bad day or a bad week the system does LESS
    and holds MORE, and never creates urgent work. It works the safe
    tier and queues the rest. The business moves; nothing that needs the
    founder happens without the founder. This is a design constraint,
    not a wish: the system must be useful on the worst day, not only the
    best.

    AUTONOMY TIERS, named so a future build cannot quietly skip them.
    SAFE-UNATTENDED: reads, scouts, checks, website/receptionist
    monitoring. SIGN-OFF: patches to live code, emails to clients.
    NEVER-AUTOMATED: money, pricing, client commitments. On a low day
    the butler works tier 1 and queues 2 and 3.

    LEGAL LINES, already held as habits — a line in the plan, not a
    build, so the receptionist cannot go live without them. (a) The AI
    receptionist declares it is AI and asks whether the caller wishes to
    continue. (b) The butler listening to a client conversation says so
    verbally, says why, and asks permission; if refused, notes by hand.
    (c) A record of what the agent did, why, and who was accountable —
    the plan/memory/capsule/run-state record IS that answer. (d) A kill
    switch, and least privilege: no long-lived credentials. (e) Before
    any client-facing AI goes live: disclosure, a test plan, a monitoring
    process, and a named human accountable (the founder).

    THE TRUST GATE. No batch runs without a check per item, and the
    first run is watched. A system that says "done" while it isn't is
    worse than no system, because it corrupts the last reliable thing —
    the founder's own judgement about what is real. The checks are the
    compliance, the record is the defence, and the trust is the joy.

    WHY, one line: six years of good ideas that did not compound. This
    is the thing that makes them compound — a record that does not
    forget when attention moves on.


[ ] accord.client_side_calendar_join — FOUND 26 Oct. The shape is
    already in read_accord: dates, times, contactId, isAllDay, source.
    The content is in encryptedData, client-side. The app holds the
    key: it can decrypt and match titles to the shape the butler
    returns, so the user sees "3 events with Cafe Corner" while the
    model sees only the skeleton. LLM conductor, browser executor. The
    UI build that uses it.


[ ] accord.onboarding_state_write_dead — FOUND 26 Oct. onboardingStep
    and onboardingComplete are read in three places (auth/signin/route.ts
    :52, user/route.ts:21, user/route.ts:104) and written in none. Every
    user's values are empty/false, the founder's included. A branch on a
    field that is always false is a lie in the control flow. Symptom:
    user girosprodromos@gmail.com signed up 22 Oct 18:51, updatedAt 18:52,
    and the app cannot say whether they explored or stalled, because the
    field that would show it has never been written. Fix is open: wire the
    writes, or retire the fields and the reads that trust them.


[ ] gov.activity_event_write_dead — FOUND 26 Oct. ActivityEvent has a
    model and a route (app/api/activity/log/route.ts) and zero rows ever.
    ActivityLog, meanwhile, records exactly one action: chat_interaction
    (41 rows), so it is a chat counter, not a general activity log. The
    app has no record of non-chat actions — calendar, contacts, onboarding
    — for any user. A check that "if an activity route exists, it writes"
    would catch this class.


[ ] gov.no_general_activity_record — FOUND 26 Oct. The three write-dead
    findings above share a shape: the app's own record of what a user did
    is absent. Not a defect in one route, a gap in the system: "are they
    using the app?" has no system that can answer it. This item exists so
    the question is not lost; it may resolve into the two above, or into
    a small purpose-built record. Do not build until the wire-vs-retire
    call on onboarding_state is made.


[ ] [LIVE] accord.vault_managed_split — BUILT 21 Oct. The data
    model and read path for the two products.

    User.managedById (self-relation): set means a managed instance,
    null means a vault. It records WHO manages the instance — the
    question the transparency statement must answer — rather than a
    boolean mode.

    ProductToggle: userId, product, enabled, enabledAt, enabledBy,
    notes. No price column; the price is per client and lives in the
    notes.

    lib/managed.ts: isManaged, hasProduct, productsFor.
    GET /api/account/mode returns the mode, the manager, and the
    products switched on.

    Verified: the founder is managed, the manager is named, and the
    Executive toggle is on; a user without managedById returns
    'vault' with no products.

    THE RIGHT TO LEAVE — BUILT 21 Oct: POST
    /api/account/revoke-managed sets managedById to null and deletes
    every ProductToggle row, in a transaction. The instance becomes
    a vault. Idempotent. Verified: revoke returns
    {ok:true,mode:'vault',revoked:true}, the user's toggles go to 0,
    and GET /api/account/mode returns mode 'vault'. This is the
    action that makes the transparency statement true.

    THE SETTINGS UI — BUILT 21 Oct. The Instance pill at the top of
    Settings. Vault: one line and a 'Grant Bosly Ltd access' button.
    Managed: names the manager as Bosly Ltd, lists the products, and
    offers 'Remove Bosly Ltd's access' with the full confirmation.

    THE LOCK — BUILT 21 Oct. 'This cannot be undone by Bosly' is a
    database rule. User.managedRevokedAt is set when the client
    revokes. While set, set-managed.sql reports UPDATE 0 and Bosly
    cannot re-attach. Verified: after a revoke, UPDATE 0 and toggles
    0; the revoke route is idempotent (already: true).

    THE GRANT — BUILT 21 Oct. The mirror of the revoke, in the same
    pill: vault shows 'Grant Bosly Ltd access'. POST
    /api/account/grant-managed attaches Bosly Ltd to the caller's own
    instance, clears the revoke, and switches the Executive back on,
    in one transaction. Verified by button: vault -> grant -> managed
    with the Executive listed; managed -> remove -> vault with the
    grant button back.

    NOT YET: an invite link so a *client* can attach Bosly without the
    client being the founder, the two privacy statements per mode, the
    toggle management for products beyond the Executive, and the
    pricing-per-client record.

    THE THIRD PRODUCT — accord.founder (DECIDED 23 Oct). The founder's
    instance. It is a managed instance with User.isFounder true, and
    it is the only instance whose Executive has the Custodian's build
    tools. Vault and manage are unchanged; founder is the founder's
    own, not for sale. The gate is isFounder.


[ ] [LIVE] accord.executive_unattended_loop — DECIDED 22 Oct. The
    last rung. The Executive running "work this week's list" without
    the founder in the chat. Not a new tool, not a new model: a
    trigger, a door, and a delivery.

    THE DOOR: a route or script that runs the same tool loop the
    chat runs, callable without a conversation. The same tools, the
    same guard, no chat window.

    THE TRIGGER: a new ranked CSV (the pickup already watches for
    it), or a cron tick. The work arrives; the loop runs.

    THE DELIVERY: send_draft_to_me emails the drafts to the
    founder's phone. He reads them, approves, sends.

    THE GUARD, UNCHANGED: the loop DRAFTS and DELIVERS TO THE
    FOUNDER ONLY. It never sends to a client. send_email still
    requires confirmed=true and an explicit yes. The toggle is
    still the guard; the loop does not bypass it.

    WHY IT IS THE LAST RUNG, NOT THE NEXT: it depends on every rung
    under it being trustworthy. An unattended loop on an unproven
    Executive is a machine that does the wrong thing while the
    founder is asleep. The checks, the toggle guard, the capsule —
    those are what make the loop safe to build, not a substitute
    for it.

    THE ORDER, AND WHY IT MATTERS:
      Now:      the Executive's loose ends, then the consultancy
                page.
      After:    the loop's door.
      Then:     the trigger.
      January:  the founder wakes Monday, the drafts are on the
                phone, he approves and sends.

    The unattended loop is AFTER the loose ends and the page. Not
    before. A loop that runs on an unproven Executive is the thing
    that makes January fail quietly.

    NOT YET: the door, the trigger, the delivery test.


[ ] [LIVE] ops.priority_to_january — DECIDED 21 Oct. SUPERSEDED by
    ops.plan_to_january_v2 (23 Oct). Kept for the record; where they
    differ, v2 wins.

    The split works for the founder; it does not need to work for a
    client until January. The work now is the things that earn.

    ORDER:
      1. The Executive working for the founder — the model call out
         of /api/chat, client-side via a proxy; the calendar and
         inbox read and decrypted in the browser.
      2. The AI receptionist — the first client product.
      3. The consultancy page — one page, through Claude, shipped.

    DEFERRED TO DECEMBER (not bugs, not forgotten):
      - the two privacy statements per mode
      - the client-attach flow (Bosly attaches a real client)
      - toggles beyond the Executive
      - the pricing-per-client record
      - the invite link for a client to attach Bosly


[ ] [LIVE] accord.executive_state_now — RECORDED 21 Oct. HISTORICAL:
    this is what the Executive was at the close of 21 Oct. The ladder
    since built (A-D, accord.learned_answer_cache) and the front door
    (gov.custodian_front_door, 23 Oct) supersede the 'next build'
    below. Kept for the record.

    What the Executive actually is, for the founder, at the close of
    21 Oct.

    TOOLS (14, all in routers/tools.py on the Gov side):
      append_plan_entry, save_memory, read_file, run_check
      save_thing, read_thing, find_things, link_things
      draft_email, send_draft_to_me, run_lead_scout, send_email
      read_leads, ecosystem_state

    ECOSYSTEM SECTIONS THAT WORK: plan, things, scout, capsules.
    The accord section says 'not yet — needs the session token'.

    WHAT IT CAN DO FOR THE FOUNDER: hold the business memory; read
    the plan, the scout, the capsules; find leads, draft outreach,
    send drafts to the phone, send guarded emails; run the county
    scout. The pickup notices a new sweep.

    WHAT IT CANNOT DO: see the founder's calendar or inbox; reason
    in Accord (/api/chat is a deterministic router, not an LLM);
    work while the founder is away; listen to a call.

    THE NEXT BUILD, and it is one piece: the client-side Executive
    in Accord. /api/executive/proxy for the model call; a browser
    reader for calendar and inbox that decrypts encryptedData with
    the session key; the chat gains a mode when the Executive is on.

    WHAT WAS FOUND: the calendar route returns encryptedData as
    JSON, undecrypted, alongside plaintext title and startTime. The
    browser can decrypt it; the server never does. encryptedData
    exists on twelve models. So the client-side Executive is
    buildable, and the calendar's plaintext titles are the one
    caveat worth stating.


[ ] [LIVE] gov.custodian_front_door — DECIDED 23 Oct. One Executive,
    two rooms, one front door.

    THE FRONT DOOR: the founder talks to the Custodian Executive.
    It is the server screen, the room the founder walks into. It
    holds the plan, the memory, the checks, and the build tools.
    It is where the work happens.

    BEHIND IT, THE OTHER ROOMS:
      ACCORD MANAGED — the business room. Invoices, emails, the
        calendar, the day-to-day. It runs the founder's business.
      BOSLY KEEP — the personal portfolio. Personal, not a product.
      THE SCOUT — the county sweep, the ranked shortlist.
      THE CONSULTANCY — the front door at bosley.app/consulting.

    THE CUSTODIAN TALKS TO ACCORD ON THE FOUNDER'S BEHALF. The
    founder asks once, in one conversation. "Have I forgotten an
    invoice?" — the Custodian asks Accord, gets the answer, tells
    the founder, and acts on a yes. One voice, two rooms, no
    tab-switching. That is what makes it a butler rather than two
    assistants.

    THE GUARD IS UNCHANGED. The Custodian's trust contract binds it:
    nothing changes without explicit consent; consent is
    per-action. The Accord Executive's vault/managed toggle and the
    proxy's guards are unchanged. The front door is a conversation,
    not a new permission.

    THE TOOLS DIFFER BY ROOM. Accord's tools: business work —
    leads, drafts, briefings. The Custodian's tools: build work —
    the plan, the repo, patches, checks, the ecosystem reader.
    Same assistant, same memory, same plan, same guards. Different
    tools because the work is different.

    WHY IT IS SERVER-SIDE. The build room is plaintext, on the
    machine the founder controls. The repo, the plan, the checks,
    the memory — all server-side by design. The Accord room is
    encrypted and client-side. Two security models, one assistant,
    one front door.

    THE NOTE: the founder's own Accord is a managed instance,
    managed by Bosly Ltd. The Custodian room is developer-only, for
    the founder. Nothing in this entry changes the client model or
    the vault/managed split; it records where the founder sits.

    THE PRODUCT IS THE TEMPLATE. What is built for the founder is
    the working version. The client version is the same butler,
    tuned to their business, with their toggles. Every rough edge
    sanded off is a rough edge the client version does not have.

    THE ROOM: the Custodian Executive lives in Accord.founder — the
    founder's managed instance, with isFounder true. Reached through
    the terminal today, and through the founder's Accord tomorrow. A
    client's manage never has it.

    THE NAMES: the butler is the assistant — the Executive and the
    Custodian, together. The Executive is the acting half (judgment,
    action, the conversation). The Custodian is the restraining half
    (the checks, the plan, the memory). The Copilot is the tool — the
    build hands, run inside the Custodian. Accord.founder is the app's
    door to the digital butler. The UI butler is the laptop's door to
    the digital butler.


[ ] [LIVE] gov.founder_door — BUILT 23 Oct. The founder's chat
    reaches the Custodian. The door is open and proven.

    WHAT IT IS: POST /api/executive/founder — gated by User.isFounder,
    then calling the Copilot's /api/chat (localhost:3102), which runs
    the tool loop (routers/tool_loop.py, run_with_tools). The founder
    talks to the Executive in Accord.founder; the Executive reaches the
    Copilot's tools; the founder never touches the Copilot directly.

    THE CHAT BRANCH: ChatDrawer reads /api/account/mode (isFounder).
    For the founder, the message goes to the door FIRST and returns;
    /api/chat, the proxy and the cache are the business door and are
    unchanged. Two doors, two routers: the founder's is the Copilot;
    the business's is /api/chat.

    THE BUG AND THE FIX: the first attempt put the founder branch
    inside the unknownIntent check, after /api/chat. The deterministic
    router answered 'what's on the plan?' with 'nothing scheduled for
    that period', and the door was never reached. The fix was the
    order: the founder's message goes to the door first. The order is
    the architecture.

    THE GATE: gov.founder_gate — the route calls isFounder, returns
    founder_only for a non-founder, and reaches the Copilot. A
    client's manage never has isFounder true, so a client never
    reaches the Copilot's tools through this door.

    PROVEN 23 Oct: 'What's on the plan?' in Accord.founder returned
    the plan's actual content — 15 in-progress items, the right ones,
    with the right statuses. The Copilot read the plan; the door
    returned it; the chat showed it. No /api/chat, no proxy, no cache.

    THE ACCORD READER — BUILT 23 Oct (02a1184). read_accord reads the
    founder's Accord through the app's routes: the calendar, the mode,
    and the sections to come (invoices, finance). The token is the
    butler's key, and it lives where the loop runs.
    WHAT IS NOT YET: the invoices and finance sections of read_accord,
    and the Keep reader (Keep's fix list as a tool).

    THE BUTLER'S TOOLS: the build tools (plan, repo, checks, patch,
    scout) and the business tools (read_accord: calendar, invoices,
    mode) are in ONE loop. The model picks by what you ask. The app
    and the UI butler are the same butler; the message decides the
    tool. read_accord reads the founder's Accord through the app's
    routes, with the butler's token — the founder's key, narrow.
    PROVEN 23 Oct: 'what is on my calendar this week?' ran read_accord
    through the butler and returned the calendar.


[ ] [LIVE] ops.butler_test_day — DECIDED 23 Oct. Tomorrow: test the
    app butler and the UI butler, and build a few small items.

    THE TEST: ask the butler the real questions, in both doors — the
    calendar, the plan, the invoices, a scout run. Note what it does
    and what it misses. The test is the proof, and the gaps are the
    next builds.

    THE SMALL BUILDS: the invoices and finance sections of read_accord;
    a tool description pass (so the model picks better); one small
    thing from the rough-edges list. Built WITH the butler, as the
    loop intends.

    NOT YET: the Keep reader, the UI butler's full screen, the feed.


[ ] [LIVE] gov.prompt_caching — FOUND 23 Oct. The stable prefix, the
    cost lever.

    WHAT IT IS: the butler's request sends the same stable context on
    every call — the system prompt, the tool definitions, the plan,
    the memory. Anthropic prompt caching reads that prefix at ~10% of
    normal input price; a cache write is ~1.25x, a cache read ~0.1x.
    The cache is the reduction; the prompt cache is the lever.

    THE CONSTRAINT: the cached prefix must be byte-for-byte identical
    between requests. Stable content first, dynamic content after.

    NOT YET: the cache_control directive in the butler's request; the
    measurement (tokens before and after).


[ ] [LIVE] gov.butler_rough_edges — FOUND 23 Oct. The list, named,
    not built.

    - read_accord: the invoices and finance sections.
    - The tool descriptions: clear enough that the model picks right.
    - The Keep reader: Keep's fix list as a tool.
    - The UI butler's full screen: the readers, the tool calls shown.
    - The client's manage tools: later, adapted.
    - gov.evolve_loop_feed: the feed that turns questions into builds.

    The test day names which of these the butler asks for first.

    TESTED 24 Oct (both doors). WORKED: the plan (read_file, accurate),
    the calendar (read_accord, empty but honest), the Keep list (the
    plan's items). FOUND:
      - read_accord("invoices") returns invalid JSON ("Expecting value:
        line 1 column 1"). The path is wrong (the route is likely not
        /api/invoices) or the route returns a 401/HTML; the tool does
        not parse the error, so the butler cannot say why.
      - finance: the same broken path; "how much did I make" fails the
        same way. Needs its own route.
      - the scout: lead_scout rejects --category/--area; the script's
        usage is [--config] [--retry]. A CLI mismatch.
      - THE BUTLER CANNOT WRITE CODE. The Copilot's tools are read_file,
        run_check, append_plan_entry, save_memory — no patch/write. So
        "add the invoices section" cannot be done by the butler. This is
        the biggest gap: the loop that builds the butler needs a write.
      - read_accord has no period: "next week" cannot be read; the butler
        asked which week, honestly, but the tool cannot answer.
    The butler's honesty is a feature: every failure was reported as a
    failure, never as a zero. The gaps are named, not guessed.

    CLOSED 24 Oct: the invoices path (the middleware redirected the
    butler's token — the token branch lets it through); the tool's
    honesty (status and content-type, never a parse error); finance
    (removed — encrypted client-side; the butler says ask in Accord,
    where the session has the key); the scout (the tool writes a
    one-area config, runs --config, filters the CSV; timeout 300s;
    countrycodes=gb so NE46 is Hexham, not Nebraska). The scout found
    Overpass down on the retry; the tool refused the bad CSV and set a
    retry marker.

    STILL OPEN: read_accord has no period — "next week" cannot be read.
    The calendar path needs ?from=...&to=...


    THE RELATION TO THE LOOP: accord.executive_unattended_loop is
    the Executive's door, unattended. The Custodian room is the
    founder's door, attended. Different doors, different guards.


[ ] [LIVE] ops.plan_to_january_v2 — DECIDED 23 Oct. The order to
    January, refined. This supersedes the ORDER in
    ops.priority_to_january; the old entry stays for the record.
    Where they differ, v2 wins.

    NOW (late October) — the Accord Executive's loose ends, then
      the tool loop in the proxy. One day for the loop: the loop
      exists; it is a port, not a build.

    NEXT (November) — the Custodian room. A usable chat, the full
      tool set, the room view. This is the build that removes the
      bottleneck: the founder talks to the Custodian, the Custodian
      builds and tests and reports. A week or more, because UI is
      where estimates slip.

    THEN (late November to early December) — the receptionist, the
      Keep fixes, the consultancy page. Built WITH the Custodian
      Executive rather than by hand. This is where the time saved
      starts to pay back.

    DECEMBER — not idle. The Custodian Executive does the heavy
      lifting: the scout runs, drafts are reviewed, the pitch is
      refined. The founder uses the machine rather than building
      it. A light rhythm, one or two sessions a week. Rest, not
      dormant.

    JANUARY — the wave. 15 contacts a week from the scout. The
      Custodian drafts, the founder approves. A paying client at
      the end of January is a good outcome, not a slow one. The
      reply comes mid-January; the contract after that.

    FEBRUARY ONWARD — the butler assembles, room by room. The
      client version is the same butler with different keys.

    THE PRODUCT IS THE TEMPLATE. The founder's own business is the
    proving ground. What is built for the founder is the working
    version; the client version is the same, tuned.


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
THE ECOSYSTEM
================================================================

Five pieces. One shape. Written 9 Oct, because the shape is now
visible and a future session — or January-me, deep in consultancy
work — will not see it from the entries alone.

BOSLY — the app. Free tier for individuals, Accord paid tier for
  the full workspace. The product for ADHD brains running small
  businesses. Being refined, not rebuilt.

BOSLY KEEP — a sovereign ethical investment platform. Wealth that
  grows without costing the earth. £19.6k personal ISA today (Phase
  1), a corporate fund for Bosly Ltd next (Phase 2), open to others
  with FCA authorisation after that (Phase 3). Its own constitution
  — the Bosly Keep Trust. Its own mission: end financial exclusion,
  make capital access a right. The pension market is the stated
  destination. It funds Bosly; it is also its own thing.

THE WAITING WELL PAGE — a public resource for the UK neurodiverse
  community. Four pills, sourced and dated, self-checking. Free, no
  login. The community bridge.

THE CONSULTANCY — the income. Workflow audits and small automation
  builds for UK small businesses. Seven phases, January runway. The
  engine that funds the wait.

BUSINESS SETUPS — gated. The consultancy's output, generalised. The
  first hairdresser is an engagement; the second is a product. Built
  when a real client pays for one.

HOW THEY CONNECT:

  Social → Waiting Well (free help) → Bosly (the tool for the ADHD
  tax). The community route.

  Consultancy → real client needs → Business setups (the product
  generalises). The commercial route.

  Consultancy → income → funds the app while it grows.

  Bosly → runs the consultancy → proves it works in a second domain
  → makes it sellable to other businesses.

  Keep → personal and company wealth → funds more projects, and
  builds toward the pension market on its own terms.

THE SHAPE OF IT: five pieces, each feeding another. The consultancy
is the engine — it funds the wait and proves the product. The app is
the destination. The Waiting Well page is the conscience. Keep is
the fuel, and a destination of its own.

================================================================
PHASE 1 — BUILD THE PIPELINE
================================================================

Goal: prove the pipeline works end to end with one invariant check.
Then add more.


[ ] [LIVE] ops.jarvis — THE VISION. One voice across everything.
    Not a feature: the destination. The thing Bosly has been building
    towards for months, and the reason the ecosystem coheres.

    WHAT IT IS. A voice interface that reaches Bosly Accord, Bosly
    Keep, Bosly Gov, and the consultancy as one. You talk to it, and
    it answers from all of them.

      "What's going on today?" — it dips between Keep, Accord, Gov,
      and the consultancy, and tells you.

      "Help me build this." — it writes code alongside you.

      "Build a website for this client." — it does the demo.

      "Set up an AI receptionist for this hairdresser." — it
      configures the setup.

    THE INTERFACE, NOT A FEATURE. Today the five systems are separate
    surfaces. Jarvis is the thing that makes them one — a single way
    in, with everything behind it. That is the whole point.

    WHERE IT RUNS. A local voice assistant on the home server. Wake
    word, speech-to-text, an LLM with tools, text-to-speech. Local
    hardware, because the point is not to rely on external services
    for the core. Open-source starting points: fusion-runtime
    (self-hosted, sub-second latency on consumer hardware), jarvise
    (voice pipeline with RAG memory and tool calling).

    SHARED PIPELINE WITH THE PRODUCT. Jarvis and the AI receptionist
    are the same pipeline with different wrappers. Jarvis serves the
    founder and connects to the founder's systems. The receptionist
    serves a client and connects to theirs. Build Jarvis to learn the
    pipeline; sell the receptionist to learn the client-facing layer;
    self-host when the demand is proven. See ops.voice_infrastructure
    for the product side.

    WHY IT MATTERS. It reduces the build bottleneck — an assistant
    that can help build, and that queries the systems by voice. But
    it is bigger than that. It is the shape of the whole project:
    five things that are one thing, and a way to talk to all of it.

    Raised 10 Oct, rewritten 12 Oct as the vision rather than a
    gated feature. This is the destination; the product entries hang
    off it.


[ ] [GATED] ops.voice_infrastructure — The voice products. Two tiers
    sharing one pipeline, and a chief of staff as the destination.

    TIER ONE — THE AI RECEPTIONIST. Answers the phone when the
    founder cannot. First sentence always declares itself: "Hello,
    I'm the AI assistant for [name]. They're unable to take your
    call at the moment, but I can help." It asks the discovery
    questions, gathers details, books a call.

      The human fallback: if the caller says they don't want to talk
      to an AI, it says "Of course — I'll note that you called and
      they'll call you back." Then it takes the message and ends the
      call cleanly. This is the product working, not failing. Most
      AI receptionists fail because they have no exit.

      v1 uses a platform — Vapi (developer-first, bring-your-own LLM,
      $0.05/min platform fee), Retell (managed, $0.07-0.18/min
      all-in), or ElevenLabs Agents (best voice cloning, if the
      client wants their own voice). v2 self-hosted, once demand is
      proven. The differentiator is the Bosly integration: the call
      outcome lands in the workspace as a card or contact. No generic
      platform has that.

    TIER TWO — THE CHIEF OF STAFF. The destination for the product.
    Bosly with a phone line attached. It answers when the founder
    cannot, and it also:

      - Records and transcribes the calls the founder does take,
        with consent asked first. If the client says no, the AI
        switches off and the founder takes notes by hand. Not a
        degraded product — the honest one.
      - Briefs the founder before a call: who is this, what do they
        want, what's the history.
      - Sits in on the call, takes notes, summarises.
      - Keeps track of clients and context, so nothing is forgotten.

    What a busy professional pays an assistant £30k a year for. For a
    solo consultant, it is the difference between running one
    business and running three.

    THE FIRST CLIENT IS THE FOUNDER. Build the receptionist for the
    consultancy line. Use it daily. Test it ruthlessly — call it from
    a different phone, try to break it. Only then put it on the front
    door. A clunky AI receptionist on a consultancy that sells AI
    receptionists is the worst possible demo.

    THEN SELL IT. Same shape as accord.business_setups. Tier one is
    the entry product (£200-250/month). Tier two is the chief of
    staff, which sells to businesses with staff and process, not to
    sole traders. Likely priced per-seat, not flat — a two-chair
    salon and an eight-practitioner clinic are different businesses
    with the same software. Not decided yet.

    THE DEMO IS THE PRODUCT. When a client asks what it does, the
    answer is "call this number." Live, not a mock. One
    implementation per vertical — the hairdresser version is the
    same pipeline with different questions and a different voice.

    GATED on the first consultancy engagement that needs a voice
    receptionist, OR the home server upgrade. Do not build ahead of
    demand. Raised 10 Oct, expanded 12 Oct with the two-tier shape,
    the fallback, the consent rule, and the chief-of-staff
    destination.


[ ] [GATED] accord.business_setups — Bosly stays as it is: free
    tier, Accord paid tier, no architectural change. On top of that,
    consultancy engagements produce reusable setups — a bundle of
    modules and configuration that fits one kind of business, ready
    to switch on for the next client of that kind. The first
    hairdresser is an engagement. The second is a product.

    The pattern: a client needs something (an AI receptionist, a
    small-business accounting module, whatever their particular
    chaos is). It is built as a Bosly setup, generalised, and priced
    per month on top of Accord (e.g. receptionist GBP 200-250/month,
    accounting GBP 250-300/month). The first client funds the build;
    every subsequent client of that type is margin.

    Build the setup, not the bespoke. A one-off build pays once. A
    generalised setup, configured for the client, pays forever. This
    is the discipline that makes the consultancy scale.

    EVERY SETUP CARRIES A VALUE REPORT. Not an add-on — part of the
    product. The setup tracks what it delivered and reports it
    monthly, from the real numbers, never estimated:

      Hairdresser   calls answered, bookings made, revenue booked,
                    no-shows prevented
      Plumber       quotes sent, jobs won, time-to-quote, revenue
      Dentist       appointments booked, no-shows prevented,
                    reminders sent
      Any           hours saved, £ recovered

    It does three jobs. Retention — £350 in, £2,400 out, and the
    numbers argue for the renewal. Case studies — "this hairdresser
    recovered £X in three months" is the pitch for the next
    hairdresser, and it is true. And product development — if 40 of
    47 calls book for one client and 12 of 47 for another, the
    variation tells you what works.

    The report is honest by construction: every number comes from the
    system, not from a summary. A report that only ever says "great
    month" is a report the client stops reading.

    GATED on the first consultancy engagement that needs one. Do not
    build setups ahead of demand. When a real client of a given type
    pays, that is the signal to build their setup — and from then
    on, that vertical is switchable.

    Related: accord.spaces_encryption (shared workspaces for
    businesses and their employees). A business setup and a space
    are different things — a setup configures Bosly for a kind of
    business; a space lets a business's people share and work
    together. A client may want both. They are gated on the same
    demand.

    Raised 9 Oct.


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


[~] ops.social_strategy — DECIDED 17 Oct. No more Meta posting.
    Instagram and Facebook apps deleted from the phone 17 Oct
    after seven hours of doom-scrolling in a single day. The
    decision, recorded here so it does not get relitigated:

    - No posting on Instagram or Facebook. Accounts stay (business
      pages); if needed, post from a browser, never from an app.
    - LinkedIn, once a week, Thursday. One post, written because
      there is something to say. If there is nothing to say, skip
      the week. The cadence serves the founder, not the algorithm.
    - Morning routine: coffee, 5-10 minutes on LinkedIn, like a
      couple of things, comment on 2-3 where there is something
      genuinely useful to add. Participation, not consumption.
      Bounded — it has a start and an end.
    - No ADHD-creator role. The ADHD resource exists and is good;
      it goes in LinkedIn's Featured section as a thing built, not
      as a content series. The algorithm was drifting the founder
      into a niche he did not choose. Stepped off.
    - Primary LinkedIn URL: the consultancy page. Featured cards:
      the ADHD resource, the waiting well page, Bosly Accord,
      Bosly Keep.
    - Reassess 1 February 2027, not before. The question then:
      did this produce consultancy enquiries or Accord signups?
      Not "did it go viral." Real output.

    A prompt for the other chat (the social-media chat) was written
    17 Oct and pasted there. It holds the line.


[ ] [LIVE] ops.findability — Done once, then left alone.
    The handful of places a real person looks, so the consultancy
    can be found without posting daily. This is not a channel
    strategy; it is a one-off structural job.

    - LinkedIn Website field: bosley.app/consulting. One URL. This
      is the primary link; when someone clicks the founder's name
      from a comment, they land on the consultancy page.
    - LinkedIn Featured section: the ADHD resource, the waiting
      well page, Bosly Accord, Bosly Keep. Framed as "things I've
      built," not as a pitch. Descriptions one line each.
    - Google Business Profile for Bosly Limited, consultancy
      trading. Category: business consultant / automation. Service
      area, not a shopfront.
    - Backlinks: from being useful in public (LinkedIn comments,
      carefully-chosen forums), not from directory submissions.
      One good answer to a real question is worth more than fifty
      directory entries.
    - No submission sprees. No guest-post treadmill. The work
      accrues from use.

    [ ] Phase 1 — LinkedIn URL and Featured cards
    [ ] Phase 2 — Google Business Profile
    [ ] Phase 3 — one or two real directories, chosen, not swept
    [ ] Phase 4 — leave it alone for three months


[ ] [LIVE] ops.consultancy — Bosly Limited's consultancy arm.
    Workflow audits and small AI/automation builds for UK small
    businesses drowning in admin. Front door at bosley.app/consulting.

    REVISED 18 Oct — this is the MAIN BUSINESS, not a bridge. The
    earlier framing ("replaces gardening income while the app
    grows") is out of date. The shape now: consultancy is the
    business; Bosly Accord is the product it sells (£25/month base
    plus feature toggles, priced per client against the human
    equivalent); Bosly Keep is personal and off the critical path.
    See THE SHAPE OF BOSLY at the top of this file. Everything
    before January serves this entry.

    The runway: winter is naturally slower, and January is when
    small business owners have had a break and rethink their admin.
    Everything before January is setup. Do not expect a client
    before then. The build plan assumes a January push.

    [x] Phase 1 — The front door.
    BUILT 10 Oct. A one-page site at bosley.app/consulting: the
    headline, an about paragraph with a photo, three capability
    cards (workflow audits, automation builds, ongoing care), an
    enquiry form, and a footer with contact@bosly.app. Live, public,
    taking enquiries. The form appends to
    consultancy-enquiries.jsonl, which the orientation reads as
    "N new consultancy enquiry(ies)".
    Design pass deferred — see ops.consultancy_design.

    [ ] Phase 2 — The legal floor (before any paid work). Professional
    Indemnity Insurance, GBP 1m minimum. A consultancy agreement
    template (scope, payment terms, deposit, IP). Invoicing
    discipline: invoice the moment a milestone is hit, Pay Now link,
    no Net 30. These gate everything — no paid work without them.

    [~] Phase 3 — The lead-gen tool. BUILT 20 Oct (see
    ops.scout_cron for the pipeline details). OSM discovery,
    Companies House enrichment, and ranking are done. Google is
    built and inert until the key exists. Employee count and ICO
    are not done; they are optional size signals.

    The filter. Reduces hundreds of thousands of businesses to a
    shortlist worth researching by hand. Not a research engine, not
    a CRM — it finds strong candidates and hands them over.
    Everything past that (LinkedIn, Facebook, a manual read of the
    site) is done by hand on a handful of businesses.

    Source order — free first, Google last:
      1. OpenStreetMap — discovery, and the no-website signal.
      2. Companies House — active status, incorporation date,
         directors, SIC code.
      3. Companies House daily accounts files — employee count.
      4. ICO register — optional size confirmation.
      5. Google Places — review count and rating, shortlist only.

    Output: a CSV, one row per business — name, location,
    incorporated date, employees, directors, VAT, website (if any),
    phone, and the specific Day Zero findings. The findings are what
    write the email.

    Two rules that make it sellable later: config not code
    (verticals, weights, location, threshold in one file); shortlist
    not rank (top N, not a leaderboard).

    Build steps: API setup, OSM discovery, Companies House
    enrichment, employee lookup, website check, scoring, CSV.

    Not a SaaS. Not a web app. Not a front end. A script that runs
    and outputs a list.

    THE EXECUTIVE IS THE JUDGMENT AROUND THIS SCRIPT. The script
    stays a script — it runs, it outputs a CSV, it's done. The
    Executive calls it: "find me companies" → run_lead_scout →
    CSV rows → the Executive picks five, researches each, drafts
    the email adapted to each, asks before sending. The "manual
    read of the site" in this entry becomes the Executive's job.
    Each shortlisted lead becomes a thing in the business memory
    (ID, status, outcome) — which is the "each lead gets an ID;
    note the outcome" line below, made real. The loop between
    the script and the memory is what makes the weights evidence
    rather than guesses.

    Legal: official APIs and open data only. No scraping the
    directories. Google used on the shortlist only — Places data is
    not stored permanently.

    The loop: each lead gets an ID; note the outcome; after enough
    rows the weights get evidence instead of guesses.

    Later: the product version (adapted per consultancy), the trades
    directories (Checkatrade, Yell) as a second source, a UI.
    Design-age heuristic dropped from v1 — too noisy, the other
    markers are reliable enough.

    [ ] Phase 4 — The first audit. The Day Zero method: pick one
    business, audit its public footprint, write up three ranked
    bottlenecks, send with no ask. One a week. Not ten. The email
    goes at 6-7am or 8-9pm — trades read before the day starts and
    after dinner. Where a business has an office manager or
    bookkeeper, that is the route in: they feel the pain and forward
    it upward.

    [ ] Phase 5 — The first paid work. Three stages. Audit: GBP
    500-1,500, 1-2 weeks. Build: GBP 2,000-5,000 for a single
    workflow. Retainer: GBP 300/month. Revenue model: 3 clients =
    GBP 3,000 audit + GBP 9,000 build + GBP 900/month recurring.

    [ ] Phase 6 — The background hum. LinkedIn, one post a week, for
    credibility when a business Googles me. Instagram continues as
    planned. The Waiting Well page is the community bridge, not the
    business one — the consultancy audience and the ADHD community
    overlap but are not the same.

    [ ] The one rule: send 15 audits before drawing any conclusion.
    First five are usually silence. First reply around six to ten.
    First paid audit around eleven to fifteen. Track the count, not
    the reply rate — the count is the thing that is controlled.

    WHERE THE APP FITS. Nowhere, yet. Deliver audits however is
    fastest — email, a document, by hand. No Bosly in the
    deliverable, no signup, no friction. The app is shown only when
    there is a live conversation and it is natural. From spring,
    once a few audits have been done by hand and the pain points are
    known, build the consultancy workflows into Bosly the way the
    gardening ones were built. The consultancy is a second business
    run by the same ADHD brain; running it by hand is how the app
    learns what a consultancy needs. When it works for two
    businesses, it is general enough to sell. See
    accord.business_setups.

    SUCCESS, SHORT TERM. Not a client by next week. By end of
    January: fifteen audits sent and three businesses spoken to.
    That is the controllable target. The rest follows or it does
    not.

    Raised 9 Oct.



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


[ ] [LIVE] ops.send_email_test_address — FOUND 19 Oct. The full
    lead workflow works: find, draft, deliver, confirm, send. The
    end-to-end test sent to hello@cafecorner.example, which is a
    reserved .example domain with no mail server — the send failed
    with a 550, and the Executive reported it honestly ("nothing
    was sent").

    The .example domain is the right test address: it can never
    reach a real person. When testing the send path, use an
    @example.com or @cafecorner.example address, never a real
    client's. That is how the guard was proven without emailing a
    stranger.

    Also: send_email now logs failures as well as sends
    (status: sent / failed), so there is a trail of what was tried,
    not only what went out.

    Unblocked once Overpass is back: run_lead_scout finds real
    candidates; save_thing records them; draft_email drafts;
    send_draft_to_me delivers; send_email sends to a real address
    with confirmed=True. Every piece is built and tested except the
    live scout run.


[ ] [LIVE] gov.config_patch_preserve_keys — FOUND 20 Oct. Three
    times today a config file lost data to a patch that rewrote it
    from a partial state:
      1. lead-scout.config.json: the fit.weights object was replaced
         with only the three new keys, dropping has_phone,
         bookable_trade, has_address and the CH weights. Every row
         scored 0; the ranking looked broken.
      2. Earlier: the same class on a smaller scale — a config edit
         that set one key and dropped others.

    The fix, in code: the ranker now refuses to run if fit.weights
    is missing core keys. A loud refusal is better than a silent
    zero.

    The rule, for the future: a patch that edits a JSON or YAML
    config must PRESERVE the keys it does not own. Load, modify,
    write — never reconstruct from a partial dict. And where a
    partial config would silently misbehave, add a guard that
    refuses.


[ ] [LIVE] gov.prompt_identity_wins — FOUND 19 Oct. The model
    refused to save a business lead through the Executive, saying
    "this is a code copilot, not a CRM." It was right — the system
    prompt was the project context_header ("Bosly Developer
    Copilot for bosly-gov"), not the tools prompt. The tools
    existed; the identity told the model not to use them. Fixed:
    the tool branch now sends tools_prompt + context_header, so
    the model sees both. Same class as
    gov.project_chat_context_ignored: the right context exists,
    but a wrong one is winning. General lesson: when a model
    refuses a valid action, check what identity it was given
    before checking the tools.


[ ] [LIVE] gov.project_chat_context_ignored — FOUND 19 Oct. The
    project chat handler (_handle_project_chat_post) builds a
    context_header containing the Accord, the current report,
    memory, and recent chat — then never passes it to the LLM.
    run_chat_once only receives {message, project}. So the project
    chat has been answering without its context. The tool branch
    (added 19 Oct) now passes context_header as the system prompt
    when tools are on. The plain path (tools off) still does not.
    Fix: pass context_header to run_chat_once too, or remove the
    dead build if it was deliberately abandoned.


[ ] [LIVE] ops.capsule — THE CAPSULE HABIT. DEFINED 19 Oct.

    A capsule is a session record: not a summary, not a memory
    entry, but the reasoning trail. It answers "how did this
    session go, and why" for a future session — and, long-term,
    it is part of the training set.

    LOCATION: /mnt/bosly/bosly-data/copilot-knowledge/<slug>/capsules/YYYY-MM-DD-name.md

    FORMAT:
      - Date and session name
      - Commits made
      - What happened (the arc, a few paragraphs)
      - The decisions, and why (the valuable part)
      - What was built
      - What was found (bugs, gaps, findings)
      - What's open (what a future session picks up)
      - The lesson, if there is one

    RULE: write for yourself, not for the model. The training
    value is a side effect of writing well, not a reason to write
    differently. A capsule that is good to read is good training
    data; one written as training data is neither.

    THE HABIT: one capsule per session that produced something.
    Not every conversation — every session that shipped, found,
    or decided. The plan holds the result; the capsule holds the
    thinking.

    First capsule: 2026-10-19-custodian-tools.md.

    Not yet: a schema check. The memory has one (memory_schema);
    capsules don't. Worth adding when the habit is established.


[ ] [LIVE] gov.custodian_executive_map — THE FURNITURE.
    WRITTEN 19 Oct, after the conversation drifted once too often.

    THE ORIGIN, PLAINLY. Bosly Gov was meant to be the chief of
    staff. As it was built, the checks turned out to be the
    foundation, and Gov became the custodian. The Executive is the
    original vision, built on the custodian's foundation. That is
    not a failure — it is the right path, arrived at by building.
    Gov is now two roles in one codebase, and that is fine:

      - THE CUSTODIAN verifies. The plan, the memory, the checks,
        the invariants, the provenance. It does not act.
      - THE EXECUTIVE acts. The conversation, the tools, the
        builds, the notes, the emails, the searches, the reports.
        It does not verify its own work.

    They are ONE SYSTEM WITH TWO ROLES, not two systems. The same
    process, the same LLM connection, the same tools, the same
    memory. The Executive acts; the Custodian checks what it did.
    That is why they can live in one codebase — because they are
    one thing, seen from two sides.

    THE INVENTORY — what exists, and where it belongs. This is the
    real state as of 19 Oct, not what we remember building.

    THE EXECUTIVE'S ALREADY-BUILT PARTS (living under Gov's name,
    built for the wrong role, readied for the right one):
      agent_router.py — the agent loop, session management,
        deploy stages. Propose, act, pause, resume.
      agent_state_store.py — sessions.
      patch_engine.py — structured patches. Building code.
      fix_router.py — "fix this file." Building code.
      file_access_router.py — read and search files.
      command_router.py — commands the founder types.
      intent_classifier.py — what is the founder asking for.
      deploy_after_fix.py — deploy after a change.
      validation_pipeline.py — check the output before it lands.
      tool_loop.py, tools.py — the tools, built 19 Oct.

    THE CUSTODIAN'S PARTS (verification, honesty, the record):
      All 17 checks in manifests/checks.yml.
      answer_verifier.py — multi-pass verification. The core.
      provenance.py — where did this come from.
      consent_flow.py, consent_store.py — the consent contract.
      error_types.py — typed errors.
      observability.py, metrics_router.py — what happened.
      session_digest_router.py — the failure digest.
      memory_first.py, memory_store.py — the memory store (the
        schema check that guards it is Custodian's).

    THE SHARED SUBSTRATE (both use, neither owns):
      direct_llm.py, llm_router.py — the LLM connection.
      context_engine.py, context_orchestrator.py, context_graph.py,
        project_graph.py — building the context the LLM sees.
      prompt_compactor.py, token_budget.py, snippet_cache.py —
        keeping the prompt small.
      The PLAN file. The memory files. The capsules.

    WHAT THIS REVEALS. The Executive is already most-built. The
    agent loop, the patch engine, the fix router, the file access,
    the intent classifier — these are Executive capabilities that
    exist and work. They were built for Gov because Gov was the
    chief of staff. What the Executive is missing is:
      (a) the business memory — clients, projects, leads, ideas,
          notes. The "everything" store.
      (b) the proactive loop — "leave that with me" and the
          report-back.
    Everything else is a matter of moving modules to the right
    side of the line, not building them.

    THE TWO PURPOSES, BOTH REAL. It serves the founder first:
    "what's on my schedule, what's going on, what clients, how do
    we email, build me this code." And it becomes a saleable item:
    the same architecture, tuned per client, multi-tenant,
    isolated data, shared inference (see ops.architecture). The
    founder's Executive is the template for the product. That is
    not a later concern — it shapes the build.

    THE NOTE THAT STOPS THE DRIFT. When the conversation drifts —
    and it will — this entry is the reference. The Executive acts.
    The Custodian checks. The tools grow; the shape does not
    change. It serves the founder, then it sells.


[ ] ops.one_butler_capabilities_as_products — FOUND 2 Nov. THE
    PRINCIPLE. Bosly is one butler engine, not five products. A product
    is a SET OF CAPABILITIES plus a must-never-do spec: the salon gets
    answering and booking, the consultant gets leads and drafts, the
    founder gets everything plus the build tools. A capability is built
    ONCE and configured per product; the packaging is the market. This
    is the sentence that makes the salon, the consultant and the founder
    the same machine, and it belongs with the architecture principles.
    Consequence: never build a client's feature as a separate thing from
    the founder's — build the capability, prove it on the founder, then
    configure it.


[~] gov.custodian_tools — THE CHIEF OF STAFF. BUILT 19 Oct.

    DONE 19 Oct: routers/tools.py (four Custodian tools + guards,
    13-case self-test; ten tools now, see the Executive's build
    order), routers/tool_loop.py (the loop, 8-case self-test
    monkey-patching the API), tools_prompt.txt (the system prompt),
    config.json tools_enabled switch. Wired into all three chat
    paths: /api/chat, /api/chat/stream, and
    /api/project/{slug}/chat (the endpoint the UI uses). Verified
    end to end through the UI: read_file and append_plan_entry
    both work, and the append guard now requires a well-formed
    entry ([x] name — description), not a bare marker.

    Still open: save_memory and run_check untested through the
    UI; and the tool behaviour in the plain path (tools off) is
    unchanged, which is correct but worth confirming.

    THE REFRAMING. Until today the Custodian's LLM was explicitly
    told it had NO tools ("You have NO runtime tools in this
    mode", llm_router.py:59), and any output resembling a tool
    call was scrubbed. That was a safety valve, built because the
    founder was scared the model would go rogue and trash the
    code. The fear was reasonable. The valve is now the wrong
    answer, because it means the Custodian can only talk, not act,
    and the founder is still the courier between the conversation
    and the plan, memory, and code.

    WHAT IT BECOMES. A chief of staff that can act — but only
    through declared tools, each with a check on what it writes.
    The model cannot invent a tool. It cannot run arbitrary code.
    It cannot write outside the declared shapes. Every action it
    takes is one of four, and every one is guarded.

    THE FOUR TOOLS (v1):
      1. append_plan_entry — append a new entry to PLAN.md.
         Guard: the file must start with "BOSLY GOV — PLAN" (so we
         are not writing to the wrong file), and the entry must
         parse as a valid plan block (a [ ]/[~]/[x] marker line).
         The tool refuses if either check fails.
      2. save_memory — write a memory entry. Goes through
         store_memory_item (routers/memory_first.py), so the
         schema check applies. project_slug must be one of the
         three known repos. No raw writes to memory.json.
      3. read_file — read a file under one of the three repos.
         Bounded: the path must resolve inside the repo root.
         No traversal, no reads outside the repos, no .env.
      4. run_check — run a registered check by id (from
         manifests/checks.yml). No arbitrary commands. The model
         names a check, not a shell command.

    THE PRINCIPLE, SAME AS THE EXECUTIVE: the Custodian proposes
    and acts; the checks verify what it did. The model cannot
    verify its own work. Every write runs the relevant check
    before it lands, and if the check fails, the tool returns an
    error to the model, which sees it and tries again or stops.

    WHAT IS NOT A TOOL, AND NEVER WILL BE:
      - arbitrary shell execution
      - writing outside the four declared shapes
      - editing files (only appending — no replace, no delete)
      - reading .env, secrets, or anything outside the repos
      - deleting anything

    THE BUILD:
      [x] routers/tools.py — the four functions, their JSON
          schemas, and their guards. No LLM involvement yet;
          testable on their own.
      [x] routers/tool_loop.py — the agent loop: call the API
          with tools=[...], handle stop_reason == "tool_use",
          run the tool, feed the result back, repeat until
          "end_turn". This is the piece that replaces the
          "no tools" instruction.
      [x] server.py — wire the loop into handle_api_chat_stream
          (and handle_api_chat), replacing the plain route_llm
          call when tools are enabled.
      [x] Remove the "NO runtime tools" instruction from the
          system prompt, but only after the loop is proven.
      [x] Test each tool in isolation first, then together, then
          the loop, then the UI.

    TIMELINE: real build, not a patch. The tool module is the
    safe part — write it and test it before the loop exists. The
    loop is the part that needs the guards to be proven first.


[~] gov.evolve_loop_feedback — IN PROGRESS, digest built. The
    unknown-intents digest is live: lib/intent_classify.py labels each
    question bug / feature / question / other, evolve_feedback.py
    groups by label and gains --summary, and the orientation calls
    --summary. On today's five questions it shows 3 bugs, 1 feature,
    1 question, and names the recurring-appointments feature as the
    open signal — which is what this entry predicted it would do.

    The tracking store is built (e0383e1): a small JSON file beside the
    log records each question's status, and the digest marks each
    question open or fixed and lists only open questions in Open
    signals. Seeded with the five current questions — three fixed,
    two open.

    Remaining, in the order the entry below describes them:
      - Recurrence. The digest groups by label; it does not yet spot
        when two questions are about the same thing. Needs real data
        (today's five are all distinct) before it can be tested.
      - Close the loop — tell the user when their feedback led to a
        change. Not designed. The entry says the feedback loop is a
        two-way street; today it is one-way.

    UPDATE 5 Oct: five unknown-intent questions were logged on 2-5 Oct.
    Three were real bugs since fixed (the calendar timezone, the
    invoice PDF, the send failure); one is the recurring-appointments
    feature; one is a greeting the chatbot cannot answer.

    Original entry follows.
    feedback-driven evolution.
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


[ ] [LIVE] gov.pattern_signal — FOUND 22 Oct. Bosly reads patterns
    from the app itself — what is asked, what is needed, what the
    app contains — to find what to build next. This is the QUESTION
    side of the learning loop; accord.learned_answer_cache is the
    ANSWER side. Together they are the seed of Bosly's own model.

    WHAT IT READS (non-sensitive signal only):
      - the unknown-intents log (what the engine cannot answer) —
        already the seed of gov.evolve_loop_feedback's digest
      - the shape of questions the Executive answers (which kinds of
        help are asked for)
      - the app's own usage (which pills, which features, which
        workflows fire) — UsageEvent rows already exist

    WHAT IT PRODUCES: a periodic signal of what Bosly should become
      — the features implied by what is asked and what is used —
      for the founder to read and decide. Not automatic building;
      a signal, like the digest, for a human to act on.

    WHAT IT MUST NOT READ: client content. No calendar titles, no
      invoice amounts, no contact names, no messages. The signal is
      shape and frequency, not content. Same rule as the proxy: the
      route that reads patterns has no path to sensitive content.

    THE RELATION: gov.evolve_loop_feedback is the first instance
      (the digest groups unknown intents by label and names the
      recurring feature). This item generalises it: from questions
      to questions + usage + shapes. Keep them linked; this is the
      umbrella, the digest is the first reader.

    THE DIRECTION: Bosly develops itself from what it is asked and
      what it uses, so the next build is chosen from evidence, not
      guesswork. That is ops.jarvis's "one voice" seen from the
      build side: the app tells you what it wants to become.


[ ] [LIVE] gov.evolve_loop_feed — FOUND 23 Oct. The questions and
    actions the user gives, fed to the evolve loop so the founder can
    see where Bosly needs improving.

    WHAT IT IS: every question the user asks, and every action they
    take (open the calendar, draft an invoice, look up a contact), is
    a SIGNAL. This feed carries the signal to the evolve loop: the
    question SHAPE, the action LABEL, and the OUTCOME (answered,
    refused, or failed). The founder reads the feed and sees the
    patterns — what is asked, what is refused, what is done — and
    chooses what to build next from evidence.

    WHAT IT IS NOT: not a second logger. unknown-intents.jsonl already
    records what the engine cannot answer; the feedback log records
    what users flag. This feed adds the SUCCESSFUL questions and the
    ACTIONS — the things that worked, which tell you what Bosly should
    do more of, not just what it missed.

    THE BOUNDARY: the feed carries the question SHAPE (the same [name]/
    [date] slots), the action LABEL, and the OUTCOME. Not the content —
    no client name, no amount, no message. The same rule as the cache:
    the shape crosses, the data does not.

    WHAT IT FEEDS: gov.evolve_loop_feedback's digest, gov.pattern_signal's
    question side, and the founder's build decisions. The digest sees the
    misses; this feed sees the successes; together they are the whole
    picture of what Bosly is asked and what it should become.

    NOT YET: the feed route, the action labels, the digest integration.


[~] ops.deploy_smoke_test_covers_routes — FOUND 22 Oct. The deploy
    smoke test is http://localhost:3100/api/health/smoke only. It does
    not curl the routes that changed, so a green deploy is green for
    health, not for the feature. Verification of a new route is a
    manual curl to 3100 — 303 anonymous is the live signal; 404 is the
    deploy trap. A smoke test that covers the changed routes is a
    separate, small item: either the script takes a list of routes to
    curl after deploy, or a per-route check is registered in the fast
    tier. Not urgent; named.


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


[ ] [GATED] accord.chat_llm_fallback — Reconnect the LLM to the
    chatbot as a fallback, under a principle: the LLM is scaffolding,
    the workflows are the destination. Do not build this until the
    unknown-intents log shows questions worth answering that the
    workflows cannot. The chatbot works for what is needed now;
    using it more is what fills the log.

    THE PRINCIPLE. Every capability the LLM provides is a placeholder
    for a deterministic workflow that does not exist yet. The goal is
    not to rely on external LLMs — it is to use them to build the
    thing that replaces them. The mechanism is the unknown-intents
    log:

      - A question the workflows cannot answer -> the LLM answers it
        -> the question is still logged.
      - Over time the log shows which questions recur.
      - A recurring question becomes a workflow — deterministic, no
        LLM, faster, free.
      - Once the workflow exists, the LLM never sees that question
        again.

    The loop: LLM answers now -> log the question -> build the
    workflow -> the LLM is needed less. Without the log, the LLM
    becomes permanent and nothing notices which parts are ready to
    fold in. Same shape as gov.evolve_loop_feedback, at the chatbot
    layer instead of the product layer.

    THE BUILD (when the log justifies it):
      - Workflows first. The deterministic engine runs; on a match,
        no LLM call, no cost, instant.
      - LLM fallback. No match -> the LLM answers; the user gets a
        real reply.
      - Always log. Whether the LLM answered or not, the question
        goes to unknown-intents.jsonl. That is the signal.
      - Reuse Gov's Claude client pattern (routers/direct_llm.py —
        _call_claude / _stream_claude, CLAUDE_API_KEY and
        CLAUDE_MODEL from env). Keep the two code paths separate —
        separate prompts, separate logs — even though they share the
        key.
      - The digest tells you what to fold in: a recurring question
        becomes a plan item to build as a workflow.

    NOTES FROM THE INVESTIGATION (10 Oct):
      - Gov's Claude client is clean and streaming-ready. Reusing the
        pattern is small.
      - The archived AI-era chat (legacy/api-ai-20261003/) does not
        contain the cache-then-LLM system that was remembered. What
        was there: an LLM chat with several routes, a 26-line stub
        "brain" expecting an embedding store, and a 60-second
        in-memory cache of memory items (not of answers). The
        learned-answers system was intended — ChatMemory and
        MemoryFact tables exist — but the implementation never
        landed.
      - ChatMemory holds 2 rows. The memory system has barely been
        used. The current deterministic engine plus the unknown-
        intents log is the first real version of it, and it is doing
        the same job more honestly: it answers what it can, logs
        what it cannot, and the log drives what gets built next.

    GATED ON: the unknown-intents log showing a recurring question
    the workflows cannot answer. Use the chatbot more; the log fills;
    the signal appears. Raised 10 Oct.


[ ] [GATED] accord.chat_llm_legal — Before the LLM fallback ships,
    the legal and user-facing documents must say what it does. This
    is required-before-ship, not after. The failure mode is updating
    three of the five and leaving one claim false.

    THE CHECKLIST:
      - Terms of Service. The LLM is used to answer questions the
        workflows cannot. Responses may be inaccurate. Add the
        clause.
      - Privacy Policy. User messages leave the device and go to
        Anthropic. Today they go to the server and are processed
        deterministically; with an LLM, the question text is sent to
        a third party. Say so, plainly.
      - The Accord (the constitution). A clause on what the app
        promises about AI and what it does not: "The LLM answers
        questions; it does not read your encrypted content." The
        zero-access promise must hold — the LLM sees the question,
        not the vault.
      - Stripe / billing. If the LLM is Accord-tier only, the tier
        copy must say so. If it is metered or costs more, the
        billing terms change. Decide which before shipping.
      - In-app copy. The app currently says "No cloud AI" in places
        (e.g. the Billing settings copy). Connecting the LLM makes
        that false. gov.claim_invariants should catch it, but fix it
        deliberately, not by accident.

    GATED ON: accord.chat_llm_fallback being built. Same trigger —
    the log showing it is time. Raised 10 Oct.


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


[~] accord.waiting_well_page — A public resource for the UK
    neurodiverse community, at /waiting-well. Not a lead magnet: a
    filter. It gets people to the right information and the right
    next step, in a system that is overwhelming by design. The second
    unauthenticated public surface, after the standalone /invoice
    tool. Static: holds no user data, so the encryption question does
    not arise.

    COMPLETE 10 Oct, watching before [x]. All four pills are written,
    sourced, and live. 22 claims carry @claim markers and visible
    citations; every URL now points at the exact page that carries its
    claim, and gov.waiting_well verifies all 22 resolve. The check
    runs nightly at 6am, the orientation shows claim staleness and new
    questions, and the Ask a question form works end to end. Remaining
    before [x]: let it run a week, answer a few more real questions,
    and watch for a claim going stale on its own.

      Is this me?         ADHD traits, autism traits, the overlap,
                          and the screening tools (ASRS, AQ-10,
                          RAADS-R) as links.
      Getting an          Three routes — local NHS, Right to Choose,
      assessment          private. RTC explained properly: legal
                          right, ask by name, the GP must agree, no
                          guarantee of speed.
      Medication          Your situation: why GPs are stopping, the
                          referral-vs-titration distinction, the
                          realistic waits, bridging prescriptions.
      FAQs                Twelve questions, answered, sourced. Plus
                          the Ask a question form.

    Self-maintaining. Every claim carries an @claim marker (source,
    URL, verified date, review window, population) and a visible
    [source] citation. The gov.waiting_well check reads the markers
    nightly at 6am, flags stale claims and broken URLs, and writes a
    status file the orientation reads. The Ask a question form writes
    to a questions file the orientation also reads — new questions
    surface where the founder looks.

    Marker syntax, so a future session can add claims:
      {/* @claim type="figure" source="..." url="..." verified="YYYY-MM-DD"
          review="30" population="..." */}
    'verified' is the date a human last confirmed the claim, not the
    date the source was published. type is fact | policy | figure |
    advice. review is days.

    The Ask a question loop: a public form -> POST
    /api/waiting-well/question (honeypot + length limit, no user data)
    -> appended to waiting-well-questions.jsonl -> the orientation
    shows "N new question(s) to answer" -> answered by hand, added to
    the FAQ by hand, marked answered -> the count drops.

    Built in two sessions: the shell and the public-surface fix on
    10 Oct morning; the four pills, the check, and the form through
    the day. Found a real bug while building the shell — every public
    page was gated. See gov.public_surface_gated.

    Watching before calling it done: the check has run twice clean,
    one real question answered. Let it run a week and answer a few
    more, then tick to [x]. Raised 28 Sept, revised 9-10 Oct.

    Purpose. In England, over 960,000 people are waiting for an ADHD
    assessment, some two years or more, with almost nothing offered
    while they wait. Healthwatch found people feel abandoned by the
    system during this period. The page fills that gap. It is a
    filter, not a memoir — no first-person voice anywhere on it. The
    lived experience lives on social media and links here.

    The angle. Most waiting-well resources are clinical-adjacent,
    generic self-care, or US-focused. None is UK-specific, calm, and
    built for the whole journey — from "is this me?" through
    assessment and medication. The whole page is about the ADHD tax
    without ever naming it as a problem Bosly solves.

    Structure: ONE landing page with FOUR pills, and FOUR sub-pages
    under it. Five routes total, each indexable (own title, own
    description — not fragments; Google ignores fragments). All in
    app/(marketing)/.

      /waiting-well              the landing. Four pills, short
                                 description each, calm, visual.
      /waiting-well/is-this-me   pill 1
      /waiting-well/assessment   pill 2
      /waiting-well/medication   pill 3
      /waiting-well/faqs         pill 4

    The four pills:

      1. Is this me? — What ADHD and autism can look like, cited.
         The overlap explained (50-70% of autistic people also have
         ADHD; ADHD is under-recognised in women). ADHD traits and
         autism traits differentiated, honestly, with the conflict
         between them named (routine vs novelty, connection vs
         exhaustion). Mirror first, then signpost to the screening
         tools — ASRS, AQ-10, RAADS-R — with a plain warning: a
         starting point, not a test, and not everyone is captured.
         Every claim sourced.

      2. Getting an assessment — The routes. NHS waiting. Right to
         Choose explained properly (ask for it by name, name the
         provider, do not accept a local referral; England only).
         Private. What to ask the GP. What happens at each stage.

      3. Medication — Getting started; staying on it; and the
         shared-care collapse happening now. Why GPs are withdrawing
         (BMA guidance, unfunded, outside core contract). The
         difference between a referral and titration — the referral
         is to join the queue, and the titration queue is the long
         one. Realistic wait times, sourced AND dated. Bridging
         prescriptions. What to do while you wait.

      4. FAQs — Real questions people are actually asking, answered
         plainly, sourced where checkable. Grows over time. Includes
         an "Ask a question" form — see below.

    The footer — ONLY on the landing page (/waiting-well), at the
    very bottom. Not on the four pill pages. Not in the pills.
    Contains, in this order:
      - the Bosly logo
      - "Sponsored by Bosly"
      - "Your digital butler"
      - one concise sentence of what Bosly helps with
      - a link to Bosly
    This is the only place Bosly appears on the entire site.

    The "Ask a question" feature (FAQs page):
      - A simple public form: one textarea, one submit. No account,
        no email required.
      - POSTs to /api/waiting-well/question.
      - Writes to waiting-well-questions.jsonl beside
        unknown-intents.jsonl on the mount.
      - The orientation reads it and shows "Waiting Well: N new
        questions."
      - Questions are answered by hand (sourced, cited), added to the
        FAQ by hand (editing the .tsx), and marked answered.
      - Spam defence at first: honeypot field plus a length limit. If
        abused, add rate limiting.
      - No auto-answering. Medical-adjacent content is written by a
        person.

    Constraints:
      - Public, accessible without login. MUST be added to the
        middleware's isPublicRoute list, or it redirects to sign-in.
        See accord.middleware_public_routes.
      - Lives in the app/(marketing)/ route group with the other
        public pages. Route group /waiting-well, five routes.
      - Start as plain pages: text, links, headings. No chatbot, no
        quiz. Live and linked beats perfect.
      - Stays on the community and resources side of the line. Not
        clinical, not diagnostic, no implied medical judgment. The
        ADHD taskforce has recommended regulation and quality
        standards for ADHD service providers; the page must not look
        like one.
      - No first-person voice anywhere on the page. The lived
        experience lives on social media.
      - The page must not promise more than Bosly does today. The
        footer says what Bosly helps with, not what it will do. See
        accord.admin_assistant_direction.

    Success. Not thousands of users. A handful of the right people.
    Track clicks from the Instagram bio. Adjust framing if it is not
    used.

    THE CHECK — gov.waiting_well, in bosly-gov. The whole point: the
    page evolves, and the check stops it rotting when attention
    moves elsewhere. Slow tier, not fast: it makes HTTP requests to
    external sites, which must not slow or fail the fast tier.
      - HEAD-requests every external link; reports non-200.
      - Reads machine-readable markers in the page source: each
        figure/claim carries its source and the date last verified.
      - Flags any figure not re-verified within a set horizon
        (e.g. 30 days).
      - Reports in the orientation: "Waiting Well: 1 broken link,
        2 figures need re-verifying" or "all clear."
      - Same split as gov.accord_compliance: mechanical drift
        checked, prose reviewed by hand.

    BEFORE BUILD: verify the external claims — the assessment
    waiting figure and its source; the Right to Choose mechanics
    against current NHS England guidance; the medication wait times
    (Psychiatry UK titration, referral processing) with dates; and
    that every resource link resolves.

    Raised 28 Sept. Revised 9 Oct: reframed from lead magnet to
    public resource; four pills instead of six sections; five routes
    instead of one; the self-checking system; the Ask a question
    feature; no first-person voice; the Bosly footer on the landing
    page only.


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


[ ] [LIVE] ops.architecture — The principles the build decisions
    hang from. Written down because every argument about a feature
    will come back to one of these.

    1. One app, many tenants. Bosly Accord is the platform; the
       products are toggles inside it. A client logs in once and
       sees what they've paid for. Not five apps with five logins.
    2. Isolated data. Each client's data is separate at the
       storage layer — separate databases, separate keys, separate
       memory directories. Not "we have access controls"; the data
       is not together in the first place.
    3. Shared inference. One model serves many clients. Each
       request carries its client's context. The model is the
       expensive part and is paid for once, not once per client.
    4. No cloud. Ever. The client product runs on hardware Bosly
       controls. The reason the product is worth anything is that
       the data never leaves a machine the client's supplier
       controls. If it outgrows the box, the answer is a bigger
       box or a second box, both owned. Not a rented one.
    5. Scale is vertical until it isn't. One machine, upgradeable
       pieces. The GPU is the swappable heart; RAM, storage, PSU
       are independent. Current-gen motherboard so the next
       generation is a swap, not a rebuild.

    Read this before proposing a feature that touches storage,
    auth, or hosting. If the proposal breaks one of these, it's
    not the feature that's wrong, it's the proposal.


[ ] [LIVE] ops.external_services_degrade_honestly — FOUND 19 Oct.
    Three times today an external thing failed and the system lied
    about it:

    - pm2 restart did not reload changed Python; the service kept
      running old code and reported 'online'.
    - Cloudflare Access looked configured but was not attached;
      gov.bosly.app went straight through with no login.
    - All three Overpass mirrors 502'd or timed out; the lead
      scout printed '0 businesses found', which looked identical
      to a real zero.

    The rule: when an external service fails, say so. A zero result
    and an outage are different states and must read differently.
    The lead scout now does this ('this is an endpoint problem,
    not a zero result'). The pm2 note is: use delete + start, not
    restart. The Cloudflare note is: attach the policy and save
    the application, or the login never appears.

    General: any code that calls something outside the process
    must distinguish 'it failed' from 'it returned nothing'.


[ ] [LIVE] accord.lead_machinery — FOUND 19 Oct, forgotten. A
    real lead pipeline already exists in Accord, built for the
    gardening business, and it was not in the plan. Three files:

    lib/auto-lead.ts (5.4 KB) — maybeAutoLeadFromConversationId:
    reads a conversation, decrypts the inbound message, checks
    whether it is already linked to a card, and if not, creates a
    lead card from the contact. The card carries the source
    (email / WhatsApp / Instagram / Facebook / phone / website),
    the contact details, and the first meaningful line of the
    message as the title.

    lib/leadSources.ts (110 B) — the six-source taxonomy.

    .data/lead-values.json — per-lead values. Eight entries now
    (hedge trimming £80, patio cleaning £150, ...). Used to
    prioritise; probably test data but the structure is real.

    Wired into the app: app/api/user/route.ts:24 exposes
    leadSources, so this is live, not dead code.

    THREE THINGS CALLED "LEAD", and they must not be conflated:
      1. accord.lead_machinery (this) — the gardening business's
         inbox-to-lead capture and valuation. Live in the app.
      2. ops.consultancy Phase 3 — the scouting script that finds
         businesses with no website. A script, not the app.
      3. The Executive's business memory (things store) — holds
         leads among everything else. A store, not a pipeline.

    They could meet one day: a gardening lead is a thing, and
    could live in the things store. But they are different jobs
    today, and the plan should say so before the word "lead"
    hides the difference.

    Not touched by today's work. Recorded so it is not forgotten
    again.


[ ] [LIVE] ops.scout_persona_filter — FOUND 29 Oct. The LinkedIn tip:
    run scout candidates past personas before acting.

    THE TIP: a contact suggested personas-as-a-filter — create distinct
    points of view, run leads through them, see what they say. The
    second half (self-healing) waits: it needs a deterministic check
    that can say whether a verdict was right, and that doesn't exist
    yet. A healer on an unproven filter is the same mistake as raising
    a number without evidence.

    THE SHAPE: three personas (the skeptical café owner, the busy
    hairdresser, the one who hates booking pages), one question each,
    a structured verdict: interested / not / maybe, one line why. The
    scout's ranking shows the persona verdict alongside — a high rank
    with three "not interested" is visible, and that's the useful part.

    WHY BUILD IT: MiroFish is a heavyweight (OASIS, GraphRAG, Zep,
    Docker, two API keys, Flask + Vue) — the scout needs ~100 lines,
    not that stack. Prior art proves the small version: personas in,
    structured verdict out. The value is in the skeptical personas, not
    the agreeing ones — if all the personas think like me, the filter
    says yes to everything I already believe.

    NOT NOW: the loop is first. This waits for the butler to run it.


[ ] [LIVE] ops.lead_workflow — THE WEEKLY LEAD LOOP. DEFINED 19 Oct.

    WHAT THIS IS, IN ONE LINE: a digital butler. A personal PA for
    the founder's life and work — the thing that holds the threads,
    does the admin, and brings back the work without being asked
    twice. This entry is the first real job that proves it: finding
    clients for the consultancy, from search to sent email, with
    the founder in the loop at every gate.

    THE SEQUENCE, with trigger and guard for each step:

    1. THE SCRIPT RUNS (weekly, cron). The lead-gen script from
       ops.consultancy Phase 3 runs Sunday night. It reads public
       data, writes a CSV, exits. Nobody watching. The script is
       read-only against the internet; it writes one file. No
       guard needed — it cannot touch anything else.

    2. THE EXECUTIVE NOTICES (on startup or first message). A
       timestamp check: is lead-scout.csv newer than the last time
       I read it? If yes, read it and brief the founder: "3 new
       candidates. Company X has no site and takes bookings by
       phone. Company Y has a site but no booking. Company Z looks
       too big. Want the details?" That is the morning briefing,
       applied to leads. Read-only.

    3. PERMISSION TO RESEARCH. The founder says "go on then" or
       "research these three". Asking is granting. The Executive
       reads each site, checks their presence, works out the fit.
       Read-only — fetching a page doesn't need permission.

    4. THE FOUNDER'S OWN SEARCH. Deliberately in the loop. The
       Executive's research is an input, not the answer. The
       founder looks too.

    5. PERMISSION TO DRAFT. The founder says "draft the emails".
       The Executive writes one per company, adapted to each,
       using the specific findings from step 3. It does NOT send.
       Draft is text; it is not an action on the world.

    6. THE DRAFT COMES TO THE FOUNDER. send_draft_to_me emails the
       drafts to jr-arnott@outlook.com (the address the monitor
       already uses). SMS is later. The point: the founder reads
       the draft while on the phone to the Executive, or walking,
       or away from the desk. Two channels, one loop.

    7. THE FOUNDER APPROVES, and only then: send_email. Guarded.
       Requires an explicit "send it". Each lead becomes a thing
       in the business memory — ID, company, what was found, the
       email sent, the outcome, the date. The "each lead gets an
       ID; note the outcome" loop from Phase 3, made real.

    THE PROACTIVE TRIGGER IS A FILE, NOT A TIMER. The Executive
    does not hold a scheduler. It checks "is this file newer than
    the last time I read it?" A small state file records the
    last-read timestamp. That is the whole proactive loop, and it
    is about 20 lines. It means the Executive cannot forget to
    run; the cron does. It means the Executive only acts when
    there is something new.

    THE GUARDS, in one place:
      - The script: writes one CSV, reads public data only.
      - Step 2 (notice): read-only.
      - Step 3 (research): fetch, read-only.
      - Step 5 (draft): produces text, no action.
      - Step 6 (send draft to founder): sends to the founder only.
      - Step 7 (send email): guarded, requires explicit approval.

    WHAT THIS NEEDS TO BUILD, in order:
      [ ] The business memory (Step 1 of the Executive build
          order). Leads are things. Every step after this writes
          a thing.
      [ ] The scouting script as a cron job. The script is Phase 3
          of ops.consultancy; the cron line is new.
      [ ] The "new CSV" pickup in the Executive. Timestamp check,
          read, brief.
      [ ] draft_email tool. The model drafts, the tool returns
          the text.
      [ ] send_draft_to_me tool. Emails the draft to the founder.
      [ ] send_email tool. Guarded; requires explicit approval.

    WHY THIS IS THE FIRST REAL JOB. It is concrete, it pays
    (it finds clients), it exercises every part of the Executive
    (notice, research, draft, ask, send, record), and every step
    has a natural gate where the founder stays in control. Build
    this, and the Executive is a working PA. The rest — calls,
    admin, the voice — is more of the same with different tools.


[ ] [LIVE] gov.executive_orientation_and_reporting — DEFINED 19 Oct.
    How the Executive briefs, reports, and asks permission.

    ORIENTATION IS ABSORBED, NOT DELETED. The `bosly` command
    becomes a thin wrapper that asks the Executive. The Executive
    runs the same checks, reads the plan, the memory, and the
    business store, and answers "what's going on?" in
    conversation. That is the morning briefing: what broke
    overnight, what needs a decision, what can wait. The founder
    says "off you go" — that is permission — and the Executive
    fixes it, with the Custodian's checks confirming the fix.

    THE THREE REPORTING CHANNELS, escalating by urgency:
      1. Email — the default. What it did, why, how, whether
         action is needed, and a severity: low / medium / high /
         critical. Low/medium say "no action needed"; high/
         critical say "ACTION NEEDED" and say what.
      2. In-conversation — when the founder is in the UI. The
         tool-call events already do this; results follow.
      3. Phone call — later, when connected. For time-sensitive
         and high-value: "I found a client, this is time-
         sensitive, do you want me to email them?" An email takes
         a day; the opportunity does not.

    THE PERMISSION MODEL: ASKING IS GRANTING. "Find me companies"
    is permission to search. "Off you go" is permission to fix.
    But sending, posting, deleting, spending — always a question
    first, with the proposed action stated plainly. Sensitive
    actions get a question BEFORE the action, not a report after.

    Build needs: the report tool takes severity and needs_action;
    the permission rule in tools_prompt.txt (done 19 Oct); the
    `bosly` command changed to call the Executive's briefing.


[ ] [LIVE] ops.bosly_executive — THE CHIEF OF STAFF. The
    conversation that holds the whole of the digital side of the
    business so the founder's ADHD doesn't have to.

    WHAT IT IS, IN THE FOUNDER'S WORDS. "It will save me from my
    ADHD, and keep on top of all of the digital stuff for me."
    You talk to it like a person. It talks back. You plan
    together, and the plan persists — not a chat that scrolls
    away, but PLAN.md itself, written as you go. You dump
    everything that's in your head, and it catches it.

    WHAT IT DOES — THE JOBS IT HOLDS. Each of these is a thing
    the founder currently does by hand, or drops:

    - The morning briefing. "What's going on today?" — the
      calendar, the inbox, the plan, the leads, in one answer.
    - The dump. Everything in the founder's head, said out loud,
      held. The day, the clients, the builds, the ideas. So the
      ADHD doesn't have to hold them.
    - The plan. Planned together, written to PLAN.md, and
      remembered. The plan entry the Custodian wrote today is
      the first piece of this working.
    - "Leave that with me." The founder goes shopping. It works.
      It calls: "I found the client for that build, I've done X,
      Y, Z, shall I go ahead?" Yes or no, or "what happened?"
      and it tells you.
    - Failure, handled. "That didn't work, but I've rolled it
      all back. Everything's safe. Should we work out what
      happened?" Rollback must be real, not claimed, and it must
      report when it rolled back.
    - Call notes. It listens to client calls, specialist calls,
      the hairdresser. It records the useful facts and reads
      them back.
    - Client portfolios. "This client is a hairdresser, they
      need X and Y." It knows that, remembers it, builds from
      it.
    - The digital admin. Email, follow-ups, invoices,
      notifications. The threads that fall through the cracks.
    - Leads. Businesses that look like a good fit, researched
      and brought back.
    - The interface to everything. Accord, Keep, Custodian, the
      consultancy. One way in. "What's going on?" dips between
      all of them and answers.

    WHAT IT IS NOT: not a chatbot, not a command line. A
    persistent colleague that knows the business and the person
    running it. And not the verifier — the Custodian verifies.
    The Executive proposes and acts; it cannot verify its own
    work.

    IT IS ALSO A PRODUCT. The same shape, tuned to each client.
    A hairdresser's chief of staff is the same architecture,
    different instance. The Executive the founder builds for
    themselves is the model for the client version. This is why
    it is built first — it is the founder's tool and the
    template for the product.

    BUILD ORDER — the current sequencing, written 19 Oct. Each
    step is useful on its own; each teaches what the next needs
    to be.

    The Custodian is the foundation. The Executive reuses the
    Custodian's four tools (read_file, append_plan_entry,
    save_memory, run_check) and its guards, and adds six of its
    own (save_thing, read_thing, find_things, link_things,
    draft_email, send_draft_to_me, run_lead_scout, read_leads,
    send_email — ten in all). Every Executive action goes
    through a guard, and the guards are one pattern, not two.

    UPDATE 19-20 Oct: ten tools now, not four. The Executive
    does have tools of its own; the Custodian's are the
    foundation, not the whole. The four
    Custodian tools above, plus six Executive tools:
    save_thing, read_thing, find_things, link_things (the
    business memory), draft_email, send_draft_to_me,
    run_lead_scout, and send_email. All in routers/tools.py,
    same {ok, result|error} shape, same guard pattern. The
    Executive does not have a separate tool registry — the
    tools are one list, and the guards are one pattern.

    STEP 1 — THE BUSINESS MEMORY. [x] DONE 19 Oct.
    routers/things.py: a SQLite store of "things" — kind (free
    string: client, lead, project, idea, draft), title, status,
    body (markdown), tags. Accent-insensitive search ("Cafe"
    finds "Café"). Four tools: save_thing, read_thing,
    find_things, link_things. 16-case self-test. 17-case
    tool-wrapper self-test.
    DONE WHEN: the Executive can answer "who are my clients
    and what do they need?" from the store — verified: it
    found the Café Corner lead by name and read the email
    from the record.

    STEP 2 — THE MORNING BRIEFING. [~] PARTIAL 20 Oct.
    Read-only. Calendar, inbox, plan, business memory. One
    answer. No actions.

    BUILT:
      - The pickup (routers/pickup.py) — notices a new scout CSV.
      - routers/ecosystem.py — ecosystem_state(section), one reader
        for the whole ecosystem: plan, things, scout, capsules.
        Verified: "What is going on today?" returns a real picture
        from all four working sources in one tool call.
      - The accord section is present but says 'not yet — needs the
        session token'.

    STILL OPEN: the accord sections (calendar, inbox, invoices)
    need the session token (gov.executive_access). Until then the
    briefing covers plan, things, scout, and capsules.

    DONE WHEN: the founder asks "what's going on today?" and gets a
    real answer drawn from the plan, the business memory, the
    scout, AND Accord's calendar and inbox.

    STEP 3 — THE PROACTIVE LOOP. "Leave that with me." A task
    queue, a scheduler, a report-back path. The Executive works
    while the founder is not watching, and calls back with
    what it did. Real rollback, visible: if it acted, it must
    be able to undo, and it must report when it rolled back.
    WHY THIRD: it is the biggest piece and the one where the
    balance of powers matters most. Every action goes through
    the Custodian. It depends on steps 1 and 2: there is
    nothing to work on proactively until the Executive knows
    the business and can brief on it.
    DONE WHEN: "leave that with me" produces a real report
    later, and a failure produces a real rollback and a
    real explanation.

    STEP 4 — EMAIL AND CALLS. The integrations. Drafting
    first (the Executive writes, the founder approves, it
    sends). Listening later (call transcription and notes).
    WHY FOURTH: it needs the proactive loop to be useful —
    drafting an email that waits in a queue is a draft; the
    loop is what makes it a chief of staff that handles the
    admin.
    DONE WHEN: a client email arrives, the Executive drafts a
    reply, the founder approves it, it sends.

    STEP 5 — THE VOICE. Text-to-speech first (it speaks, you
    listen). Listening last (it hears the call). The wrapper,
    not the substance.
    WHY LAST: the substance comes first. By the time the
    voice is built, the Executive will already be useful by
    text. The voice is the way in, not the thing itself.
    DONE WHEN: the founder talks to it and it answers by
    voice, from the same business memory.

    EARLIER SEQUENCING (superseded 19 Oct, kept for the
    history — the first three are now done):

      1. Text interface, working, used daily. Talk to it; it
         writes to the plan and memory through Custodian tools.
         This is "stop being the courier" and it's close —
         Custodian already has the API and the UI (broken).

         [x] UI connects and answers — DONE 19 Oct. The UI was
         calling /gov/api/*, but do_GET and do_POST exact-matched
         /api/* routes. /gov/api/chat/stream 404'd and
         /gov/api/health returned index.html via the static
         fallback. One strip at the top of each handler fixed it.
         Verified: the Custodian UI answers a message with real
         context from the manifest and memory. Commit a89fef6.

         [x] Tools: the conversation can read the plan, write a
         plan entry, write a memory entry, read a file, run a
         check. DONE 19 Oct. routers/tools.py, 13-case
         self-test. read_file and append_plan_entry tested end
         to end through the UI; save_memory and run_check
         untested but built.
      2. Tool loop. It reads the code, proposes patches, runs
         the checks. Now it builds with you.

         [x] Tool loop — DONE 19 Oct. routers/tool_loop.py,
         8-case self-test. Wired into /api/chat,
         /api/chat/stream, and /api/project/{slug}/chat (the
         endpoint the UI uses). Verified through the UI.
      3. Email and admin. It drafts, you approve, it sends.
         First "saves me time" feature. — moved to Step 4 above.
      4. Client memory and portfolios. It remembers the
         hairdresser needs X. — moved to Step 1 above.
      5. Text-to-speech. It speaks to you. Easier than listening,
         high value. — moved to Step 5 above.
      6. Listening (call transcription). Last, because it's the
         hardest and the most likely to disappoint. By the time
         it's built you'll know whether the product works. —
         moved to Step 4 (later half) and Step 5 (last) above.

    The rule that makes it safe: the Executive cannot verify its
    own work. Every action goes through Custodian checks. When
    the Custodian says no, the Executive reports it; it does not
    route around it. This is the balance of powers — see the map
    at the top of this file.

    Unattended action requires real rollback. If it acts while
    the founder is not watching, it must be able to undo, and it
    must tell the founder when it did. Claimed rollback is not
    rollback. That is a build in itself.

    Priority: build first. It's the founder's tool and the model
    for the client version.


[ ] [LIVE] ops.bosly_receptionist — THE AI RECEPTIONIST. The
    first client-facing toggle. Bounded, and that's the point: a
    workflow, not a general assistant.

    What it does: answers the call, transcribes, classifies
    intent (book / enquire / complaint / other), books or routes,
    logs the call. Same workflow for every client, with their
    rules and their calendar.

    Why it's bounded: it's a workflow, so it can be specced,
    built, and verified. Unlike the Executive, it has a finite
    list of jobs. That's why it's second: the Executive teaches
    the tooling, the Receptionist proves it on a client.

    Pricing: £1,000–£1,500 build + £250–£500/month ongoing,
    priced per client against the human equivalent
    (£1,200–£1,500/month for a human receptionist). Same
    principle as every toggle: the ceiling is what the human
    costs, the floor is what the client can bear. Price each one.

    Deadline: January. The first thing a hairdresser (or any
    small business drowning in phone admin) will pay for.

    Build order: spec the workflow first. The code is mechanical
    once the spec is right.


[ ] [LIVE] ops.training_set — THE FRAME. The plan, the memory,
    and the capsule are not admin. They are the training set.

    Long-term intent: Bosly becomes its own AI — a model shaped
    by the founder's decisions, reasoning, and corrections, fine-
    tuned on the accumulated data. Not trained from scratch;
    steered by everything written. Same base, different shape.

    What that needs:
      - Plans (decisions and why). Have these.
      - Memory entries (lessons, patterns, incidents). Have
        these; consistent style matters.
      - Decisions with reasoning. The gold. In plan entries and
        in conversations.
      - Corrections (the "no, not that" moments). Most valuable,
        because judgment is mostly knowing what not to do.
      - Domain knowledge (investing principles, ethical
        exclusions, UK compliance, the consultancy offer).

    What's missing: conversations as data. The reasoning that
    produced the entries is where the learning is, and right now
    it evaporates. The capsule is the attempt to hold it. The
    habit is not yet as strict as the plan or the memory. It is
    the one to strengthen — the plan holds the result, the
    capsule holds the thinking, and the thinking cannot be
    reconstructed after the fact.

    Retrieval first, fine-tuning second. The thing that makes
    an assistant feel like yours is mostly that it remembers
    your context. The memory system is retrieval. The fastest
    path to "Bosly feels like Bosly" is better retrieval, not a
    bigger model. Fine-tuning comes after.

    The data must be clean to train on. The memory schema check
    is the model: a model trained on malformed entries learns
    the malformation. The checks that keep the system honest
    are the checks that keep the training data good.

    Write for yourself, not for the model. The training value
    is a side effect of writing well, not a reason to write
    differently. If plan entries start being written as training
    data, they stop being good plan entries, and the thing that
    made them valuable is lost.


[ ] [LIVE] ops.hardware_plan — The box. And the constraint that
    shapes it.

    Constraint: no cloud. The client product runs on hardware
    Bosly controls. See ops.architecture, principle 4. This is
    not a cost decision, it's the promise the product is built
    on. AWS was used and removed because control of the machine
    is the whole point.

    Now (personal/first-few-clients box): £1,200–£1,500.
      - GPU: used RTX 3090 (24GB) is the sweet spot. Runs a
        14B model comfortably, 32B quantised. The single
        decision that matters most.
      - RAM: 32GB minimum, 64GB if running assistant + voice +
        model together. Cheap, max it.
      - CPU: mid-range Ryzen. Don't over-spend.
      - PSU: 1000W. Over-specify now so a second GPU later
        doesn't need a swap.
      - Storage: 1TB NVMe.
      - Motherboard: current-gen. The one place not to save
        money — it determines how easy every future upgrade is.

    Later (the platform box, when 5+ clients are real): a bigger
    server for the client tenants. One machine, many tenants,
    isolated data, shared inference. Not 50 machines; not cloud.

    Upgrade path — the pieces age independently:
      - GPU: swap when the model grows or clients need more.
      - RAM / storage: add sticks / add an NVMe. Cheap.
      - PSU: already sized for a second GPU.
      - CPU: ages slowest; only swap with a motherboard jump.
      - Motherboard: current-gen buys 5 years of easy upgrades.

    Home server runs inference, not training. Fine-tuning is done
    rarely, on rented GPU hours, from data accumulated locally.
    Home machine runs it; cloud trains it, occasionally.


[ ] [LIVE] accord.invoice_mobile_layout — The line-item row in
    the Accord invoice editor is squished on mobile. It stacks
    (flex-col sm:flex-row, patched 19 Oct), but each input is
    still tight and the columns are hard to read on a phone.
    Deferred because the founder is the only user right now.
    Fix: proper mobile form layout — labels, or a two-column
    grid, or a mobile-specific row shape. Also affects the
    preview table (5 columns on a phone).

    Also found: components/workspace/InvoicePreview.tsx is dead
    code — nothing imports it. It was patched on 19 Oct before
    that was discovered, and the actual preview is inline in
    InvoiceEditor.tsx. Decide: delete it, or wire it in as the
    real preview.

    Also found: two invoice tools (app/(marketing)/invoice — free,
    public; components/workspace/InvoiceEditor — the Accord one).
    They don't share a line-item type or a render. Every invoice
    change must be made twice. Consider unifying the LineItem
    shape at least.


[ ] [LIVE] ops.consultancy_design — The front door looks correct,
    not striking. The structure and copy are settled; the gap is
    visual — proportion, rhythm, weight, motion. A page worth hiring
    from, not just a working page.

    THE LOOP: Claude Pro can see images, which nothing else in the
    stack can. Screenshot the page, ask what's off, change one thing,
    screenshot again. The visual feedback loop closes in a chat
    interface, not in code.

    SETUP: a Claude Pro account (~£18/month, separate from the API
    key Gov already uses). Pro is the tier with Claude Design.
    Business expense, not personal.

    THE JOB: not a rebuild. The page is a headline, an about
    paragraph with a photo, three capability cards, a form, and a
    footer. The work is making those feel decided rather than safe.
    Reference-led — find a page that feels right and build to that
    structure, not to "make it better".

    Raised 10 Oct.


[ ] [LIVE] ops.consultancy_sales_sequence — How a lead becomes a
    client. Five stages, and the order matters. The instinct is to
    send the demo first; the right move is to earn it.

    STAGE 1 — THE DAY ZERO EMAIL. The observation, from the lead-gen
    tool. No link, no demo, no ask beyond a reply. One or two a day,
    not ten. The purpose is not to sell — it is to get a reply.
    Deliverability note: a first cold email with multiple links drops
    inbox placement from 89% to 58%. So: no link in the first email.

    STAGE 2 — THE REPLY. They respond. You say what you noticed, and
    ask for a call. "What I found from the outside is probably not
    the whole picture — can I ask you a few questions?"

    STAGE 3 — THE DISCOVERY CALL. 20/80 — you talk 20%, they talk
    80%. This is a consultation, the skill from 20 years of
    hairdressing. Five questions, same for every vertical, different
    words:

      1. Where does the admin eat the most time?
      2. What falls through the cracks most often?
      3. How do you handle that now? (The workaround. If the answer
         is "I remember it" or "it's in my head", that is the gap.)
      4. If you could only fix one, which would make the biggest
         difference? (Everyone has a list. You need the one.)
      5. If that were fixed, what would change? (Not a price —
         the outcome. You repeat their words in the demo.)

    Vertical variants: hairdresser — missed calls; plumber — quotes;
    dentist — no-shows; agency — hours tracking. Same five, different
    words.

    Write down their exact phrases, not your summary. "I lose the
    Saturdays" goes in the demo email, not "reduced admin burden".

    Do not solve on the call. The urge is strong and it is the
    craftsman's urge — you see the problem, you know the fix, you
    want to show your work. It is mistimed. The fix belongs in the
    demo, where it is evidence, not in the call, where it is talk.

    STAGE 4 — THE CLOSE. A summary and a next step. Nothing else.

      "That's really useful — thank you. Let me make sure I've got
      it right. The thing costing you most is [their words]. It's
      happening because [what they said], and right now you handle
      it by [their workaround]. Have I got that right?

      Leave it with me. I'll put together something that shows what
      this could look like — nothing you have to commit to. I'll
      send it over in the next few days."

    The summary is the close. Saying their problem back accurately
    is what makes someone want to work with you — not the solution.
    "Nothing you have to commit to" removes the pressure. "In the
    next few days" buys the time to build, and is a reason to email
    again.

    If they push — "what would you actually do?" — the answer is:
    "A few things, probably. But I'd rather show you than tell you.
    Give me a couple of days."

    STAGE 5 — THE DEMO. Built after the call, not before. This is
    the whole point of the order: a demo built before answers what
    you think they need; a demo built after answers what they told
    you. One per vertical, reused — the hairdresser demo goes to
    every hairdresser who takes a call. But it is sent only to
    someone who has already talked to you.

    The demo shows the OUTCOME, not the website. A hairdresser does
    not want a prettier website; they want the phone answered at
    9pm and the booking in the calendar. Lead with that.

    Delivery: a YouTube thumbnail embedded in the email as an image,
    hyperlinked to a two-minute video. One link, to a reputable
    domain. A Loom — your face, your voice, their problem — beats a
    static site every time. Keep it under three minutes.

    THE COST PER INTERESTED COMPANY: about an hour. 5 min email,
    2 min reply, 30 min call, 15-30 min demo, 5 min send. And the
    first three stages filter hard — most will not reply, and the
    ones who take the call have qualified themselves.

    Raised 11 Oct.


[ ] [LIVE] ops.consultancy_contract_terms — The foundation of the
    client agreement. Not the full contract — the decisions that
    shape it. A solicitor reviews the wording before it is used; this
    is what it has to say.

    THE OFFERING, FOUR PARTS SOLD AS ONE RELATIONSHIP:
      Audit        £500-2,000, one-off. The entry point.
      Build        £2,000-5,000, one-off. Website, receptionist, or
                   setup.
      Retainer     £200-500/month. Maintenance, hosting, updates,
                   care.
      Licence      Bosly owns the software; the client uses it.

    THE TERM. Twelve months, then rolling monthly. The year recovers
    the build cost and filters for serious clients. The roll after
    keeps it flexible.

    OWNERSHIP, STATED PLAINLY:
      - The website and any software built by Bosly Ltd remain
        Bosly's. The client holds a licence to use them.
      - If the client cancels or does not renew, the software is
        taken offline at the end of the billing period. Written
        explicitly, not implied.
      - The client's data is the client's. Handed over on exit, in a
        usable format. Always. This is the same principle as Bosly's
        export, and it is a selling point.
      - The domain is the client's, always. If they have one, they
        keep it. If they don't, they register it themselves. Bosly
        never holds a domain as ransom — that is a business risk as
        much as an ethics one: "my web guy held my domain hostage" is
        the most damaging story a local consultant can have, and it
        kills the referrals that are the growth engine.

    THE BUYOUT. At any point the client can pay a one-off sum to own
    the software outright and stop the subscription. Removes the "you
    own nothing" objection, and is a route to a larger single payment.
    Most will not take it.

    ON EXIT. Find out why they are leaving, and note it. Three
    clients leaving for the same reason is a product problem; a
    business closing is nothing. The exit conversation is a signal,
    not a retention trick. Then let them go cleanly — data handed
    over, software down, domain untouched.

    NOT YET DONE: the full wording, and a solicitor's review. This
    entry is the decisions; the document comes when a client is
    close, so it does not drift while it waits.

    Raised 12 Oct.


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


[~] accord.invoice_aggregates_client_appointments — READ SIDE TESTED 10 Oct,
    The write side is unproven. The schema (invoicedAt + invoiceId on CalendarEvent and
    two composite indexes), a shared nextInvoiceNumber in
    lib/invoices/numbering.ts, the read route (GET
    /api/invoices/unbilled?from=&to= groups unbilled events by contact
    with hours and totals), the write route (POST
    /api/invoices/aggregate creates one invoice and marks its events in
    a single transaction), the Unbilled tab in Finance, and the
    confirmation modal are all in.

    The two safety nets against double-billing are the pre-check
    (every event unbilled, owned, for the stated contact) and the
    conditional update with invoicedAt: null in the WHERE clause. If
    the count of updated rows does not match, the transaction throws
    and the invoice rolls back. The crux the original entry names —
    a billed state so a second press does not double-bill — is the
    invoicedAt column, set inside that transaction.

    TESTED 10 Oct. The Unbilled tab loads against real data, shows
    the clients, their hours, and their totals. Testing found two
    bugs that only appeared at runtime, both fixed in dda104d:
    contact names showed as "[encrypted]" because the read route
    returned the plaintext placeholder instead of the encrypted
    field, and the component fetched in a loop because its load
    callback depended on the whole useFeedback object, which is a
    new reference every render. The fix: the route returns the
    encrypted contact data, the component decrypts it, and the
    effect depends on fb.fail (stable) not fb.

    The aggregate route itself has not yet been run — no invoice has
    been created from the modal. That is the last untested step.

    Original entry follows.
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


[ ] [LIVE] accord.invoice_sender_picker — The send dialog has a
    sender picker, shown when more than one connected account
    exists. Built 30 Sept but only exercised with one account;
    the dropdown path is unverified. When a second account is
    connected (e.g. a personal one), test that choosing it sends
    from that address. The backend (getTransporter fromAccountId)
    is done and rejects an unknown account rather than falling
    back. Raised 30 Sept.


[ ] [DECISION] accord.unlogged_invoice_prompt — Chat-driven invoice detection. ORIGINALLY designed as: user asks "have I sent any invoices I haven't logged?", a server route reads the Sent folder and returns metadata only, the browser asks which to log. NEEDS RE-FRAMING: the chatbot is now a workflow engine without an LLM. Two options: (a) a workflow engine recipe that asks the browser to scan the Sent folder client-side; (b) wait for the local model. Lean: (a), since it's a deterministic pattern (read emails, count, ask browser to compare).



[ ] [DECISION] accord.follow_up_prompt — Chat-driven follow-up. ORIGINALLY: user asks "which invoices need chasing?", the browser identifies overdue invoices from decrypted data, prompts to send, builds emails client-side. NEEDS RE-FRAMING: same shape as above. This is a workflow engine recipe, not an LLM feature. The browser does the identification; the workflow engine handles the intent.



[ ] [LIVE] accord.wellness_amount_check — Client-side anomaly check. ORIGINALLY: the browser computes per-client averages from decrypted data and surfaces anomalies locally. This is a workflow engine pattern. No LLM needed. Still valid as designed — the browser does the computation.



[ ] [LIVE] accord.email_relay_encryption — Option D for the email relay.
    Encrypt the email body client-side with a per-request
    throwaway key that the server decrypts in memory, uses for
    the SMTP call, and immediately discards. Server never holds a
    persistent view. Current state is Option B (documented
    transparently).


[ ] [LIVE] ops.gate_private_hostnames — DONE 19 Oct. The Custodian
    and Keep were both publicly readable on the internet:
    gov.bosly.app returned 200 and /api/projects returned the
    names of all three repos; keep.bosly.app was equally open.
    Both are now behind Cloudflare Access (Zero Trust): a
    self-hosted application per hostname, an Allow policy
    matching jr-arnott@outlook.com, deny by default. Access
    remembers the browser for 24 hours, so a second hostname
    opens without a prompt once you have logged in once — that
    is SSO, not a misconfiguration. bosly.app (Accord) stays
    public, which is correct.

    What is not done: the tunnel's "Protect with Access"
    toggle (defence in depth — validates the JWT at cloudflared,
    not required for the prompt but worth turning on). Any new
    hostname added to the tunnel must be gated the same way
    before it goes live.


[ ] [LIVE] ops.gate_private_hostnames — DONE 19 Oct. The Custodian
    and Keep were both publicly readable on the internet:
    gov.bosly.app returned 200 and /api/projects returned the
    names of all three repos; keep.bosly.app was equally open.
    Both are now behind Cloudflare Access (Zero Trust): a
    self-hosted application per hostname, an Allow policy
    matching jr-arnott@outlook.com, deny by default. Access
    remembers the browser for 24 hours, so a second hostname
    opens without a prompt once you have logged in once — that
    is SSO, not a misconfiguration. bosly.app (Accord) stays
    public, which is correct.

    What is not done: the tunnel's "Protect with Access"
    toggle (defence in depth — validates the JWT at cloudflared,
    not required for the prompt but worth turning on). Any new
    hostname added to the tunnel must be gated the same way
    before it goes live.


[ ] [LIVE] ops.security_posture — What Gov already covers, what the
    SAST and SCA tools add, and the rules file for AI coding tools.
    Written because the receptionist is being built, not because it
    might be. Security is decided before the build, not after.

    THE PRINCIPLE: AI output is a draft, not a finished product.
    Every line shipped is the founder's responsibility, whatever
    wrote it. The tooling exists. The discipline is the
    differentiator. Gov is the discipline.

    WHAT GOV ALREADY COVERS, mapped to the SHIELD framework:

      Separation of duties — AI has no production access. The chat
        reasons; the founder executes.
      Human in the loop — every patcher aborts on missing anchors;
        every change verified with tsc, build, check tier.
      Input/output validation — gov.stub_detection,
        gov.naming_honesty, gov.claim_invariants.
      Security helper models — gov.secrets_audit (exposed
        credentials), gov.email_password_plaintext.
      Least agency — the chat drafts; the founder executes. No AI has
        write access to the repos or server.
      Defensive controls — gov.tsconfig_excludes (live code hidden
        from the compiler), gov.orphaned_routes (unreachable code).

    And the architectural ones built deliberately:
      Zero-access encryption — the server never reads plaintext.
      Consent gating — gov.consent_gating.
      Public routes public, paid gated — gov.public_routes_are_public,
        gov.paid_routes_gated. That is OWASP A01, the top risk.
      Secrets handling — .env checked, no hardcoded credentials.

    WHAT IS MISSING, and gets added before the receptionist ships:

      1. SAST — taint analysis, tracking user input to dangerous
         sinks. Gov checks invariants and behaviour; it does not do
         this. basesec (npx basesec scan ./src --severity high) —
         65 rules, taint analysis, Prisma and Next.js aware. Catches
         SQL injection in $queryRaw, dangerouslySetInnerHTML, open
         redirects, NEXT_PUBLIC_ secret exposure. Run once on the
         existing code first; the result is evidence either way.

      2. SCA — dependency scanning. OWASP 2025 ranks Software Supply
         Chain Failures third. AI-suggested dependencies are a real
         risk: typosquats, non-existent packages, compromised
         versions. guardvibe scan_dependencies, checked against OSV
         with reachability analysis.

      3. Slopsquatting — AI generates placeholder package names that
         do not exist; attackers register them. Verify every package
         in package.json is real, maintained, and not flagged.

      4. Prompt injection — becomes real the moment the receptionist
         takes a call. @barric/next wraps Next.js route handlers
         with injection detection and PII redaction. Non-optional
         for any route that accepts user input.

      5. Tenant isolation, when accord.business_setups ships —
         multiple businesses on one Bosly instance is OWASP A01 at
         the data layer. Prisma Row-Level Security via middleware,
         with fail-closed default: a query without tenant context is
         blocked, not allowed.

    AND ONE FILE: a rules file for AI coding tools, in the repo root,
    so every AI-assisted change is held to the same standard. VettIQ
    publishes Next.js + Prisma security rules that Claude Code
    enforces automatically. Drop it in; it costs nothing and catches
    the class of mistake that is invisible in review.

    THE ORDER: run basesec and the dependency scan on the existing
    code first. Fix what they find. Then add the rules file. Then
    build the receptionist with the SAST layer already in place.

    UPDATE 16 Oct: the dependency scan is done. npm audit found 51
    vulnerabilities. The safe patch upgrades — next 15.5.15 to
    15.5.28, next-auth 4.24.13 to 4.24.15 — closed two criticals.
    Those were the ones that mattered: the Next.js middleware
    bypasses are the same category that bit the public-routes list
    on 10 Oct, and the next-auth issues included OAuth state not
    bound to its provider. Both fixed, build passes, 60 pages, app
    running.

    The count stayed at 51 because the safe upgrades cannot touch
    the rest — they need major version upgrades:
      - nodemailer 7 to 10 (breaking — invoice, waitlist, and
        support email all need re-testing)
      - prisma 6 to 7 (breaking — schema and client both change)
      - the DoS set in build tooling (tar, brace-expansion,
        minimatch and the rest) — low priority, not in the runtime
        path

    And one lesson: npm audit fix --force would have upgraded
    nodemailer, prisma, sharp and about 90 other packages in one go,
    and closed zero vulnerabilities. The dry-run showed that. Do not
    run it. The two criticals were fixable within the same major;
    everything else needs a planned migration.

    caniuse-lite updated to 1.0.30001816; the build warning is gone.

    Still to do: basesec on the existing code, and the two major
    upgrades, each its own session.

    Raised 15 Oct, updated 16 Oct.


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


[~] keep.price_history_missing — FOUND 16 Oct, DESIGN GAP.
    DEPRIORITISED 18 Oct: Keep is personal and off the critical
    path. This is real work and worth doing, but it does not block
    January, and the interesting-ness of the bug is not a reason to
    work on it before the consultancy. Do it when there is spare
    time, not before.

    This is the systemic finding; the four entries below are its
    symptoms.

    The app records the current price of each asset
    (Asset.currentPrice) and the current portfolio value
    (PortfolioSnapshot). It does not record the history of either.
    PricePoint exists in the schema and has 0 rows. Consequence: the
    evolution engine cannot compare "what I did" to "what could have
    happened" — it has no price series to evaluate rules against.
    EthicalScoreHistory has 242 rows and Trade has 73, but the prices
    between the two are not stored. A system that only knows "now"
    cannot learn.

    Three-layer fix:
      L1. app/api/prices/route.ts appends one PricePoint per asset
          per day. Not a rewrite of currentPrice — an append. Ten
          lines. Small enough to apply this week.
      L2. Backfill PricePoint from Yahoo daily history for the gap
          (10 Sept → 16 Oct, and back as far as wanted). Yahoo's
          chart endpoint returns daily bars for any range; fetch
          once, insert many. Real work, next session.
      L3. Derive PortfolioSnapshot from PricePoint × holdings per
          day. Snapshot becomes computable rather than primary.
          Then a backfilled snapshot history is correct rather than
          approximated.

    This is the foundation for gov.evolve_loop_feedback. The
    evolution engine needs a price ledger to evolve against.


[~] keep.price_cron_missing — FOUND 16 Oct. Bosly Keep has no
    heartbeat. The user crontab runs five jobs (sync-email every 10
    min, backup, monitor, two gov check tiers), none of them touch
    Keep. app/api/prices/route.ts works — it fetches Yahoo, updates
    every asset, and writes a PortfolioSnapshot — but nothing calls
    it. Result: Asset.priceUpdatedAt and PortfolioSnapshot were both
    frozen at 2026-09-10 14:07, five weeks ago. Fix: a weekday
    22:00 UTC cron line POSTing to the endpoint. Installed 16 Oct.
    Verify tomorrow that Asset.priceUpdatedAt has advanced.


[~] keep.snapshot_backfill — FOUND 16 Oct. PortfolioSnapshot has a
    five-week gap (10 Sept → 16 Oct) with no rows. Snapshots are
    point-in-time; the gap cannot be filled with today's prices
    without lying. Backfill requires fetching daily Yahoo closes
    for each held asset across the gap and recomputing the
    portfolio value per day. Real feature, not tonight's work.


[~] keep.pricepoint_empty — FOUND 16 Oct. The PricePoint table
    exists (schema is present) but has 0 rows. app/api/prices/route.ts
    updates Asset.currentPrice but never inserts PricePoint. There
    is no per-asset price history — only the latest value. Cannot
    answer "what was X worth on date Y". Same class as the missing
    snapshots: a table designed to record history, and it isn't.


[~] keep.udmy_404 — FOUND 16 Oct. Yahoo returns HTTP 404 for UDMY
    (Udemy). One of 83 assets has no price. Every portfolio total
    either misvalues the position or omits it. Decide: delisted?
    Acquired? Remove from the screened universe, or hold and mark
    it manually.


[~] keep.trade_idempotency — FOUND 16 Oct. /api/trades has no
    deduplication, and the "Execute Buy" button re-enables before the
    new signals land: fetchSignals() is not awaited and
    setExecuting(null) runs immediately after. A double-click, a
    network retry, or a fast user creates duplicate trades. Evidence:
    four identical £300 TRIG buys on 2026-09-10, one second apart,
    strategy "Bosly Keep Engine", manuallyExecuted: true, from the
    signals page. Cash £1,813.16 → £613.16 in four steps. The
    maxTradesPerDay guard lives in generateSignals() (the read path)
    and is never consulted on write. Paper trading only — no real
    money — but the same bug would misfire in production.

    Fix (two parts):
    (a) app/signals/page.tsx — await fetchSignals() before clearing
        executing; add an in-flight useRef<Set<string>> guard so a
        second click on the same ticker is a no-op.
    (b) app/api/trades/route.ts — reject a duplicate trade (same
        asset, type, quantity, price) within 10 seconds with 409.
        This is the real fix; (a) only prevents honest mistakes.

    Related: the £953.31 "loss" is the P/L figure. Deposited
    £20,000, portfolio worth £19,046.69, difference = £953.31.
    Unrealised, on paper, expected. Not a bug.


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


[ ] [LIVE] ops.ico_registration — Register with the ICO.
    SCHEDULED: end of December, just before the day-0 emails go
    out. Not before — the fee is annual and there's no reason to
    start paying it months before there are clients to process
    data for. When done, update /privacy and the FAQ to state it.
    Until then, both documents must not claim registration.


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

