BOSLY GOV — PLAN ARCHIVE
Everything below was [x] in PLAN.md and moved here on 3 November 2026,
verbatim. The live plan is PLAN.md. plan_query reads both.
================================================================

[x] accord.butler_knows_today — DONE 30 Oct. Asked "27-29 October"
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

    STEP 2 DONE 30 Oct. _read_prompt in routers/tool_loop.py replaces
    the file's static "Today is ..." line with
    datetime.now(ZoneInfo("Europe/London")) on every read — read-only,
    no file mutation. Proven: "what's today?" -> Friday 30 October
    2026; NEXT.md updated with 30 Oct. The stale date caused four wrong
    dates (the 2025 pick, the NEXT.md header, a memory decision dated
    26 Oct, and a tick dated 26 Oct). Ticked [x] above; the body was
    stale when the tick landed, and the butler flagged the contradiction
    rather than silently closing it — see gov.plan_updates_have_no_anchor.


[x] accord.ui_cache_store_needs_cors — DONE 1 Nov. The learned-answer
    cache is stored by the drawer (Accord's chat, 3100) and checked by
    Gov's loop before the model, so a hit means no model call. The UI
    (served by Gov on 3102) stores nothing: its POST goes to
    /gov/api/executive/cache, and Gov has no such route — 404. The route
    is Accord's, on 3100. THE FIX: CORS on Accord's cache route
    (Access-Control-Allow-Origin for 3102, credentials true, an OPTIONS
    branch), or a Gov proxy that forwards to 3100 with the founder
    token. Until then the reduction works for the app's chat and not
    the UI's. THE CHECK: gov.answer_cache_fills — ask a question, assert
    the entry count went up; it would have caught this in one run.
    DONE 1 Nov: the route pins origin 3102 and sets credentials;
    middleware lets the OPTIONS preflight through for this path
    only; the UI stores to 3100; gov.answer_cache_fills proves
    the store on every fast run.


[x] accord.secret_unset_blocks_founder_token — FOUND 1 Nov. If
    BOSLY_AUTH_SECRET is unset, middleware.ts redirects every non-public
    route to /signin BEFORE the founder-token bypass below it runs. So on
    a box with the secret missing, the founder cannot reach any
    non-public route even with a valid FOUNDER_SERVICE_TOKEN, and
    requireAccord's isFounder bypass never runs because middleware
    redirects first. The founder gate has two halves; isFounder fixed the
    route half (committed 1 Nov), the middleware half is still open. THE
    CHECK: a founder-token request to a non-public route on a box with
    the secret unset must not redirect.


[x] accord.founder_surface_is_one_gate — FOUND 2 Nov. The founder
    has been refused from the founder's own system repeatedly because the
    entitlement lived in many gates: requireAccord's tier (fixed 1 Nov),
    hasProduct/productsFor (the Executive), the client pills via
    /api/auth/me's tier, chat via getUserTier, email-connection, and
    data-health's own hasAccordAccess. Each was patched where the founder
    was last refused; a survey found a gate nobody would have hit for
    weeks. THE RULE: effectiveTier(user) in lib/managed.ts returns
    "accord" for the founder; hasProduct returns true and productsFor
    returns FOUNDER_PRODUCTS. Every gate calls the helper; none re-reads
    the tier. THE CHECK: accord.founder_has_full_access asserts the
    wiring, and /api/auth/me must return subscriptionTier "accord" and
    isFounder true — the live proof. A new gate must call effectiveTier,
    not derive the rule again, or the series continues.


[x] ops.pm2_reaps_its_children — FOUND 2 Nov. Two next-server
    processes were running: Accord's on 3100 and Keep's on 3101, both
    under pm2's pid 1030. Keep's had been up 9 days and pm2 had lost
    track of it; killing it made pm2 respawn a fresh one. So pm2 delete
    and pm2 restart do not reliably reap their children — a stale child
    keeps running with the old env and the old build, and every check
    that greps a process name finds it. THE CHECK: after a deploy,
    exactly two next-server processes, one owning 3100 and one owning
    3101, and nothing else. Named here because it made the founder
    token look missing three times in one session.


[x] gov.butler_documents_itself — DONE 3 Nov. The butler answers
    and acts, but it does not document its own work. A session that
    decided something leaves a decision in the conversation and nowhere
    else. The founder has been the documenter — the capsule at the end of
    a session is written by the chat, not by the butler. When the founder
    talks to the butler more, and the chat less, that stops working.
    THE FIX: a standing rule (write before you finish the turn, do not
    wait to be asked) and ONE tool, session_summary, that writes the
    memory entry, ticks or adds the plan item, and appends the capsule
    line — three acts, one call, because three calls is three things to
    forget. Same rule as the rest: move the state into the tool. THE
    CHECK: a session that changed the plan has a memory entry and a
    capsule line dated the same day; the tier says so if the plan moved
    and memory did not.
    DONE 3 Nov: session_summary, dry-run by default, one call
    files memory + plan ticks + a capsule line through a
    shared filing core; idempotent; the standing rule says
    write before you finish; gov.session_summary_files
    proves the mechanism. ingest_summary is the same core
    with a different door — next.


[x] accord.invoice_number_lexicographic_collision — FOUND 3 Nov.
    FOUNDER-REPORTED, then found in the code. nextInvoiceNumber read the
    last invoice with orderBy: { invoiceNumber: "desc" } — a TEXT column,
    so the sort is lexicographic: "INV-099" sorts after "INV-100", the
    function computed INV-100 again, and the unique constraint refused
    the create. Every press after the sequence crossed 100 returned
    'invalid Prisma.invoice.create()'. The plain POST had the same bug and
    would have hit it on the next press. Fixed: read the recent rows and
    take the true numeric max; the unique constraint stays the backstop.
    THE CHECK: with INV-009, INV-010, INV-099, INV-100 present, the next
    number is INV-101 — a pure function check, no database needed. This
    is the class of bug a check catches before a founder presses a
    button.


[x] gov.prompt_cache_is_not_invalidated_by_the_date — FOUND 3 Nov.
    THE COST BUG. _read_prompt() rewrites "Today is <date>" inside the
    system prompt on every read. A prompt cache is a PREFIX MATCH: one
    changed character invalidates every token behind it. So every call
    is a cache miss, and the 15KB system prompt is re-billed at full
    input price on every round. This is the 47% the provider's email
    was about, and it is one line. THE FIX: the system prompt becomes
    static; the date moves to the first user message, after the cache
    breakpoints. Order the prompt tools -> system -> conversation ->
    date, so the stable prefix is cacheable and the variable part is
    last. THE CHECK: the composed prompt's first 10KB is identical
    across two reads on the same day.
    DONE 3 Nov: the system prompt is the static prefix; the date,
    ecosystem and repos ride on the first user message.
    gov.prompt_prefix_is_stable proves it.


[x] gov.model_is_chosen_at_the_door — FOUND 3 Nov. Model routing, done
    the way it works. Switching models mid-session destroys the cache:
    each model has its own, and a switch re-processes the conversation
    at full price. So the model is chosen when the request arrives and
    not changed: shaped questions (read a tool, format the answer) go to
    the cheap model; decisions and builds go to the strong one;
    overnight builds are strong + batch. THE MECHANISM: a model
    parameter on _call_api, set by a cheap classify_task() heuristic at
    the door, and the model logged on every tool call line so the cost
    is visible. THE CHECK: a shaped question logs model=cheap; a build
    logs model=strong; no mid-session switch.
    DONE 3 Nov: classify_task, chosen once at the door; the model
    and the four token counts on every tool call.
    gov.model_and_cost proves it.


[x] gov.tool_results_are_cached — FOUND 3 Nov. The deterministic floor
    for tools. A tool that succeeded with the same arguments returns its
    stored result instead of running again: the butler does not re-read
    the same file or re-query the same plan twice in a session. Same
    idea as answer_cache, applied to tool calls. THE CHECK: a second
    identical call returns from cache and logs stop_reason=cache.
    DONE 3 Nov: the read-only cache with the write list excluded;
    gov.model_and_cost asserts the exclusion.


[x] gov.code_map_is_generated — FOUND 3 Nov. THE CODE MAP. The butler
    does not need a language; it needs a map of the codebase that does
    not cost 50,000 tokens a turn. Generated from the code, never
    written by the model: Python's ast for Gov, exports/interfaces for
    the TypeScript repos. Two tools, code_map(module) and
    code_search(symbol); the map is read before read_file on anything
    unseen. THE ANTI-STALENESS RULES, because a stale map is worse than
    no map: (1) a single code_map_version hash — every file's path,
    mtime and size — is the cache key; the generator runs on the hash,
    not on a schedule the founder has to remember. (2) gov.code_map_is_
    fresh compares the map to the files: every file present, every
    export current, or excluded with a reason; a mismatch FAILS the
    fast tier, not a note. (3) gov.code_map_saves_tokens measures it:
    map calls vs file reads, tokens saved — the number is the reminder,
    so the founder does not have to notice the cost rising.
    DONE 3 Nov: routers/code_map.py, code_map and code_search;
    gov.code_map_is_fresh fails the tier on a stale map.


[x] accord.the_tool_line_does_not_render — FOUND 31 Oct. The loop's
    last line: show tool_events in the surfaces. Five wires were fixed
    (route key, drawer field, drawer renderer, UI renderer call, the
    chatArea container) and the server is proven correct — curl gives
    mode: tools, tool_calls: [read_file]. The tool line still does not
    appear, and the console stays silent. Two causes were found but not
    closed: the transcript 400 (a bot row written empty; fixed with a
    guard) and the possibility that the console being read is not the
    UI page's console, or that the browser is on an old app.js despite
    ?v=17 (Network -> Response is the check, not done). NOT DONE. The
    honest next step: open http://localhost:3102/gov/, its own
    DevTools, Network -> app.js?v=17 -> Response (confirm the file),
    Console -> ask, read [sendChatMessage res]. Do not patch another
    renderer until the browser's copy is confirmed.
    DONE 2 Nov: the tool line renders. Confirmed in the browser on
    app.js?v=20 — the ☆ above the reply is the tool indicator
    drawing. The server was always correct and the five patched
    wires did land; the display was never broken, only unconfirmed.


[x] gov.prompt_is_a_description — DONE 1 Nov. THE RATCHET. The
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
    PROGRESS 1 Nov. Part (2) THE TOOLS is done: the tool list is generated
    from routers/tools.py TOOLS on every _read_prompt() call, so it
    cannot go stale. Before: the prompt said "EIGHT TOOLS", listed
    thirteen, and TOOLS held twenty-three — ten tools were invisible,
    which is the stall. tools_prompt.txt is now the standing rules only
    (parts 3 and the head of 1); tools_prompt.tools.md is the per-tool
    operational prose, keyed by name and lifted verbatim. The ecosystem
    summary (part 1, partial) and the repos are composed from
    ecosystem_state and git, mtime-cached on PLAN.md and things.db. The
    check gov.prompt_matches_tools proves the prompt and TOOLS agree in
    both directions and that no notes heading names a phantom tool.
    STILL OPEN: part (1) THE WORLD as a described section (what exists
    and what it is for — plan, the pile, memory, transcript, the three
    repos), and part (4) THE SKILLS — "working the week's list" is still
    a procedure carried every turn, not a file read on demand. The item
    is not done until a new capability means DESCRIBING a store or a
    tool, not adding a rule.
    DONE 1 Nov. Part (1) THE WORLD: a prose section now describes
    the plan, the pile, memory, the transcript, and the three
    repos — what each is for, not how to use it. Part (4) THE
    SKILLS: 'working the week's list' moved out of the prompt into
    skills/working-the-week-list.md, read on demand by the new
    read_skill tool; the prompt names the skill but does not carry
    it. gov.prompt_matches_tools now also asserts every skill file
    is named in the prompt, the procedure is NOT carried, and
    read_skill is a real tool. The four parts are all done; a new
    capability now means describing a store or a tool, not adding
    a rule.


[x] gov.one_pile — DONE 30 Oct. THE CONSOLIDATION. There are three
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

    DONE 30 Oct. The jsonl moved inside the repo (bosly-gov/data/,
    gitignored for the cuids, backup covers it); the 39 backfilled into
    the pile, idempotent by a backfill:<sha1> tag; the founder route
    logs every message as founder_question; gov.unanswered_in_the_pile
    (fast, 31 checks) fails if the pile falls behind the jsonl. The
    butler could not read the file before the move — read_file refuses
    paths outside the repos — and read-and-stopped when asked to write
    the backfill itself: it composes from a shape, not a description.


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


[x] gov.the_check_proves_the_file_not_the_process — DONE 30 Oct. The
    gap every code fix has. gov.tool_loop_selftest runs python3
    routers/tool_loop.py in a SUBPROCESS, which imports the fixed file,
    so it went green while the RUNNING Gov still had the old code: the
    guard's NameError was fixed, committed, and passing, and the live
    server still crashed until pm2 restart. A check that exercises the
    code on disk is not a check that the server is running it. This is
    the same shape as 26 Oct's FOUNDER_USER_ID: a file that changed and
    a process that did not is a change the system says and does not do.
    THE FIX: a live probe. The runner uses subprocess.run(shell=True),
    so a check is any shell command — gov.executive_proxy_live already
    hits localhost. A probe that POSTs to /api/chat with a known-empty
    message and asserts cannot_help in the response proves the process,
    not the file. THE COST: it calls Claude and needs the server up, so
    it belongs in the SLOW tier, not the fast one — the fast tier stays
    cheap and offline, the slow tier proves the process. Do not put it
    in fast.

    PROVEN 30 Oct. The __probe_empty__ sentinel makes the guard
    deterministic (no API call, no tokens); gov.cannot_help_live POSTs
    it to /api/chat and asserts cannot_help, in the SLOW tier (cron
    06:00). Proven both ways: sentinel broken + restart -> [FAIL]
    gov.cannot_help_live; restored -> [PASS]. The probe goes red because
    the RUNNING process is wrong, even when the code on disk is right —
    which is the gap this item named. Fast stays 30; slow is 2.


[x] gov.the_loop_is_not_a_count — DONE 31 Oct. Asked "did I fix the
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

    EVIDENCE 30 Oct. Asked the same question again, the butler did not
    loop. It searched things.db first (nothing), searched checks.yml
    (nothing), found the loop item itself, and said: "I don't know, and
    neither does the record. I don't want to repeat that failure by
    blindly grinding through the Accord codebase — tell me where the
    invoice PDF is generated and I'll go straight to it, targeted, not
    a loop." That is the fix, in behaviour: search the record first,
    name the previous failure, and stop rather than grind. The repeat
    guard is still wanted as a floor; the habit is the thing that
    worked. The PDF was fixed by the founder and never recorded, which
    is why the record said 'unknown' — a fix that is not written down
    is a fix the system cannot learn from.

    EVIDENCE 30 Oct, a named failure. The log line built for this item
    fired: "tool loop: empty answer after 3 rounds; calls: [('read_file',
    True, ''), ('read_file', True, '')]". The loop was not a runaway —
    it read two files, produced no text, and stopped. That is a
    different failure from the 20-iteration grind, and the log named it
    rather than guessing. The fix that followed was a prompt rule, not
    a number: "reading is not doing — the turn is not complete until
    patch_file or write_file returns ok, or you say what is missing."
    After the rule, the same task completed: two patches, ok:true, the
    diff landed, 200 in the access log. Three iterations, each tested:
    narrate ("I'll update") -> read and stop (two reads, silence) ->
    act (two patches, reported). The repeat guard is still a floor; the
    rule is what moved the model.

    DONE 31 Oct. THE FLOOR: a repeat guard tracks (name, sha1(args))
    and stops on the same tool with the same arguments twice, naming
    the tool ("I called read_file twice with the same arguments").
    THE DIAGNOSTIC: the silence message now names what was called ("I
    called 2 tool(s) (read_file, read_file) and produced no answer") —
    the evidence the log already had, in the message the founder sees.
    THE PROOF: two self-tests, 11/11 — the repeat guard on a repeated
    call, the ceiling on distinct calls. The runaway test had to change:
    with a repeat guard, the same call stops before the ceiling, so the
    old test no longer proved what it said. It failed, and that was the
    test working. NOT DONE: the drawer still discards tool_events; the
    repeat guard catches repeats, the read-and-stop (two different
    reads, no write) is caught by the message, not the guard.


[x] accord.founder_door_does_not_log — DONE 30 Oct. THE INVERTED
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

    STATUS 30 Oct. MECHANISM PROVEN. The silence guard sets
    cannot_help (self-test: "PASS: silence guard sets cannot_help",
    9/9 in routers/tool_loop.py); handle_api_chat returns it; the
    founder route posts it to /api/unanswered, fire-and-forget. Along
    the way the guard itself was found broken: the logging.warning
    added to it referenced an unimported logging, so when the guard
    fired it threw NameError instead of yielding the message — the
    failure path crashed instead of reporting. Fixed (358fdf9). NOT YET
    PROVEN END TO END: no real empty answer has occurred since the
    wiring, so the pile has not yet received one from the founder door.
    The first real empty will prove it. THE "I DON'T KNOW" CASE IS
    STILL OPEN: the butler saying "I don't know" (as it did on the PDF
    question) is not the silence guard and sets no flag — that needs a
    tool the butler calls, not a field.

    DONE 30 Oct, PROVEN LIVE. The founder route now posts EVERY message
    to /api/unanswered with kind=founder_question — not only the
    empties. The founder's answered questions are the roadmap: "how do
    I invoice a client for multiple days" was answered and is a feature
    request. Gov's route takes a whitelisted kind (founder_question |
    unanswered, else unanswered). Proven end to end with a real
    question: thing-1793369187578-739a, "How do I invoice a client for
    multiple days?", userId:cmunzvouy0002gihgnhgz164o, in the pile.
    Source -> bundle -> process, all verified before asking — four
    patchers and three deploys today reported success and changed
    nothing, so the bundle grep is now part of the move. Still open:
    the "I don't know" case needs a tool the butler calls, not a flag.



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


