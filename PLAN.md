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

[ ] accord.butler_knows_today — FOUND 26 Oct. Asked "27-29 October"
    the butler chose 2025 and returned a true zero for the wrong year:
    nothing in the prompt says today's date.

    The prompt is a file: /home/bosly_accord/bosly-gov/tools_prompt.txt,
    read fresh on every call by routers/tool_loop.py _read_prompt
    (PROMPT_FILE, line 71). It begins "You are Bosly Executive, the
    founder's chief of staff." and had no date anywhere.

    STEP 1 DONE 26 Oct. The line "Today is Monday 26 October 2026
    (Europe/London)." now sits beneath the opening line. Applied by the
    founder; verified by the butler, which read the file fresh and
    quoted the line.

    STEP 2 OPEN. A static date goes stale. Change _read_prompt to inject
    a fresh datetime.now(ZoneInfo("Europe/London")) each call, and drop
    the static line or make it a placeholder. Code change; needs a Gov
    restart, verified against the running process.

    Verify: ask the butler "what's on 27-29 October?" and it must resolve
    to 2026, not 2025.

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

[ ] gov.prompt_is_a_description — FOUND 27 Oct. THE RATCHET. The
    prompt has grown by one script per failure: the plan-item rule, the
    draft rule, and a full "working the week's list" procedure three
    routes deep (tools_prompt.txt 120-260). Each script is true. Together
    they are sediment, and sediment does not scale: every new behaviour
    adds another rule the founder has to read. The fix is structure, not
    deletion. Four parts: (1) THE WORLD — what exists and what it is for
    (plan, things the pile, memory, transcript, the three repos). (2) THE
    TOOLS — one line each, no procedure. (3) THE STANDING RULES — the few
    that are genuinely constraints and stay: a failure is not a zero; a
    plan item is work; never send, post, delete, or spend without the
    founder's yes; the Custodian verifies, the Executive does not; do not
    fabricate a tool result. These are already in the prompt (lines
    240-260) and they are good. (4) THE SKILLS — procedures move to files
    the butler reads when the job starts, not text it carries every turn.
    "Working the week's list" becomes a skill. THE TEST: a new capability
    means DESCRIBING a store or a tool, not adding a rule. Until this is
    done, every session makes the pile heavier; this item is the ratchet
    that stops it. Do not rewrite the prompt in this item — the rewrite is
    its own session, against this shape.

[ ] gov.one_pile — FOUND 27 Oct. THE CONSOLIDATION. There are three
    piles: PLAN.md (decided work), things.db (ideas, clients, leads,
    drafts), and the governor's unknown-intents.jsonl (questions the
    butler could not answer — 39 total, 32 in the last 7 days, read by
    nobody). A fourth, tasks-store.json, is dead ("cooking" x3, last
    touched September). One pile is manageable; three is how a backlog
    becomes another thing you do not read. THE FOLD: lib/intent_classify.py
    (the writer, line 28) calls save_thing(kind="unanswered", ...) instead
    of appending to the jsonl; the 39 existing rows backfill once;
    evolve_feedback.py keeps reading the jsonl until the fold is proven,
    then reads things. tasks-store.json is removed. No new door: the app
    and the UI both reach the butler, and the butler has save_thing and
    find_things. What is missing is not a route — it is the DESCRIPTION of
    the pile in the prompt (see gov.prompt_is_a_description) and the fold
    itself. THE RISK: the governor currently writes a jsonl, not a SQLite
    file; a silent write failure is today's family of bugs. The fold is
    not done until one real unanswered question lands as a thing and a
    check watches kind="unanswered".

