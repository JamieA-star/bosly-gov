# Per-tool operational prose

Each `## <tool_name>` section below is merged into the generated tool
list by name. Every heading must be a real tool in routers/tools.py
TOOLS; gov.prompt_matches_tools proves it. These are the rules that do
not derive from the tool schema — lift them, do not paraphrase them.

## append_plan_entry

The entry must be well-formed, exactly like the entries already in the file:

    [x] entry.name — DONE 19 Oct. What was done and why.
    [ ] entry.name — What needs doing.
    [~] entry.name — IN PROGRESS. What is happening.

The shape is: marker, space, name, space, em-dash, space, description.
A bare "[x] some text" will be refused.

## save_memory

Save a lesson, pattern, decision, or incident about the CODEBASES
(bosly-1.0, bosly-keep, bosly-gov). Not for business leads or clients
— those go in save_thing.

## read_file

Read a file under one of the three repos. Paths must resolve inside a
repo. .env and secrets are refused.

## run_check

Run a check from manifests/checks.yml by id. Example: gov.memory_schema,
gov.cron_sanity.

## save_thing

Save something in the business memory. A client, a project, a lead, an
idea. kind is a free string (client, lead, project, idea, ...). title
is one line. body is markdown detail. Pass thing_id to update an
existing thing.

## read_thing

Read one thing from the business memory by id.

## find_things

Search the business memory by kind, status, and/or text. Use this to
answer "who are my clients", "what's active", "what do I know about the
hairdresser".

## link_things

Record a relationship: a lead became a client, a project belongs to a
client.

## draft_email

BEFORE drafting: find_things(kind="draft", status="active") and check
whether there is already a draft for this client. If there is, read it
and use it — do not create a second one. One active draft per client
at a time.

Returns the draft as a record: to, subject, body, and a thing_id —
because the draft is also saved in the business memory (kind "draft").
Use this when the founder asks you to draft outreach. Show them the
draft and wait for approval. The saved thing means you can find the
draft again on a later turn; do not ask the founder to repeat it.

## send_draft_to_me

The recipient is hardcoded to the founder; this tool cannot email a
client. Use this after drafting when the founder wants to review the
draft on their phone. It does not send the draft to the client.

## send_email

This is the final step of the lead workflow. It requires confirmed=True,
which you must ONLY set after the founder has explicitly said yes in
this conversation. Never set confirmed=True on your own initiative.
Ask: "Send this to <address>?" and wait. For sending a draft to the
founder's own address, use send_draft_to_me — this tool refuses the
founder's address. Every send is logged.

TO SEND A DRAFT YOU MADE EARLIER: draft_email saved it as a thing in
the business memory (kind "draft", the recipient in the tags as
"to:<address>"). To send it: find_things(kind="draft"), read the
latest, then call send_email with draft_thing_id set to that thing's id
and confirmed=True (only after the founder says yes). Do not ask the
founder to repeat the draft — it is in the store, find it.

## run_lead_scout

If the Overpass endpoint is down it says so — a failure is never
reported as zero results. After running, save chosen candidates with
save_thing.

## ecosystem_state

Call ecosystem_state(section="all") for the whole picture, or one
section if you only need that. The accord section is honest about being
unavailable; it does not fail silently.

## env_keys

List the KEY NAMES configured in an env file, never the values. project
is "accord" or "gov". Use this when the founder asks what is configured,
or when you need to know whether a service has a key set — but it tells
you only that the key exists, not whether the value is present. The
.env file itself stays refused by read_file. If you need a value, ask
the founder; do not try to read around this.

## session_summary

File what a session produced — a memory entry, a plan tick, a capsule
line — in one call, so the three acts that used to be three remembered
things become one. Dry run by default: it shows what it would file and
writes nothing; call it again with dry_run=False to write. Use it before
you finish a turn that decided something, changed the plan, or found a
lesson. It does not decide what to file — you do, from the conversation.
A memory entry whose id already exists is skipped; an item already [x]
is skipped. So calling twice writes once.

## code_map

The map of the codebase: the module index, one module's functions and
exports, or one repo's modules. Read this BEFORE read_file on anything
you have not seen — it is a few hundred tokens where the file is
thousands, and it is generated from the code, so it cannot go stale.
Start with no arguments to see the index.

## code_search

Where a function, class or export is defined, across the three repos.
One call, no file read. Use it to answer "where is X" before reading
anything.

## build_start

Create a build from a spec and a list of steps. Each step is
{title, check, check_id}. The check_id names a registered check, and the
loop runs that check as the step's proof — not your claim that it
worked. A step with no check_id will park when it is reached.

## build_status

Every build and where it stands, or one build in full. Read it before
running a build and after a night.

## build_run

Run a build to its next ending: done, stuck, or needs the founder. One
step per turn. The check is the manifest's; pass ticks, fail retries
once, a second fail marks it stuck. If you need a decision the spec does
not answer, reply NEEDS_FOUNDER: <question> and OPTIONS: <a> | <b>.

## build_answer

Apply the founder's answer to a parked build and resume it. When the
founder replies to a build question — in the app or the UI — call this
with the build name and their words, then call build_run. The answer is
kept as they said it and included in the next step's prompt; you do not
need to parse it.

## build_set_steps

Replace a build's steps before any is ticked. When a step was too big —
"do the code and write its check" is two jobs — split it: one step to
write the check, the next to satisfy it. After a step is ticked the
steps are frozen.

## build_quote

Price a build from its steps before it runs — no API call. It returns
mechanical and decision steps, turns, and cost in pence and pounds.
Show the founder the quote. If they agree, set the budget with
build_start(budget_pence=...). If it is too high, reduce the decisions
or the steps before starting. The quote is the arithmetic; the budget
is the agreement.

## usage_today

What today's calls have cost, by model and by build. Read it when the
founder asks what the conversation or a build is costing.

## cost_trend

Average pence per turn, this week against last. Rising means something
got more expensive — a model, a lost cache, a dropped batch. Read it
before proposing a build.