[x] accord.learned_answer_cache — FOUND 22 Oct. THE LADDER BUILT
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


[x] ops.crlf_line_endings — DONE 23 Sept. 57 files had CRLF line endings and/or UTF-8 BOMs. All normalised to LF, no BOMs. Most importantly: deploy.sh and restore-bosly.sh had CRLF, so their shebangs were '#!/bin/bash\r' — the kernel reads that as 'bash\r' and refuses to run them. Same class as the bosly-monitor shebang bug. Verified: zero CRLF, zero BOMs, typecheck clean. Some shell scripts in the repo
    have Windows line endings (CRLF). scripts/postbuild.sh has
    them: its trailing || true guards fail with "$'true\r':
    command not found". Cosmetic for the cp commands, but the
    guards are broken. Check all .sh files and normalise to LF.


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


[x] accord.accord_revision — DONE 24 Sept. ACCORD.md bumped to v1.3.0. Added Part III — Where Bosly Is Today, listing what's encrypted (invoices, health, chat memory), what's plaintext (contacts, calendar, cards, finance, conversations, client patterns), what the bot can and can't do post-hardening, and what's not yet built. Existing parts shifted: What's Planned is now Part IV, Amendment is Part V. Also updated the Preamble, Article 1.1, and Article 6.2. The document now reads as a target with an honest progress marker. Revise the Accord to reflect
    the direction: keep the target (everything encrypted),
    add a "where Bosly is today" section listing what's
    migrated and what isn't. The Accord is a promise with
    a progress marker, not a description of the current
    state.
    Estimate: half a day.


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