[x] gov.plan_as_boundary — DONE 29 Oct. THE NEXT BUILD, and the thing
    that makes the butler useful without being steered. The plan is the
    boundary: the butler reads PLAN.md, finds the open item, and
    PROPOSES it — it does not act until the founder says go. The
    principle is already in the plan ("the Executive proposes and
    acts") but there is no item that wires it: today the founder must
    name a plan item in the message ("accord.butler_knows_today, step
    1") or nothing happens. THE SHAPE: when the founder asks "what's
    next" or "what should I do", read PLAN.md with read_file, find the
    highest open item (respecting START HERE / next_session_first and
    the dependency notes in the items), and propose it in one
    paragraph: what it is, what step, what it would touch, and the
    question "shall I do it?". Wait for the yes. Proven once: ask
    "what's next on the plan?" and it names gov.next_session_first (or
    the loop item) without being told. DO NOT AUTO-RUN: propose, never
    start.

    PROVEN 29 Oct. First test at 13:51, after the item landed:
    the butler listed 15 in-progress items instead of proposing —
    the prompt said 'do what its STEP says', not 'pick one and
    propose'. Added a paragraph: when asked what's next, read
    PLAN.md, find the highest open item, propose it, ask 'shall I
    do it?'. Second test, 13:56: it proposed butler_knows_today
    step 2, correctly refusing to guess at the rest of the file.
    Third test, 14:09: it wrote NEXT.md — 19 open items, the
    closed ones named as omitted, the 40KB limit and the
    truncated last entry flagged, and 'want me to read further?'
    asked. Proposed, approved, built, proved. The dependency it
    found (the plan is too big to read) is gov.the_plan_is_too_big.

[ ] gov.the_loop_is_not_a_count — FOUND 27 Oct. Asked "did I fix the
    invoice PDF cut-off?", the founder butler hit the tool-loop ceiling
    at MAX_ITERATIONS=5. Raised to 20: it ran 20 and stopped again. So
    5 was too few for investigation and 20 was still a loop, not
    thoroughness. A raw iteration ceiling is the wrong shape. THE FIX,
    once the evidence is in: (1) show tool_events - the founder route
    returns data.tool_events and the drawer discards it, so the
    diagnostic is captured and thrown away; (2) then guard the pattern -
    the same tool with the same arguments twice - not a count. Do not
    raise the number again without evidence. 20 iterations on one
    question is also the token drain.

[ ] accord.founder_door_does_not_log — FOUND 27 Oct. THE INVERTED
    PILE. ChatDrawer.tsx routes by user: the founder's message goes to
    /api/executive/founder -> Gov /api/chat -> the butler, and the comment
    is explicit that it never touches /api/chat or the deterministic
    engine. A client's message goes to /api/chat (workflows) and then
    /api/executive/proxy. logUnknownIntent is wired into /api/chat, so
    the pile records the CLIENTS' misses and not the FOUNDER'S. The
    questions that should shape the next build are the ones not being
    logged. THE FIX is not string-matching the butler's prose. It is a
    cannot_help signal from Gov's /api/chat (one field in the response,
    set by the tool loop when it has nothing), which the founder route
    then logs. One field, one route, one writer. Whether the app is
    touched now or after the UI work is the founder's call, not a
    premise from a misread: the founder door IS the same butler as the
    UI, so "app frozen" was never a fact, only an inference.

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

[x] accord.delete_route_toggle_cleanup — DONE 21 Oct. The
    vault/managed split added ProductToggle as a child of User. The
    delete route enumerates child models manually, and the
    delete-route-coverage invariant caught the drift immediately:
    deleting a user would have left their toggle rows behind. Added
    prisma.productToggle.deleteMany to the transaction. test-fast.ts:
    11 passed, 0 failed.

    This is the invariant doing exactly what the manual-list pattern
    predicted: a list that drifts silently when the schema grows,
    now caught by a check on the first run after the change.

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

[x] gov.silence_guard — DONE 29 Oct. The loop speaks when it ends
    without text.

    The loop returned nothing when the model ended without a text block
    — a task could vanish without a word. The guard tracks whether any
    text was said, and yields a fallback before done: "I ran the tools
    but produced no answer. The tool calls are above." PROVEN with a bad
    anchor: the patch aborted (0 times, needs 1), the butler said so,
    and offered to read the file first. Not silence — the honest report.

[x] accord.calendar_period — DONE 29 Oct. The calendar can be read
    for a period, not just the five-year window.

    TWO HALVES, both silent: the calendar route hardcoded a window, so
    a period could not narrow it; and read_accord's signature and
    schema declared `period` while the body ignored it. The route now
    reads ?from= and ?to=; the tool parses the period (today, tomorrow,
    this week, next week, this month, a date, a range) and appends it.
    Both doors get it — the patch is in the tool, not a room.

    PROVEN: 'what is on my calendar next week?' returned 2–8 Nov, with
    the encrypted-titles caveat stated. A declaration without a wiring
    is a stub.

[x] ops.cron_environment — DONE 24 Oct. The fast-tier cron ran at
    05:00 with no environment: no DATABASE_URL, no HOME, no nvm. Three
    checks failed — keep.invariants (no Node), vault_plaintext_calendar
    and hasProduct_vault_false (no DB). The email was a false alarm;
    the 09:18 live run was 29/29.

    THE FIX: PATH and DATABASE_URL at the top of the crontab, the fast
    tier moved to 07:00 (after the DB and app are up), and run under
    `bash -lc` so a login shell loads HOME, nvm, and Node. Verified:
    `bash -lc` gives 29/29 — the cron's environment now matches the
    shell's. An alarm that only fires for real problems.

[x] gov.shared_transcript — BUILT 25 Oct. One butler, two rooms,
    one log.

    Both rooms write /api/transcript (Gov): the UI butler from app.js,
    the app from ChatDrawer via Accord's own route, which forwards and
    is gated by requireAccord. Each line is {ts, room, role, text}; the
    ts fixes the UI's "Invalid Date" and the room records where it was
    said. read_chat (b90abf5) reads the log — both rooms, last N,
    optionally filtered — so "what did we say about X" is a read, not a
    guess. Proven: the Café Corner question answered from the lead store
    and the transcript.

    ALSO BUILT 25 Oct: write_file and patch_file (f341db6) — the butler
    patches code, anchored, aborting on a bad anchor, backed up, guarded
    by the same resolver as read_file. Proven: it patched routers/tools.py,
    ran the checks, and reported.

    STILL OPEN: the loop returns an empty answer when the model ends
    without text (the empty-answer guard); read_accord's period; the
    finance route (encrypted client-side, the honest boundary).

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

[x] accord.typecheck_clean — DONE 16 Oct, superseded. The gap this
    entry names — a check that reports which excluded directories
    contain live imports — is filled by gov.tsconfig_excludes, which
    is registered in the fast tier and passing. The remaining
    excludes were audited as part of that work.

    Original entry follows.
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

[x] gov.tsconfig_excludes — DONE. Registered in the fast tier and
    passing. checks/tsconfig_excludes.py lists every excluded
    tsconfig directory containing source, except a deliberate-list.
    The three flagged directories (app/api/spaces/**,
    app/api/connect/google/**, app/api/inbox/webhooks/sms/**) are
    unfixed — that is work the check found, tracked separately, not
    work on the check.

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

[x] gov.plan_hygiene — RESOLVED 7 Oct, no check built. A check was
    built and tuned three times (checks/plan_hygiene.py, since
    removed). Each rule tried to distinguish drift from legitimate
    text using surface patterns, and each pass removed some false
    positives only to reveal more: "TODO" in a check that detects
    TODOs; "two routes had duplicate validators" as past-tense
    description; "ACCEPTANCE" as a shared section header. After
    three passes, 6 findings remained, none of them drift. The check
    also missed the case that motivated this entry —
    accord.usage_capture_wiring kept pre-work text below "Original
    entry follows", which any quoted-history filter exempts. The
    five drifts on 5 Oct were found by a person reading the plan.
    That is the practice: read the entry before acting on it. The
    drift problem is real but not checkable by pattern.

    UPDATE 12 Oct: the plan grew about 30% in five days, 3909 lines
    to 5051. The consultancy cluster is now scattered — ops.jarvis at
    315, ops.voice_infrastructure at 361, accord.business_setups at
    425, ops.consultancy at 703, ops.consultancy_design at 1769,
    ops.consultancy_sales_sequence at 1791, ops.consultancy_contract_terms
    at 1959. Related entries should sit together. Not urgent, because
    the orientation finds them by marker, but a fresh reader looking
    for "everything about the consultancy" has to grep for it, and
    the point of the plan is that they should not have to.

    And a method lesson: an insert run twice duplicates. Two entries
    were duplicated this weekend — the claim-class cross-reference,
    and ops.consultancy_sales_sequence. A replace is idempotent; an
    insert is not. The check after any insert is: grep the plan for
    the entry's own name and confirm it appears once. Worth adding to
    the Working Agreement under Patches.

    Original entry follows.
    [ ] [DECISION] gov.plan_hygiene — The plan accumulates drifts. Five
    found and fixed on 5 Oct, all small, none caught by a check:

      1. Four entries written with the wrong date (6 Oct for 5 Oct).
      2. A done entry (accord.usage_capture_wiring) kept its pre-work
         description below the DONE summary — a fragment about
         /api/usage/ping and duplicate hooks, all resolved 21 Sept.
         It made the entry read as half-open, and an outside reader
         flagged it as an error in a neighbouring item.
      3. The same entry's tail stranded, attributed to the wrong
         entry in a truncated read.
      4. accord.action_feedback_audit had a duplicated DONE line, and
         two summaries that disagreed.
      5. The same entry said "eight settings pages" and named seven,
         missing DuressSettings. Eight files fetch; one is done.

    The shape: the plan is appended to constantly and cleaned rarely.
    Ticking an item leaves its old text behind. Counts drift from
    reality. This is the "hidden, not removed" pattern applied to the
    plan itself. gov.plan_tracks_known_gaps checks that admissions are
    tracked — nothing checks that a done item's stale text is removed,
    or that an entry's count matches the names it lists.

    A check could verify: a [x] entry contains no "TODO", "not yet",
    or pre-work imperative; a stated count matches the list below it;
    no two entries contain the same block of text. Report-only first.

    Raised 5 Oct.

[x] ops.founding_member_offer — DONE 6 Oct. The post went out; the
    reel is live; the offer is running. FOUNDER40 has 20 of 21
    redemptions remaining — the one used was the end-to-end test on
    2 Oct. The detail below is the record of how the offer was built
    and stays as history.

    If the 20 fills and the offer should close, that is a new item, not
    this one. If a second test ever runs, the post's "20 spots" claim
    becomes false — gov.claim_invariants territory.

    Original entry follows.
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

[x] accord.usage_capture_wiring — DONE 21 Sept. Wired useUsageTracking into all nine workspace pills (active, finance, health, calendar, contacts, inbox, invoice-analytics, social, data-health). Removed the duplicate hook at components/useUsageTracking.ts. UsageEvent now captures product usage. Unblocks gov.evolve_loop. (The original task text was left below the DONE summary until 5 Oct, which made the entry read as half-open.)

[x] accord.db_in_git — DONE 19 Oct. A database backup,
    prisma/dev.db.pre-onboarding-reset.20260308-095110, had been
    tracked in git since March (commit c9ff4ba).

    WHAT WAS IN IT, inspected 19 Oct: one user
    (jr-arnott@outlook.com, name "bosly", a pbkdf2 password hash —
    not a plaintext password), five contacts (Test Contact, Kevin,
    Jamie Arnott, Sarah, Tom — the founder's own contacts and test
    entries), eight test tasks ("AUTH TEST — created via PA",
    "Real-use test task", "Work"), thirty-four test cards (mostly
    "TEST CARD 3" duplicates, one hairdressing lead), six activity-
    log rows. Every other table empty — no inbox, no messages, no
    conversations, no social accounts, no channel accounts.

    The only real third-party detail was a business email of the
    founder's own (contact@emporiumon.co.uk). No client data, no
    third party's data, no financial records.

    DECIDED: left in git history, not rewritten. A history rewrite
    is a destructive operation with a real chance of error, and the
    thing protected is the founder's own dead test data from March.
    Revisit if the repo ever becomes public, or if the password
    hash could ever be a live credential.

    FIXED: prisma/dev.db (the live database) was untracked but not
    ignored, because the .gitignore rule named bosly.db, not the
    prisma path the app writes to. .gitignore now covers
    prisma/dev.db, prisma/*.db, prisma/*.pre-onboarding-reset*,
    prisma/*.backup*. The March backup is untracked (git rm
    --cached). The file remains on disk for inspection. Commit
    0e525e3.

    The lesson: a database file is live data, not source. It must
    be ignored from the first day, at the path the app actually
    uses, not at the path someone guessed.

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

[x] ops.backups — DONE 20 Oct. Four backup holes found, all closed.

    WHAT WAS FOUND:
      - The Postgres dump of the Accord database had been EMPTY for
        at least five days. Every bosly-db-*.gz was 20 bytes — a
        gzipped nothing. Cause: sudo -u postgres needs a password
        cron cannot give, and '2>/dev/null || true' turned the
        failure into a success.
      - The data tarball was 370 MB per day, 98% of it node_modules
        (1.1 GB of npm packages), backed up seven times.
      - The governor state (things.db, memory, lead CSVs, capsules)
        had no backup at all.
      - The state backup's cron line was misspelled three times
        (backup_stat.py), each time silently.

    WHAT WAS FIXED:
      - Postgres: a bosly_accord role with peer auth and grants on
        the bosly database, default privileges for future tables.
        pg_dump -d bosly now works without sudo, under cron. The
        dump is 126 KB. No '|| true'; a dump under 1 KB exits
        non-zero.
      - The data tarball excludes node_modules, _snapshots, test
        output, and logs: 370 MB -> 8.1 MB.
      - scripts/backup_state.py discovers the governor state by
        rule, not by list — a new memory.json, chat.json, .db, or
        capsule is covered without editing the script. Every file
        checked non-empty; every .db gets PRAGMA quick_check. 14-case
        self-test. Keeps 14 days.
      - Both scripts live in the repo; the cron points at them.
      - Backup dir: 4.1 GB -> 74 MB.

    THE LESSON: '2>/dev/null || true' is how a backup dies silently.
    A backup that has never been restored is a hope, not a backup.
    Every backup step must fail loudly, and every backup must be
    checked for size and integrity — not just for having run.

    STILL TO DO:
      - Test a restore. The dump opens, the things.db opens, but
        nothing has been restored into a scratch database. That is
        the next session's first job.

[x] ops.backups — DONE 20 Oct. Four backup holes found, all closed.

    WHAT WAS FOUND:
      - The Postgres dump of the Accord database had been EMPTY for
        at least five days. Every bosly-db-*.gz was 20 bytes — a
        gzipped nothing. Cause: sudo -u postgres needs a password
        cron cannot give, and '2>/dev/null || true' turned the
        failure into a success.
      - The data tarball was 370 MB per day, 98% of it node_modules
        (1.1 GB of npm packages), backed up seven times.
      - The governor state (things.db, memory, lead CSVs, capsules)
        had no backup at all.
      - The state backup's cron line was misspelled three times
        (backup_stat.py), each time silently.

    WHAT WAS FIXED:
      - Postgres: a bosly_accord role with peer auth and grants on
        the bosly database, default privileges for future tables.
        pg_dump -d bosly works without sudo, under cron. The dump is
        126 KB. No '|| true'; a dump under 1 KB exits non-zero.
      - The data tarball excludes node_modules, _snapshots, test
        output, and logs: 370 MB -> 8.1 MB.
      - scripts/backup_state.py discovers the governor state by
        rule, not by list — a new memory.json, chat.json, .db, or
        capsule is covered without editing the script. Every file
        checked non-empty; every .db gets PRAGMA quick_check.
        14-case self-test. Keeps 14 days.
      - Both scripts live in the repo; the cron points at them.
      - Backup dir: 4.1 GB -> 74 MB.

    THE LESSON: '2>/dev/null || true' is how a backup dies silently.
    A backup that has never been restored is a hope, not a backup.
    Every backup step must fail loudly, and every backup must be
    checked for size and integrity — not just for having run.

    STILL TO DO:
      - Test a restore. The dump opens and the things.db opens, but
        nothing has been restored into a scratch database. That is
        the next session's first job — the only proof a backup is
        real.

[x] ops.scout_routes — DONE 20 Oct. The Executive works each
    candidate by its contact_route.

    THE THREE ROUTES, decided by the audit:
      email         the site has an address -> draft_email, send to
                    the founder's phone, approve, send
      contact_page  the site has a contact form but no email -> a
                    note with the URL and what to say on the form
      call          no website, or no other contact -> a call brief

    THE TOOL: read_leads(only_call_list, limit) returns the ranked
    rows as structured data. Fixed path; the model cannot read the
    log or the state.

    THE PROMPT: tools_prompt.txt now says, per route, what to
    produce. It also says: cite Companies House details ONLY when
    match_confidence is medium or high. A low-confidence match gets
    flagged, not cited.

    VERIFIED: the Executive read 10 call-list rows, found all were
    route=call (OSM rarely carries a website), checked each CH
    match, cited only Ashleys Hair Salon (high confidence), and kept
    the rest to OSM facts.

    WHAT THE DATA SAYS: the no-website list is the majority, and it
    is the call list. The email and contact-page routes are thin,
    because OSM rarely has a website tag. Google Places (when keyed)
    returns a website for businesses that have one, which is the
    single biggest lever for more email routes.

[x] ops.scout_cron — DONE 20 Oct. The pipeline: sweep -> Companies
    House -> Google (when keyed) -> rank.

    WHAT WAS BUILT:
      scripts/lead_scout.py     county sweep from lead-scout.config.json.
        50 counties in rotation, state file remembers where it is,
        wraps after a year. Every shop and craft with a phone and
        no website, capped at 250, split by tag family so Overpass
        is not overloaded.
      scripts/ch_enrich.py      Companies House: status, incorporation
        date, age, SIC, directors, with a match confidence.
      scripts/google_enrich.py  Google Places Text Search: rating,
        review count, status. Built and inert until
        GOOGLE_PLACES_API_KEY exists. Skips cleanly.
      scripts/lead_rank.py      weights from config. CH signals count
        only at medium/high confidence, so a guess does not outrank
        a verified company. Top 15, top 10 call-listed.
      scripts/lead_pipeline.py  one entry point, the thing the cron
        calls.

    VERIFIED on Northumberland, 20 Oct: 250 rows swept, 250 CH
    lookups, ranked to 15. The top 5 all have verified limited
    companies with real ages and directors. The low-confidence
    name matches fell out of the top.

    STILL TO DO:
      - Install the cron: Saturday 23:00 (sweep), Sunday 23:00
        (--retry), Monday 06:00 (rank).
      - Point the Executive's pickup at lead-scout-ranked.csv, not
        lead-scout.csv, so it briefs on the 15, not the 250.
      - Google key: register, paste, no code change.
      - Employee count (Phase 3 step 3): Companies House accounts
        files. Fiddly; approximate from SIC or skip in v1.

[x] gov.tool_results_not_persisted — DONE 20 Oct. The Executive
    lost continuity between turns because only the message was
    saved. Three fixes: tool_call events now carry the result's
    thing_id; the saved tool_events and the context renderer show
    it ('[used: draft_email (thing-...)]'); and the context header
    puts [Recent chat] first, with the project background smaller.
    Plus: the prompt says check for an existing active draft before
    drafting.

    Verified: turn 1 reused the existing draft instead of making a
    second; turn 2 found the draft by name, checked the .example
    address, refused it, and asked for a real one. The model no
    longer says 'the recent exchange was about what Bosly Gov is
    for'.

    Two consequences found today:
      - 'send it' failed because the draft was not in history. Fixed
        by saving drafts as things (kind 'draft') and letting
        send_email take a draft_thing_id. That is the artefact
        stored; this entry is about the conversation.
      - 'yes pls send it' asked again which of two drafts, because
        the model could not tell whether 'it' referred to the draft
        it had just shown. It was being correct — it just could not
        see the confirmation it had already given.

    Same class as gov.project_chat_context_ignored: the context is
    there, but not the right context. The fix: save the tool calls
    and results alongside the messages in chat.json, so a turn can
    see what the previous turn actually did. Then the model can
    answer 'the draft I just showed you' instead of asking again.

    Not blocking the workflow — it finds, drafts, delivers, asks,
    and sends when told. It just makes the conversation smoother.

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

[x] ops.archive_ai_era — DONE 3 Oct. The AI chat was replaced by the
    workflow engine on 24 Sept, but its routes and components were
    never removed. Archived to legacy/api-ai-20261003/: five routes
    (check-leads, next-action, orchestrator, reply, realtime), the
    lib/bosly-brain.ts, and three dead components (ChatAssistant,
    ChatWidget, BoslyChatWidget). All unreachable — the greps found
    no callers. 'realtime' was not AI at all: a local keyword search
    over chat-memory.txt, and a duplicate of bosly-brain.ts.
    Commits 5347025, f3ed729. The live chat is ChatDrawer.

[x] accord.executive_proxy — DONE 22 Oct. The model call, out of
    /api/chat, into the browser's reach. Gated by the toggle. Proven
    end to end in the running build.

    WHAT EXISTS:
      - app/api/executive/proxy/route.ts — a relay, not a composer.
        requireAccord (paid tier), then hasProduct(uid, "executive")
        (the toggle). Body is { messages } built by the browser. It
        calls Claude via fetch, copying the social routes' pattern
        (CLAUDE_API_KEY / CLAUDE_MODEL, anthropic-version 2023-06-01).
      - components/chat/ChatDrawer.tsx — when /api/chat returns
        unknownIntent, the chat asks the proxy. A 403 (not managed,
        or toggle off) falls through to the deterministic reply. The
        client does not check the toggle; the server is the authority.

    THE STRUCTURAL GUARANTEE: the proxy has no path to the database.
    No prisma import, no model query. Data-minimisation happens in the
    browser (the prompt) and in the client-side tools (step 3). The
    promise "the LLM never sees a user's sensitive business data" is
    enforced by the route having nowhere to read from.
    Watched by gov.executive_proxy_no_db (fast tier, PASS).

    VERIFIED: tsc clean; route in .next/standalone build; live on
    3100 (303 anonymous = live, not 404); health 200.

    VERIFIED END TO END 22 Oct: three unhandled questions asked in the
    browser (cold-email opener, sole trader vs limited company, boiler-
    servicing social posts). All three returned Claude replies, not the
    canned cannot_help. The branch fired, the proxy accepted (managed
    + Executive on), the model answered. The guard was exercised by the
    same test: the proxy accepted a managed+Executive-on user and
    would have returned 403 for a vault user or a toggle-off user.

    THE SCOPE DECISION (21 Oct): managed-only. The vault backup is
    PARKED — a policy question (loosening zero-access, keeping
    finance and health encrypted) that the proxy build does not
    resolve. A vault user gets 403 from hasProduct and the
    deterministic reply stands.

    CHECKS BUILT 22 Oct (five, all registered in the fast tier):
      gov.executive_proxy_no_db — the proxy has no DB path (21 Oct)
      gov.executive_proxy_gated — requireAccord AND hasProduct,
        both before the model call
      gov.executive_proxy_managed_only — hasProduct is called with
        the literal "executive", so the guard cannot be re-pointed
      gov.hasProduct_vault_false — DB-backed: no vault user has an
        enabled ProductToggle. lib/managed.ts's docstring as a rule.
      gov.executive_proxy_live — the deploy trap, live: 303/401/403
        pass; 404 fails (not deployed); 000 fails (app down)

    OPERATIONAL: the fast tier now requires DATABASE_URL and the app
    up on 3100, in addition to the filesystem and Node. The cron that
    runs run_checks.py --tier fast must carry both. If the app is
    down, the tier fails on executive_proxy_live — correct, but the
    cron log will show it.

[~] accord.learned_answer_cache — FOUND 22 Oct. THE LADDER BUILT
    22-23 Oct: A (per-user cache), B (the extractor), C (the shared
    question shape), D (the template rule, the fill form, the hard
    rule). The feed is named (gov.evolve_loop_feed). THE GOAL:
    Bosly learns. The LLM is called less as Bosly accumulates memory;
    the memory becomes the seed of Bosly's own model, the local model
    the product design already names as the direction. Efficient,
    sustainable, and it respects everyone's sensitive information: Gov
    holds templates, the browser holds the data.

    RUNG A BUILT 22 Oct (per-user cache, non-sensitive only):
      - app/api/executive/cache/route.ts (02c56fe) — per-user store in
        Gov memory (answer-cache/<uid>.json). GET ?q= returns a hit;
        POST {question, answer} refuses if the question looks like it
        carries a value (digit, currency/percent token, two capitalised
        words, health-value term + digit). Gated twice, like the proxy.
      - components/chat/ChatDrawer.tsx (26d4aa6) — on unknownIntent the
        chat asks the cache first. A hit answers without calling the
        LLM; a miss calls the proxy and stores the answer (fire-and-
        forget, so a failed store never breaks the reply).
      - checks/answer_cache_no_sensitive.py — the data check: every
        answer-cache/*.json is scanned, and a stored question with a
        value is a breach. Registered in the fast tier.

    PROVEN END TO END 22 Oct: the same question asked twice — the
      second answered from the cache, GET hit, no POST to the proxy.
      The cache file holds the question and answer, no digits. This is
      the answer to "Bosly remembers what it was asked, so the LLM is
      not called twice" — true in the running build.

    RUNG B BUILT 22 Oct (the extractor, shape with slots):
      - app/api/executive/cache/route.ts (ffd96eb) — extractShape()
        replaces value-looking tokens with slots: a date-like token ->
        [date], a currency amount -> [amount], a digit run -> [number],
        a capitalised pair -> [name]. Every entry gains a shape field.
      - checks/shape_contains_no_sensitive.py (30feec9, registered
        36f003f) — the data check: no stored shape carries a value.

    PROVEN 22 Oct: 'How do I write a follow-up email after a Tuesday
      meeting?' -> shape 'How do I write a follow-up email after a
      [date] meeting?'. The value is slotted; the category words stay.
      A value-free question's shape is itself — correct, not a defect.

    CALIBRATION FINDING: the first stored entry (a value-free question)
      failed the check's original 'at least one slot' rule. The rule was
      wrong, not the shape: a value-free question has nothing to slot,
      and the rule is 'no value in the shape'. The fix was the rule.
      Two patcher aborts on the way (the type is an interface not a
      type alias; a line-number sed deleted the break) — both the check
      and the edit refusing to guess.

    THE HOLE, NAMED: the check and the extractor use the SAME SENSITIVE
      rules, so a value both miss would pass. The hardening before C is
      hasSlots: boolean on each entry — the extractor records whether it
      slotted, and the check verifies the claim. That is the independent
      angle C needs before shapes are shared.

    HARDENING BUILT 22 Oct (hasSlots):
      - app/api/executive/cache/route.ts (ba06285) — extractShape()
        returns { shape, hasSlots }; hasSlots is true when the shape
        differs from the question. Every entry records it.
      - checks/shape_contains_no_sensitive.py (f1172d6) — verifies the
        claim: hasSlots true -> the shape has a [slot]; hasSlots false
        -> the shape equals the question. A lying/no-op extractor
        fails. Calibrated by flipping the flag: the check fails with
        'hasSlots false but the shape differs from the question', then
        passes on the restore.

    WHAT IT CLOSES: the lying-extractor hole — an extractor that claims
      to have slotted and didn't, or claims not to and did. The check
      reads the claim and the shape and fails on disagreement.

    WHAT IT DOES NOT CLOSE: a value that neither the extractor's rules
      nor the check's rules recognise (a lowercase client name, say).
      hasSlots makes it REVIEWABLE (a human sees hasSlots: false on a
      question that looks like it had a value) but the automated proof
      does not cover it. That is the rules widening, and C waits on it.

    WIDENING ATTEMPTED 22 Oct (fd7e1de) — measured, partially reverted.
      CATCHES: relative dates ('next Tuesday' -> [date]), a capitalised
        word after a preposition ('to Acme' -> [name]), more currency
        forms ('450 GBP' -> [amount]), slash dates, the Nth, Qn, end of
        month, Month Nth.
      MISSES: a lowercase client name ('acme plumbing'). Demonstrated
        in the store: shape = the question, hasSlots false, and the
        check PASSES it because the check shares the rules.
      CORRUPTED, THEN FIXED: the possessive rule turned 'What's' into
        '[name]'s, mangling ordinary contractions while still missing
        the lowercase name. The check passed the corrupted shape too.
        Removed. A false positive that mangles the shape is worse than
        a false negative that leaves it intact.

    THE VERDICT: patterns REDUCE the hole; they cannot close it, and
      they can break the shape. C's precondition is not more patterns —
      it is a different kind of check: a VOCABULARY check (any token
      that is not a safe word is flagged, regardless of pattern) plus
      HUMAN REVIEW for the residue. The lowercase-name case is the
      demonstrated reason C waits.

    C'S PRECONDITION MET 22 Oct (d909d88) — the vocabulary check.
      The residue ('acme', a lowercase client name) passed the pattern
      check because the pattern check and the extractor share rules.
      gov.vocabulary_covers_shapes is the independent angle: it does
      not look for values, it asks whether EVERY token in a shape is a
      known-safe word or a slot. It caught 'acme' by name; the human
      removed the shape; the store is clean.

      The vocabulary is a whitelist at
      answer-cache/vocabulary.txt, one word per line, grown as words
      are proven safe. A safe word not on it is a false positive
      (flag, review, add); a dangerous word on it is a false negative.
      That is the honest ceiling of a whitelist, and it is why HUMAN
      REVIEW is the last layer before C shares a shape.

      Two tokeniser fixes on the way: a bare 's is not a word, and a
      slot may carry a possessive ([date]'s) — the SLOT regex owns it.
      The fix that makes a check right is the one that matches the
      structure.

    C IS UNBLOCKED: every stored shape is now proven token-safe or
      human-reviewed. C shares a shape with a generic answer; D adds
      the client-side fill and the hard rule (the filled question is
      never sent to Gov).

    RUNG C BUILT 22 Oct (935fa6d, 1f44e73) — share the QUESTION shape.
      - app/api/executive/cache/route.ts — a shared store
        (answer-cache/shared.json) holding {shape, hasSlots} only. A
        shape that passes looksSensitive is promoted; the shared file
        is deduplicated and capped. GET returns `shared` after a
        per-user miss.
      - components/chat/ChatDrawer.tsx — on a shared hit with no
        per-user hit, the client passes the shape to the proxy as a
        system hint and STILL CALLS IT. The answer is fresh, per
        client; the shape is the only thing shared.

    THE TRADE, AND WHY IT IS THE SAFEST VERSION: the first attempt
      shared answer shapes. The vocabulary check proved it could not
      carry them — an answer is a paragraph, and a paragraph needs a
      dictionary, and a dictionary weakens the whitelist ('Smith' is a
      common word and a client name). So the answer shape is NOT
      shared. The question is the small, token-safe, provable part; it
      is what crosses. C saves the SEARCH, not the call. D saves the
      call, when the client fills the slots.

    THE ANSWER SHAPE stays per-user (useful for D). The shared store is
      question-only. The check is questions-only.

    RUNG D FOUNDATION BUILT 22-23 Oct (a9c0703, 7318090, 1eb44a7).
      The answer shape is shared only when it is a TEMPLATE — a ratio,
      not a count: at least minSlots (2) and no more than maxFreeWords
      (20) free words. The rule lives in ONE file,
      answer-cache/template-rule.json, read by the route and the check,
      so the two cannot drift. A paragraph with two slots in it is
      prose, not a template; the prose answer shape that was shared (2
      slots, ~150 free words) was removed.

      THE HARD RULE, WATCHED: the filled question is never sent to Gov.
      gov.filled_question_never_sent reads the proxy call in
      ChatDrawer.tsx and fails if the body references a filled template
      (filled/assembled/.question interpolation). The proxy carries the
      shape (sharedHint), not a filled string.

      TWO GATES, ONE SOURCE: the structural gate is the ratio; the
      vocabulary check is the second gate. Both read template-rule.json
      and vocabulary.txt from the data mount — one source, two readers.

      NOT YET: the fill UI. The client does not yet show slots for the
      user to fill; it still calls the proxy with the shape as a hint.
      That is the end product, and it waits on this foundation — the
      shapes are proven templates, and the hard rule is already watched.






    FOUND BESIDE IT, FIXED 22 Oct: every chat memory save returned
      400 invalid_encrypted_payload — encrypt() returns version as a
      number, isEncryptedPayload checked a string. Silent (the client
      logs and continues), so nothing persisted until this was found.
      Fixed (version: 'string' -> 'number'), verified (POST ok: true,
      history persists across refresh). Watched by
      gov.encrypted_payload_shape: it reads the type's fields and the
      validator's typeof checks and fails on disagreement. The type is
      an interface, not a type alias; the scan accepts both. Calibrated
      by reverting the validator: the check fails, then passes.

    THE PROBLEM TODAY: the LLM is called every time an unhandled
    question is asked. The conversation is remembered (ChatDrawer
    saves encrypted chat memory) but the question is not learned.
    Asking the same thing twice calls Claude twice.

    THE LADDER. The end goal is D. Build in order; each rung is
    honest on its own and none forecloses the next.

    A (FIRST) — per-user cache. One JSON per user in Gov memory,
      non-sensitive only. Read before the proxy; a hit answers
      without calling the LLM; a miss calls the proxy and stores
      the answer. No sharing, no extractor. Proves the
      read-before-proxy path and the denylist. Smallest honest step.

    B — the extractor. Shape extraction: a template with sensitive
      slots removed, PROVEN to contain no sensitive terms (denylist
      + no client names, amounts, dates). The risk lives here; it
      gets its own check, like the vault-plaintext check. Do not
      share a shape until the extractor is proven.

    C — shared shapes, generic answers. B's shape offered to another
      client as a TEMPLATE ("here is how to write a cold email to a
      trade firm"), no fill. Safe, useful, no fill-in discipline
      required.

    D (THE GOAL) — shared shapes, client-side fill. The browser
      matches the shape, fills the sensitive slots with its own data,
      and produces the answer — and the filled question is NEVER sent
      to Gov. Gov holds templates; the browser holds the data. That
      is how Bosly learns across clients without seeing anyone's
      sensitive information.

    THE HARD RULE FOR D (in the plan and the code from the start):
      the filled question is never sent to Gov. The match is on the
      shape; the fill is client-side; the proxy is not called. If a
      slot is filled, the filled version goes nowhere but the screen.

    THE CAUTION: a cache that promotes the model's answers unchecked
      teaches Bosly its own mistakes. A caches per user, for that
      user. D's shapes go through B's extractor and its check. Do not
      skip the check when A's cache is used as the seed for B.

    THE SECOND SIGNAL: this item is the ANSWER side of the learning.
      The question side is gov.pattern_signal — Bosly reads what is
      asked and what the app contains to find what to build next.
      Together they are the seed of Bosly's own model.

    RELATED: gov.pattern_signal, gov.evolve_loop_feedback (the
      digest and recurrence), accord.executive_proxy (the call this
      reduces), ops.priority_to_january.

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

[x] ops.deploy_safe_ordering — DONE 22 Oct. The deploy script
    destroyed the backup before taking a new one, and a missing build
    artifact became a downed app (21 Oct). The fix is committed and
    verified both ways.

    deploy-safe.sh did rm -rf "$PREV_STANDALONE" BEFORE
    cp -r .next/standalone "$PREV_STANDALONE". When the source was
    absent, the backup was already gone and the rollback had nothing
    to restore. On 21 Oct a manual `npx next build` left .next/
    without .next/standalone/, deploy-safe.sh ran, removed the
    backup, failed the copy, called fail, restarted pm2 — and pm2
    errored the app (server.js missing). Health returned 000.

    RECOVERY: npm run build (regenerated .next/standalone/server.js),
    pm2 restart bosly. Health 200, proxy 303. No code changed; the
    outage was infrastructure.

    THE FIX (committed 22 Oct): verify .next/standalone exists BEFORE
    touching the backup. If absent, refuse cleanly — no rm, no build,
    no pm2 restart, the app stays up. If present, copy to a temp path,
    verify, then swap; the old backup is only removed after the new
    one is proven. The last good build is never the one being removed.

    VERIFIED BOTH WAYS: with .next/standalone absent, the script
    refuses and exits 1 with the app up; with it present, a full
    deploy completes, health 200, proxy 303.

    OPERATIONAL FACT: the app runs on 3100, pm2-managed, deployed by
    deploy-safe.sh. curl health on 3100 to check the app; curl a route
    on 3100 to check the route.

[~] ops.deploy_smoke_test_covers_routes — FOUND 22 Oct. The deploy
    smoke test is http://localhost:3100/api/health/smoke only. It does
    not curl the routes that changed, so a green deploy is green for
    health, not for the feature. Verification of a new route is a
    manual curl to 3100 — 303 anonymous is the live signal; 404 is the
    deploy trap. A smoke test that covers the changed routes is a
    separate, small item: either the script takes a list of routes to
    curl after deploy, or a per-route check is registered in the fast
    tier. Not urgent; named.

[x] gov.vault_plaintext_calendar — DONE 21 Oct. The vault promise
    ("the developer is blind") was enforced nowhere: no calendar route
    gates on managed mode, the list route selects the plaintext title
    unconditionally, and CalendarEvent stores plaintext and ciphertext
    side by side. Today there are no vault users, so nothing leaks —
    but the structure did not enforce the promise.

    The check (0e60ae0) queries the real database and fails if any
    user with managedById IS NULL has a CalendarEvent with a non-empty
    title. It passes vacuously today (zero vault rows), which is the
    correct state. Fast tier, high severity, REPORT_ONLY for
    calibration — flip when trusted.

    DEFERRED TO DECEMBER (named, now watched):
      - gate calendar/list so vault users get encryptedData only
      - gate the write path on isManaged before writing plaintext
      - backfill (no-op today: zero vault data)
      - the broad version across every model with encryptedData

    OPERATIONAL: the fast tier now requires DATABASE_URL in the
    environment that launches run_checks.py, including cron.

    Same shape as managedRevokedAt: a promise enforced nowhere is
    marketing; the invariant is the enforcement.

[x] gov.orphaned_routes — DONE 11 Oct. 75 orphaned routes found;
    zero remain. Registered in the fast tier (16 checks now), and
    REPORT_ONLY is false: a new route with no caller fails the
    pipeline.

    Worked down cluster by cluster — grep for callers, archive if
    none. Nine clusters archived: settings/connections, inbox,
    onboarding, cards, contacts, calendar providers, bosly
    workflows, billing, and the scattered remainder.

    Four causes, all a rebuild leaving the old API behind:
      - verb-in-path to REST (contacts/create to POST /api/contacts)
      - feature rebuilt (inbox actions, onboarding, briefings)
      - absorbed by the workflow engine (bosly/relationships,
        bosly/wellness-check)
      - dead as a consequence of cleanup (api/config, orphaned when
        its four callers were archived)

    One check bug fixed: lib/public-routes.ts counted as a caller,
    because the scan read lib/ for route paths and a policy entry
    looked like a call. It hid api/usage/migrate and two others.
    Excluded from the scan.

    One new list: DELIBERATE_NO_CALLER. Six finance routes — gifts,
    mtd, overview, pension, status, tax-position — have no caller
    but are future features, built and waiting, not dead.

    The method, for the next time: one cluster at a time, grep for
    callers, archive if clean, tsc, check the count, commit. 75
    routes removed, nothing broken, tsc clean throughout.

    checks/orphaned_routes.py. UPDATE 3 Oct: down from 90 to 77 after
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

[x] gov.orientation_script_versioned — RESOLVED 7 Oct, option (a). The
    script moved to bosly-gov/bin/bosly (336b1be) and
    /usr/local/bin/bosly is now a symlink to it. The move was
    demonstrated necessary first: on 7 Oct the orientation was edited
    twice (once to call the digest, once to fix an escaped em-dash)
    with only a timestamped .bak for recovery. Both edits went fine;
    neither had a safety net. Future edits go through the repo.
    GOV_DIR stays hardcoded; deriving it from $0 is a separate change
    if ever wanted.

    Original entry follows.
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

[x] gov.prisma_migration_history — RESOLVED 7 Oct. The migration
    history could not replay on a Postgres shadow database. Two
    causes: the pre-baseline migrations were SQLite-era
    (20260307131646_prisma_cleanup_safe uses PRAGMA and DATETIME,
    which Postgres does not have), and the history was disconnected
    from the live database — _prisma_migrations held two rows, one
    with a null finished_at, neither matching the actual schema. The
    live database's shape had been created outside the migration
    system.

    Rebuilt on a single baseline generated from the live database:
    migrate diff --from-empty --to-schema-datasource. All fourteen
    old migration folders deleted; the baseline added; the two
    orphan _prisma_migrations rows removed; the baseline's checksum
    updated to match the file on disk. Commit 46d4b8d.

    Migrate dev works again. The first migration generated on the
    rebuilt history is da6ccab (invoicedAt and invoiceId on
    CalendarEvent). The live database was not modified by the
    rebuild; the shape it had at the start is the shape it has now,
    plus the two new columns.

    Lesson: a migration history that cannot rebuild from scratch is
    not a history. The shadow database exposes this the moment
    migrate dev runs, but only if migrate dev is ever run. This one
    had been accumulating since the SQLite-to-Postgres switch and
    was found only because a schema change needed a migration.
    Memory: pattern-20261007-sqlite-era-migrations-on-postgres.

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

[x] session-20261011-orphan-cleanup — DONE 11 Oct. A day that began
    with SEO for the new pages and became 75 routes removed from the
    codebase. Kept as a capsule: the method is reusable.

    THE ARC:

    1. The SEO (morning). The sitemap and llms.txt did not mention
       /consulting or the five waiting-well routes. Both landing
       pages had no title or description. Fixed — the sitemap now
       lists them, llms.txt describes the consultancy and Waiting
       Well for AI crawlers, and both pages carry a title, a
       description, and Open Graph tags.

    2. The orientation (midday). ops.consultancy sat below the top
       five and was invisible; moved the whole entry to the top of
       the live list. Then added an IN PROGRESS section — the [~]
       items were not shown at all, so the work in flight was
       invisible. The orientation now shows in-progress first, then
       live, then gated.

    3. The orphan cleanup (afternoon). gov.orphaned_routes found 75
       routes with no caller. Worked down cluster by cluster: grep
       for callers, archive if none. Nine clusters, 75 routes, ten
       commits. Zero remain. The check is registered in the fast
       tier (16 checks now) and fails on a new orphan.

    THE FINDINGS:

      Four causes of an orphan, all a rebuild leaving the old API
      behind. Verb-in-path became REST (contacts/create to POST
      /api/contacts). Features were rebuilt (inbox actions,
      onboarding, briefings). The workflow engine absorbed routes
      into inline functions (bosly/relationships, wellness-check).
      And one route — api/config — became an orphan as a consequence
      of archiving its own callers, which the check caught at once.

      One check bug: lib/public-routes.ts counted as a caller,
      because the scan read lib/ for route paths and a policy entry
      looked like a call. It hid three orphans.

      One new list: DELIBERATE_NO_CALLER. Six finance routes — gifts,
      mtd, overview, pension, status, tax-position — have no caller
      but are future features, built and waiting. Not dead.

    THE METHOD, for the next time: one cluster at a time. grep for
    callers. Archive if clean. tsc. Check the count. Commit. 75
    routes removed, nothing broken, tsc clean throughout.

    FOR THE NEXT SESSION: accord.typecheck_clean and
    accord.doc_consistency_audit are both likely superseded — one by
    gov.tsconfig_excludes, the other by gov.claim_invariants. Read
    them first; if superseded, tick with a cross-reference.

    LESSONS (memory): pattern-20261011-an-orphan-route-is-dead-
    whatever-it-does.

[x] session-20261011-orphan-cleanup — DONE 11 Oct. A day that began
    with SEO for the new pages and became 75 routes removed from the
    codebase. Kept as a capsule: the method is reusable.

    THE ARC:

    1. The SEO (morning). The sitemap and llms.txt did not mention
       /consulting or the five waiting-well routes. Both landing
       pages had no title or description. Fixed — the sitemap now
       lists them, llms.txt describes the consultancy and Waiting
       Well for AI crawlers, and both pages carry a title, a
       description, and Open Graph tags.

    2. The orientation (midday). ops.consultancy sat below the top
       five and was invisible; moved the whole entry to the top of
       the live list. Then added an IN PROGRESS section — the [~]
       items were not shown at all, so the work in flight was
       invisible. The orientation now shows in-progress first, then
       live, then gated.

    3. The orphan cleanup (afternoon). gov.orphaned_routes found 75
       routes with no caller. Worked down cluster by cluster: grep
       for callers, archive if none. Nine clusters, 75 routes, ten
       commits. Zero remain. The check is registered in the fast
       tier (16 checks now) and fails on a new orphan.

    THE FINDINGS:

      Four causes of an orphan, all a rebuild leaving the old API
      behind. Verb-in-path became REST (contacts/create to POST
      /api/contacts). Features were rebuilt (inbox actions,
      onboarding, briefings). The workflow engine absorbed routes
      into inline functions (bosly/relationships, wellness-check).
      And one route — api/config — became an orphan as a consequence
      of archiving its own callers, which the check caught at once.

      One check bug: lib/public-routes.ts counted as a caller,
      because the scan read lib/ for route paths and a policy entry
      looked like a call. It hid three orphans.

      One new list: DELIBERATE_NO_CALLER. Six finance routes — gifts,
      mtd, overview, pension, status, tax-position — have no caller
      but are future features, built and waiting. Not dead.

    THE METHOD, for the next time: one cluster at a time. grep for
    callers. Archive if clean. tsc. Check the count. Commit. 75
    routes removed, nothing broken, tsc clean throughout.

    FOR THE NEXT SESSION: accord.typecheck_clean and
    accord.doc_consistency_audit are both likely superseded — one by
    gov.tsconfig_excludes, the other by gov.claim_invariants. Read
    them first; if superseded, tick with a cross-reference.

    LESSONS (memory): pattern-20261011-an-orphan-route-is-dead-
    whatever-it-does.

[x] session-20261010-consultancy-front-door — DONE 10 Oct. The second
    half of the day: the consultancy front door, built and live. Kept
    as a capsule because it is a different build from the Waiting Well
    pages, with its own lesson.

    THE ARC:

    1. The URL pass (afternoon). The Waiting Well citations were
       precise for the strong sources and pointed at organisation
       homepages for four of them. Fixed: the exact Cambridge chapter,
       the NHS Choice Framework on gov.uk, the ADHD Centre cost page,
       and the Norfolk & Suffolk ICB private-assessment guidance. The
       check now verifies all 22 claims resolve.

    2. The front door (afternoon). ops.consultancy Phase 1. A page at
       bosley.app/consulting: headline, about paragraph, three
       capability cards (workflow audits, automation builds, ongoing
       care), an enquiry form, and a footer with contact@bosly.app.
       A public POST route appends enquiries to
       consultancy-enquiries.jsonl, which the orientation reads. The
       first enquiry landed in the orientation the same hour it was
       built. Added to lib/public-routes.ts so it loads signed-out.

    3. The photo (afternoon). The LinkedIn photo was a .heic — not a
       browser format — then an 8.2 MB, 2316x3088 PNG. `convert`
       cropped it square, resized to 400x400, and produced a 41 KB
       JPEG. 200 times lighter, identical at display size. The lesson:
       a phone photo is not a web image until it has been converted
       and sized.

    4. The design gap (evening). The page is correct and live, and it
       does not look like something you would hire from. Named and
       deferred: ops.consultancy_design. The loop is Claude Pro, which
       can see images, which nothing else in the stack can.

    THE SHAPE, for a future session: the same lesson as the week's
    four bugs, now five. The front door passed every check —
    compiles, sourced, public, taking enquiries — and is still not
    good. Correctness is not quality. The checks verify facts; they
    cannot verify taste, voice, or design. When something is correct
    but not striking, the answer is not a check. The answer is eyes.

    LESSONS (memory): pattern-20261010-checks-verify-facts-not-quality.

[x] session-20261010-waiting-well-built — DONE 10 Oct. A day that
    began as "lets move on to finishing the waiting well page" and
    ended with a four-page, self-maintaining public resource. Kept as
    a capsule: the build is one story, and a future session needs to
    understand the mechanism, not just the pages.

    THE ARC:

    1. The shell (morning). Five routes under /waiting-well — the
       landing with four pill cards, four stubs, the footer on the
       landing only. Added to the public routes. It worked on
       localhost and redirected in the browser. The redirect was not
       the middleware, not Cloudflare, not the cache. It was
       VaultProvider: a client component fetching /api/auth/me on
       mount and bouncing any non-/signin path on failure. Every page
       in (marketing) was gated. /safety, /privacy, /terms, /faq —
       all of them. Fixed by moving the public path list to
       lib/public-routes.ts, imported by both middleware.ts and
       VaultProvider.tsx. One source of truth. The check that watched
       the middleware list failed correctly when the list moved, and
       was pointed at the new file.

    2. The Medication page. The page that mattered most — the
       founder's own situation. Plain prose, no first-person, short
       paragraphs. Every claim carries an @claim marker: source, URL,
       verified date, review window, population. Visible [source]
       citations in the prose. The claims: the BMA collective
       action, the LMC recommendations, the referral-vs-titration
       distinction, the Psychiatry UK 44-52 week titration figure,
       the 10-week referral processing, bridging prescriptions, the
       resolved supply position, and the ICB-dependent caveat.

    3. The check. gov.waiting_well, slow tier. Reads every @claim
       marker, flags stale claims and broken URLs, writes a status
       file. A nightly cron at 6am. A section in the orientation
       showing the result. On its first run it flagged three claims
       stale — because 'verified' held the source's publication date,
       not the date a human had checked. Fixed: verified means
       checked-by-a-human.

    4. Is this me? and Getting an assessment. The mirror (ADHD
       traits, autism traits, the overlap) and the signpost (ASRS,
       AQ-10, RAADS-R). Then the three routes — local NHS, Right to
       Choose explained properly, private. Citations on every claim.

    5. The FAQs and the Ask a question form. Twelve questions,
       answered, sourced. A public form posting to
       /api/waiting-well/question — honeypot, length limit, no user
       data — appending to waiting-well-questions.jsonl. The
       orientation shows "N new question(s) to answer". The first
       real question arrived and was answered the same day.

    THE SHAPE, for a future session: the page cannot rot silently.
    Every claim carries its own expiry; a check reads them nightly; a
    public form lands in the orientation. The pattern is the same as
    the unknown-intents digest — the signal lives where the founder
    already looks, and it shrinks as the work gets done.

    THE RECURRING LESSON, now four times: a mechanism that looked
    right and was not, caught by running it against reality rather
    than by a check. (1) The digest grouped nothing — built against
    empty data. (2) The drift check could not tell drift from prose.
    (3) The public surface was gated by a client redirect. (4) The
    'verified' field meant the source's date, not the check date.
    None was visible to the pipeline. All four were found by using
    the thing. The checks are good at invariants, blind to behaviour.

    LESSONS (memory): pattern-20261010-claims-carry-their-own-review-
    window, pattern-20261010-verified-means-checked-not-published,
    pattern-20261010-a-public-form-that-lands-where-you-look.

[x] session-20261007-two-arcs — DONE 7 Oct. A day that began as "lets
    keep going" on three plan items and became two arcs plus a schema
    detour. Kept as a capsule: the detour is the connective tissue.

    THE ARC:

    1. The digest and the orientation (morning). Three items: build
       the unknown-intents digest, fix the orientation script's
       versioning, clean the plan. The digest needed a classifier —
       lib/intent_classify.py labels each question bug / feature /
       question / other, rules as data. evolve_feedback.py groups by
       label and reads a status store. /usr/local/bin/bosly moved
       into bosly-gov/bin/bosly and is now symlinked. The orientation
       shows the digest summary every session.

    2. The migration detour (midday). A schema change for invoicing
       needed a migration; migrate dev failed because the migration
       history could not replay on a Postgres shadow database. Two
       causes: the pre-baseline migrations are SQLite-era (PRAGMA,
       DATETIME), and the history was disconnected from the live
       database (_prisma_migrations had two rows, neither matching
       the schema). Rebuilt on a single live baseline. This is the
       day's real lesson — a history that cannot rebuild from
       scratch is not a history, and nothing said so.

    3. The calendar and invoicing (afternoon). accord.recurring_
       appointments shipped: the add route creates a series, the
       form has a repeat control. Then accord.invoice_aggregates_
       client_appointments: schema (invoicedAt + invoiceId), a shared
       nextInvoiceNumber, a read route grouping unbilled events by
       contact, a write route that creates one invoice and marks its
       events in a single transaction, an Unbilled tab, and a
       confirmation modal. Built, not yet tested.

    4. gov.plan_hygiene resolved by removing a check. Three tuning
       passes on a plan-drift check, each pass removing false
       positives and revealing more. The patterns that indicate drift
       are the same patterns in legitimate text. No check built.

    THE SHAPE, for a future session: two of today's three big
    problems were invisible until something was run. The digest did
    nothing for nine days because it was built against empty data.
    The migration history could not rebuild from scratch, and only
    migrate dev exposed it. Both are the same shape — a mechanism
    that looked right and wasn't, caught by running it against
    reality. The checks are green throughout; both were invisible
    to them.

    LESSONS (memory): pattern-20261007-a-digest-built-against-empty-
    data, pattern-20261007-drift-is-not-checkable-by-surface-
    patterns, pattern-20261007-sqlite-era-migrations-on-postgres,
    pattern-20261007-aggregation-is-a-read-plus-a-transaction.

[x] session-20261006-feedback-sweep — DONE 6 Oct. A day that began as
    "help me with my project plan items" and finished
    accord.action_feedback_audit, but on the way it found that every
    file the sweep touched had a real bug in it. Kept as a capsule:
    the sweep was not a sweep.

    THE ARC:

    1. The list was wrong before it was worked. The plan said "seven
       settings pages remain," counted from a grep of
       components/settings/*.tsx. Eight files matched. Grepping for
       importers found five were referenced by nothing —
       AppearanceSettings, AppSettings, OnboardingPreferences,
       PasswordSettings, ThemeSettings. The live settings page mounts
       six components, three of them from that directory. PasswordSettings
       in particular implied the password UI lived in that file; it is
       inline in app/settings/page.tsx. Two turns were spent chasing
       the dead trail before the grep. The dead files are archived to
       legacy/settings-dead-20261006/ (3476b4e). Memory:
       pattern-20261006-a-file-that-looks-live-may-be-dead.

    2. app/settings/page.tsx (inline password) — the first real
       defect: a failed password change rendered in emerald with the
       word "Failed." One message state held both success and failure,
       and the JSX always used the success colour. Commit 5274243.

    3. GeneralSettings and LegacySettings — the same shape: one
       message state shared by load and save, rendered emerald
       regardless. Commits a9e5af4, e9c56e0. The load-failure path
       was also silent on General until it was routed through the
       same channel.

    4. DuressSettings — different: a state machine with four
       failure paths that set error and landed on a step that did not
       render it. checkStatus and startSetup land on idle; a failed
       storeDuressKeys returned to the phrase display with no reason.
       Bugs first: error visibility (871f59f), then a saved boolean
       that never reset after a successful delete (3663b9f), then the
       sweep (900ca3b).

    5. BillingSettings — fetchBillingData caught and discarded, so
       a failed fetch left subscription null, indistinguishable from
       "no subscription" — an active subscriber could see the
       free-tier view with a Begin Bosly Accord button. Then res.ok
       checks on the Stripe redirects. Then the sweep. Commits
       9adb967, 457baea, 3e94b95.

    6. BrandingSettings — after a successful upload, the nested PUT
       to /api/user/settings was fired and forgotten. If it failed,
       the logo appeared on screen but was never persisted. Commit
       5dba27c, then the sweep 20a0499.

    7. EmailConnectionForm — three bugs: no res.ok on the
       connection test, a swallowed fetchConnections, and a
       fire-and-forget remove with no confirm on a destructive action
       (40b4ff6, 85d7eb4, 5ff33a3). Then a partial sweep — error
       only; status is the content of the testing and done steps, not
       a next-to-the-button message, and useFeedback does not fit
       (f821181).

    THE SHAPE, for a future session: the sweep was not a sweep. Every
    file it touched had a real bug in it, and every bug was the same
    class — the app knew and did not say. That is the same shape as
    3 Oct (every bug was two parts of the system disagreeing) and 5 Oct
    (every bug was found by using the app, not by a check). Three
    sessions, one underlying pattern. The checks are green throughout;
    the pattern is invisible to them.

    The working method that held: bugs first, each its own commit,
    then the sweep as a refactor. Eight bug fixes, seven sweeps, one
    archive, two ticks, one memory entry. Nothing was pushed without
    a clean tsc and a clean build.

    LESSONS (memory): pattern-20261006-a-file-that-looks-live-may-be-dead.

[x] session-20261005-using-the-app — DONE 5 Oct. A day that began as
    "invoice last month's clients" and became nine bug fixes plus three sweeps, because
    every step of a real task was blocked. Kept as a capsule: NONE of
    the six was found by a check — they were found by using the app.

    THE SIX FIXES:

    1. accord.calendar_timezone_roundtrip — DONE. localToISO (write)
       built a local Date and converted to ISO, correct. The editor
       read it back with toISOString(), which converts to UTC again,
       so a 09:00 event showed as 08:00 and walked an hour backwards
       on every save-and-reopen. Added isoToLocalHHMM, the inverse.
       Commit abd6b86.

    2. accord.inbox_dismiss_not_persistent — REOPENED and properly
       fixed. The 3 Oct guard lived in addMessageToCache, but the
       cache is also written directly by inbox/messages/sync and
       inbox/actions, which bypassed it. Moved the guard to
       writeInboxCache, the single write path. Commit 8aa030c.

    3. accord.vault_prompt_missing — DONE. showRecovery required a
       backup flag (server hasBackup or local localHasBackup). When
       the key was missing and neither was set, the reminder rendered
       NOTHING — the user saw [encrypted] everywhere, saves failed
       silently, and the only way back was signing out. Now shows
       whenever the key is missing. Commit 844ead1.

    4. accord.invoice_number_collision — DONE. The number was
       count+1. A deleted invoice makes the count lower than the
       highest used, so the next create collided on the unique
       [userId, invoiceNumber] constraint and failed permanently.
       Numbers from the highest existing invoice now. Commit d184d1b.

    5. accord.silent_action_feedback — PARTIAL. The send dialog and
       the invoice editor now show a clear success/failure message
       next to the button. Remaining: every other action in the app.

    6. accord.mark_invoice_sent — DONE. Invoices are often sent
       outside Bosly. Added a Mark sent button; the PATCH route now
       accepts metadata-only updates. Commit 4c986da.

    7. accord.paid_invoice_zero_transaction — DONE. Mark-paid created
       a FinanceTransaction with amountPence 0, because the server
       cannot read the encrypted invoice amount; the comment said the
       user would amend it, and nothing prompted them to. A £0.00
       income row appeared. The client now sends the decrypted amount;
       if it cannot (vault locked), the route skips the transaction
       rather than writing a zero. Commit e2f23d1.

    8. accord.delete_confirm_pwa — DONE. Every delete began with a
       browser confirm(). In a PWA or iOS Safari that dialog can be
       suppressed, confirm returns false, and the delete silently does
       nothing. Replaced with an inline Yes, delete / Cancel. Every
       other confirm() in the app has the same bug — see
       accord.confirm_sweep.

    9. accord.data_events_sweep — DONE. lib/events.ts:
       bosly:data-changed carries the kinds that changed; writes emit,
       readers listen per kind. Seven components wired: FinancePill,
       ContactsPill, CalendarPill, InboxPill, ActivePill, the
       workspace, and SendInvoiceDialog. Four surveyed and
       self-contained: DataHealthPill, IdentityManager, HealthPill,
       SocialPillOrchestrator. Two wrong listeners removed from the
       workspace (both guesses). Commits 83dc53b..6d1af27.

    10. accord.confirm_sweep — DONE. Every browser confirm() replaced
        with components/ConfirmButton.tsx: eight call sites, four files
        (HealthPill 5 handlers / 6 buttons, BillingSettings,
        DuressSettings, FinancePill). A confirm() can be suppressed in
        a PWA, returns false, and the guarded action does nothing
        silently — which is how the invoice delete broke. No confirm()
        remains except the comment explaining why. Commit 6d1af27.

    11. accord.action_feedback_audit — ADVANCED. Five pills now report
        their outcome through lib/useFeedback and FeedbackLine:
        FinancePill (the reference), InboxPill, ContactsPill,
        ActivePill, HealthPill. DataHealthPill and
        SocialPillOrchestrator already reported through their own
        state. The eight settings pages remain.

    12. THE DISCIPLINE, learned the hard way over two sessions:
        before writing a patch, grep -n the exact line and sed the
        exact block, and anchor on that — never on a reconstruction.
        Then grep -c the result and read the diff, because a replace
        can land once where it should land twice, silently. And run
        tsc before the build: a replacement can match its anchor and
        still be malformed (a doubled style={{...}}, an argument with
        a stray colon). The order is anchors, then tsc, then build,
        then the count — each catches a different class. Recorded in
        memory.

    THE SHAPE: every one of the six was "the app knew and did not
    say", or "the logic was right and the condition was too narrow".
    None was a deep bug. The feeling — "I am fighting it" — was
    accurate, and it was six small things, not a broken app.

    THE GAP: no check caught any of them. The 15 checks verify that
    the parts of the system agree with each other. None verifies that
    a person can complete a task. Same lesson as 30 Sept and 1 Oct:
    walk the flow.

[x] accord.confirm_sweep — DONE 5 Oct. Every browser confirm() was
    replaced with components/ConfirmButton.tsx — a two-step button:
    first press arms, second runs, Cancel disarms. Eight call sites
    across four files:

      HealthPill        5 handlers, 6 buttons (deleteBlood renders
                        twice)
      BillingSettings   cancel Accord
      DuressSettings    remove the phrase
      FinancePill       delete a transaction

    A browser confirm() can be suppressed in a PWA or iOS Safari,
    confirm returns false, and the guarded action silently does
    nothing — which is how the invoice delete broke on 5 Oct. No
    confirm() remains in the app; the only match is the comment in
    ConfirmButton explaining why.

    Original entry follows.
    Every browser confirm() in the app.
    A confirm() dialog can be suppressed in a PWA or iOS Safari,
    confirm returns false, and the guarded action silently does
    nothing — which is what happened to invoice delete on 5 Oct. The
    invoice delete now uses an inline Yes / Cancel. Every other
    confirm() has the same bug. Find them all and replace them:
      grep -rn "confirm(" app components --include='*.tsx'
    Raised 5 Oct.

[x] accord.data_events_sweep — DONE 5 Oct. bosly:data-changed
    (lib/events.ts) carries the kinds that changed; writes emit,
    readers listen per kind. Wired: FinancePill, ContactsPill,
    CalendarPill, InboxPill, ActivePill, the workspace, and
    SendInvoiceDialog.

    Four components were surveyed and need nothing, because they are
    self-contained — they hold their own data, update it after each
    write, and nothing else reads it: DataHealthPill, IdentityManager,
    HealthPill, SocialPillOrchestrator. SocialPillOrchestrator has no
    shared list at all — its two fetches generate content.

    Also removed two wrong listeners the workspace had: it listened
    for "data-health" and "health" but reloaded loadMemory, which it
    does not display. Both were guesses, and both were wrong.

    Original entry follows.
    IN PROGRESS. bosly:data-changed
    (lib/events.ts) carries the kinds that changed; writes emit, readers
    listen. Six components wired 5 Oct:

      FinancePill      writes emit "finance"; reads listen
      ContactsPill     writes emit "contacts"
      CalendarPill     writes emit "calendar"/"finance"; reads
                       listen for "contacts"
      InboxPill        writes emit "inbox"
      ActivePill       writes emit "active"/"calendar"; reads listen
                       for both
      workspace        reads listen per-section (load split)

    REMAINING (five), quietest last:
      - SendInvoiceDialog — writes an invoice; emit "finance"
      - DataHealthPill — reads "data-health"; writes emit it
      - IdentityManager — reads "data-health"; writes emit it
      - HealthPill — reads "health"; writes emit it
      - SocialPillOrchestrator — reads/writes "social"

    THE DISCIPLINE (learned the hard way, 5 Oct): before writing a
    patch, run `grep -n` for the exact line and `sed` the exact block.
    Anchor on that, never on a reconstruction. After patching, run
    `grep -c` on the emit string and check the diff — a replace can
    land once where it should land twice, silently. Aborts and partial
    applications both cost a round-trip; reading first is faster.

    Kinds are in lib/events.ts. Pattern:
      emitDataChanged("kind")                       // after a write
      useEffect(() => onDataChanged("kind", load), [load])   // a reader

[x] accord.action_feedback_audit — DONE 6 Oct. Every live target now
    reports through useFeedback + FeedbackLine: the five pills
    (FinancePill the reference, InboxPill, ContactsPill, ActivePill,
    HealthPill), the six settings components and the inline password
    block in app/settings/page.tsx, and EmailConnectionForm. Its
    `status` state was left alone — it is the content of the testing
    and done steps, not a next-to-the-button message.

    The "seven settings pages remain" below was wrong, three ways: the
    eight-file grep list included three unreferenced files
    (AppearanceSettings, OnboardingPreferences, PasswordSettings),
    which are archived to legacy/settings-dead-20261006/ (3476b4e);
    and the inline password block in app/settings/page.tsx was never
    on the list at all. The live target count was six components plus
    the inline block.

    Bugs found and fixed on the way, each its own commit: password
    failure rendered in emerald; General/Legacy/Branding shared one
    message state with success; duress errors were set but never
    rendered; billing swallowed a failed subscription fetch and could
    show an active subscriber the free-tier checkout button; branding
    uploaded a logo and did not check whether it saved; email
    connection remove fired and forgot, and had no confirm.

    THE PATTERN, for each component:
      import { useFeedback } from "@/lib/useFeedback";
      import FeedbackLine from "@/components/FeedbackLine";
      const fb = useFeedback();
      // on success:  fb.ok("Contact saved");
      // on failure:  fb.fail(e, "Could not save the contact");
      // in the render, near the actions:  <FeedbackLine fb={fb} />

    fb.fail shows the reason when there is one — a thrown Error, a
    string, or an {error} object — and the fallback otherwise. Put the
    line at the top of the component, or inside its open content if it
    collapses. One useFeedback per component, not per row.

    DONE (5): FinancePill (the reference), InboxPill, ContactsPill,
    ActivePill, HealthPill.

    SELF-CONTAINED, no change needed (2): DataHealthPill reports scan
    failures through its own result state; SocialPillOrchestrator sets
    its own error.

    REMAINING — the settings pages. Eight fetch data
    (grep -l "await fetch" components/settings/*.tsx):
      AppearanceSettings, BillingSettings, BrandingSettings,
      DuressSettings, GeneralSettings, LegacySettings,
      OnboardingPreferences, PasswordSettings.
    DuressSettings is DONE (ConfirmButton + fb.fail, 5 Oct);
    BillingSettings is partly done (cancel button only). So seven
    remain, each a save button, a fetch, and either silence or
    setMsg in the wrong place. AppSettings and ThemeSettings do not
    fetch — nothing to report, correctly omitted.

    Also worth converting: CalendarPill and InvoiceEditor use setMsg in
    the wrong place (done for InvoiceEditor on 5 Oct; CalendarPill
    still).

    PRIORITY, from 5 Oct. Every action in the app should report its
    outcome. This is the single highest-value item from three days of
    use — "the app knew and did not say" was the shape of every bug.

    Original entry follows.
    Every action in the app
    Every action in the app should report its outcome: success or
    failure, short, next to the button. Today found the app mostly
    does neither: the send dialog showed a small error above the
    buttons and closed silently on success; the invoice editor showed
    its message 400 lines above the Create button; mark-paid and
    delete swallow errors entirely; and the vault, when locked, failed
    every save silently. None is a logic bug — all of it is the app
    not saying what happened, which is what "clunky" means. This is
    the single highest-value item from three days of use.
    Every action in the app
    should report its outcome: success or failure, short, next to the
    button. Today found that the app mostly does neither: the send
    dialog showed a small error above the buttons and closed silently
    on success; the invoice editor showed its message 400 lines above
    the Create button; mark-paid and delete swallow errors entirely;
    and the vault, when locked, failed every save silently. None is a
    logic bug — all of it is the app not saying what happened, which
    is what "clunky" means. Work: walk every button, note whether it
    reports, fix the ones that do not. Raised 5 Oct.

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

[x] gov.public_surface_gated — FIXED 10 Oct (4e1ca6e). Every page
    in app/(marketing) redirected a signed-out visitor to signin.
    /safety, /privacy, /terms, /faq, /invoice, /waiting-well — all of
    them. The middleware allowed them (isPublicRoute returned true),
    and the app served them (curl got 200), but VaultProvider fetched
    /api/auth/me on mount and, on any failure, redirected to signin
    unless the path started with /signin. So the public surface was
    gated by the client, not the server — and the server-side check
    could not see it.

    The fix: the public path list moved to lib/public-routes.ts,
    imported by both middleware.ts and VaultProvider.tsx — one source
    of truth, so the two cannot drift. VaultProvider skips the
    redirect for public paths, and still bounces a signed-out visitor
    away from private ones.

    Found while building /waiting-well and testing as a signed-out
    visitor. The redirect had never been noticed because the pages
    are only ever viewed by someone already signed in.

    The shape, same as two earlier findings: a mechanism that looked
    right and was not, caught by running it against reality. The
    digest grouped nothing (pattern-20261007-a-digest-built-against-
    empty-data); the drift check could not tell drift from prose
    (pattern-20261007-drift-is-not-checkable). Here, the check
    verified the route was allowed, not that the page served.

    Note on gov.public_routes_are_public: it did not catch this, and
    it should not have — its own entry says "a regression guard, not
    a full derivation." It asserts four known paths are present in
    the middleware prefixes. It does not test behaviour. A
    behavioural check (fetch a public page signed out, assert no
    redirect) would catch this class, but it makes HTTP requests and
    belongs in the slow tier, not the fast one. Not built yet — the
    manual test found it in five minutes. Raised 10 Oct.

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

[x] accord.recurring_appointments — DONE 7 Oct. The add route reads
    repeats and repeatUntil and creates the series in one transaction
    (77f72a7); the calendar add form has a repeat select and an until
    date (9ce158a). recurringGroupId on the model and the scope:
    "future" logic in calendar/update and calendar/delete already
    existed — the series works with them for free.

    Shipped: weekly, every 2 weeks, every month, with a default
    3-month horizon if no until date is given. Not shipped:
    chosen-weekdays from the original design note. The user asked for
    weekly or biweekly; both are live. Occurrences are separate rows
    (the recurringGroupId groups them), not generated on read — the
    design question in the original note is answered by what was
    already on disk.

    Same shape as accord.invoice_aggregates_client_appointments, which
    is now built (untested): a series creates many rows, and the
    invoicing path aggregates one client's appointments into one
    invoice. The two interact — the recurring feature makes the
    aggregate feature more valuable, and both are in place.

    Original entry follows.
    [ ] [LIVE] accord.recurring_appointments — Add a client to one day and
    repeat them weekly, biweekly, or on chosen weekdays, rather than
    re-adding them for every occurrence in the month.

    Raised by a real user on 5 Oct (logged as an unknown intent): "When
    I'm adding a client I have to repeatedly add the client for multiple
    days throughout the month. It would be good if there was a way to be
    able to add a client on a day and then select every week or
    biweekly."

    Same shape as accord.invoice_aggregates_client_appointments (now
    built, untested): both are the calendar failing to match how the
    work actually happens — several appointments for one client,
    invoiced once or booked in a run.

    Design: on the event editor, a "Repeat" control — none, weekly,
    every 2 weeks, or chosen weekdays — that creates the series. Needs
    a way to edit or delete the whole series, and a decision on whether
    occurrences are separate rows or generated on read.

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

[x] gov.claim_invariants — DONE. Registered in the fast tier and
    passing. checks/claim_invariants.py checks the free-pill list:
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

[ ] [LIVE] ops.ico_registration — Register with the ICO.
    SCHEDULED: end of December, just before the day-0 emails go
    out. Not before — the fee is annual and there's no reason to
    start paying it months before there are clients to process
    data for. When done, update /privacy and the FAQ to state it.
    Until then, both documents must not claim registration.

[x] accord.doc_consistency_audit — DONE 16 Oct, superseded. This
    entry calls itself the "immediate predecessor to
    gov.claim_invariants", and that check is now built, registered,
    and passing. The two remaining items are tracked elsewhere: the
    ICO registration claim waits on ops.ico_registration, and the
    quantum claim waits on accord.kyber_status_decision.

    Original entry follows.
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

[x] gov.cron_sanity_repo_wide — DONE 19 Oct. checks/cron_sanity.py
    now scans every *.sh under bosly-1.0, bosly-keep and bosly-gov
    for a shebang on byte 1, not just cron-invoked scripts and
    /usr/local/bin/bosly-*. Skips node_modules, .next, legacy,
    .git, dist, build. Eight files newly covered (deploy.sh,
    pm2-start.sh, restore-bosly.sh, start-bosly.sh, scripts/
    postbuild.sh, scripts/migrate.sh, deploy-safe.sh, and
    bosly-keep/scripts/run-tests.sh) — all pass. SUMMARY: 30
    passed, 0 failed. The CRLF class can no longer enter via a
    repo script.

    Original entry follows.
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
These were the cross-references for the claim class of checks.
They are now their own entries, above and elsewhere in the plan:

  accord.doc_consistency_audit, gov.claim_invariants,
  accord.naming_honesty, accord.stub_detection,
  gov.plan_tracks_known_gaps, accord.middleware_public_routes,
  gov.cron_sanity_repo_wide.

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

[x] keep.scripts_typecheck_excluded — DONE 16 Oct, un-excluded. The
    `scripts` exclude is removed from Keep's tsconfig. One error
    surfaced: scripts/test-prices.ts imported getFundTickers from
    lib/market-data, which no longer exports it. Nothing referenced
    the file — a standalone diagnostic with no callers — so it is
    archived to legacy/scripts-dead-20261016/.

    The verify suite (scripts/diagnostics/verify-*.ts) now
    typechecks, and it does run: scripts/run-tests.sh iterates every
    verify-*.ts, and keep.invariants runs that script. tsc is clean.
    Commit 7e515fa0.

    Original entry follows.
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

NOTHING SCHEDULED. This section is an ideas bank, not a calendar.

WHY NOTHING IS SCHEDULED — the not-Meta decision, 17 Oct 2026

For two months I posted consistently on Instagram and Facebook:
three a week, captions, the lot. Result: about 60 followers on
Instagram, almost nothing on Facebook, and a slow drift into
being an "ADHD creator" — posting ADHD tax stories and personal
stuff because the algorithm rewarded it. That was not who I
wanted to be and not what Bosly is.

Then a seven-hour doom-scroll in a single day. That was the
number that made the decision. The apps are deleted from the
phone. The accounts stay (business pages) but there is no
posting on either platform.

The reasoning, so it doesn't get relitigated:
- The things that get traction on Instagram are misinformation,
  bodies, animals, funny clips. An echo chamber of nothing.
  Hours of scrolling produced nothing I'd remember the next day.
- "You can't sell on Instagram" is true, but the answer isn't
  "so post relatable content forever." The answer is that
  Instagram is the wrong audience for a deliberate, principled
  investing product.
- The effort/value ratio was bad: two months of consistent
  effort for 60 followers, and exhaustion two months in. If I'm
  exhausted at month two, I can't sustain it to month twelve.
  So I'm not trying.
- The ADHD resource is good and stays. It goes in LinkedIn's
  Featured section as a thing I built, not as a content series.

What replaced it:
- LinkedIn, once a week, Thursday. One post, written because
  there's something to say. If there isn't, skip the week.
- Morning routine: coffee, 5-10 minutes, like a couple of
  things, comment on 2-3 where I have something genuinely
  useful to add. Participation, not consumption. Bounded.
- Primary URL: the consultancy page. Featured cards: the ADHD
  resource, the waiting well page, Bosly Accord, Bosly Keep.
- Reassess 1 February 2027. The question: did this produce
  consultancy enquiries or Accord signups? Not "did it go
  viral." Real output.
- A prompt for the social-media chat was written 17 Oct.

IDEAS BANK — for Thursdays when there's something to say,
but nothing drafted yet. One line each; expand when used.

- The unsent invoice. Four weeks angry at a client for not
  paying. She never got the invoice. It was in drafts. Lost
  the client. Cost: the relationship, not the money.
  (Personal. Instagram-shaped. May not translate to LinkedIn
  — decide if it's worth adapting.)

- Founding Members ask. Looking for 20 people to shape Bosly
  Keep. Free AI features for life, £15/mo instead of £25. A
  seat at the table, not a discount.
  (Check the numbers against the current plan before using —
  this was drafted pre-decision and may be out of date.)

- No app stores. App stores ask for 30% and a hundred pages
  of terms nobody reads; the trade is your data for
  convenience. Bosly isn't on them because that trade breaks
  the promise. The data never leaves your control.
  (Strong on LinkedIn. The argument doesn't need the video.)

- Quantum readiness. Most apps encrypt to today's standards;
  quantum will break those in 10-15 years. Data stored today
  in plain AES becomes readable in 2040. Bosly uses
  post-quantum cryptography. Building for 2040, not 2026.
  (Strong on LinkedIn. Works as text.)

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

[x] gov.custodian_live — DONE 19 Oct. The Custodian's project chat now uses the tool loop.
