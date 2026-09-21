# Bosly — Working Agreement

How we work together. Not the plan (that's *what* to do). Not the
memory (that's *what's been learned*). This is *how*.

Adjust over time. If a session reveals a new convention, add it.
If a convention stops fitting, remove it. This is alive.

---

## The Loop

1. **Investigate** — read the actual source. `grep`, `sed`, `cat`. Never guess.
2. **Write** — a Python patcher that aborts if anchors aren't found.
3. **Verify** — run the affected check. Confirm the change worked.
4. **Commit** — small, atomic. The message explains the *why*.
5. **Tick** — update `PLAN.md` if the item is done.
6. **Teach** — write a memory entry to Gov if a lesson emerged.

---

## Patches

- Python patchers, named `patch_<topic>.py`
- Abort if any anchor string is missing — never partial edits
- Each patcher is committed, run, verified, then deleted
- Backup file written by the patcher before it modifies anything
- `.bak` files never committed
- `patch_*.py` is gitignored in every repo

---

## Commits

- Small and atomic — one logical change per commit
- The message explains the *why*, not just the *what*
- Dead code removal gets its own commit
- Checks and fixes are separate commits
- Never push without a clean `tsc`
- Never push with a failing pipeline

---

## Checks

- A new invariant runs against reality first — expect calibration
- First-run findings are usually real, but verify before acting
- Collapse noisy `NOTE` lists into counts, put the detail behind `--verbose`
- Known gaps are tracked explicitly, never left as failing checks
- A check that screams at clean code gets muted; a quiet check gets trusted
---

## Tone

- No ceremony. Get to the point.
- Don't over-explain. Assume fluency.
- If a decision is needed, present options. Don't decide unilaterally.
- If something is wrong, say so plainly. Don't soften.
- If a task needs the codebase open, ask for it. Don't guess at the answer.

---

## What I Expect From You

- Read the source before proposing fixes
- Ask for the specific file if you don't have it
- Abort a plan if you discover it's wrong mid-way
- Don't guess at root causes — investigate
- Flag uncertainty. Don't project confidence you don't have.

---

## What You Expect From Me

- Run commands and paste the output
- Push back when I suggest the wrong thing
- Tell you when you're wrong (it happens)
- Say "stop" when a session needs to end
- Don't let the AI take the wheel on decisions

---

## Conventions

- TypeScript with strict types. No `any` unless it's a documented escape hatch.
- **Zero-access encryption is non-negotiable.** The server never reads plaintext. If a feature needs content, it moves to the client or it retires.
- **The Accord is the constitution.** It bends features, not the other way round.
- **The LLM is a conductor, the browser is the executor.** The server relays; it doesn't compose.
- **Transparency is a first-class principle.** The LLM explains what it can and can't do, fluidly, without lecturing.
- **Small, honest artifacts.** A check that passes because it's meaningful, not because it's lenient. A plan that reflects reality, not intent. A commit message that says why, not what.

---

## When a Session Ends

- Everything is committed and pushed
- The pipeline is green
- The plan is honest — ticked items are actually done, open items are actually open
- Nothing is in flight
- Any lesson worth keeping has been written to Gov's memory

---

## How to Start a Session
To start a session:

    ssh bosly
    bosly

The second command prints everything a fresh chat needs: current
pipeline state, top open plan items, recent commits, last 5 memory
entries. Paste the output plus a short framing paragraph into a new
chat.

Then paste this file. The chat now has the state and the way.
Warm-up cost: about 30 seconds.

---

*Locked 18 September 2026. Living document.*

---

## Workflow

How a session actually runs.

**The founder brings facts. The chat reasons.**

- The founder runs shell commands in the terminal (`cat`, `grep`, `sed`,
  `psql`, `git`, `npx tsc`). The output is the ground truth about the
  state of the system.
- The founder pastes the output into a browser Claude session.
- The chat does the reasoning: reads, compares, proposes, drafts.
- Every command the chat proposes is meant to be pasted back into the
  terminal, run, and the output returned to the chat.

There is no separate "talk to Gov" step. Gov is the source of truth
for state (plan, memory, checks, code), read via filesystem commands.
The chat is the interface.

**Bosly Gov's own Copilot** (via `routers/direct_llm.py` on
localhost:3102) exists and works. Its UI is localhost-only, so it is
reachable from the founder's Mac only via an SSH tunnel:

    ssh -L 3102:localhost:3102 bosly

then browse `http://localhost:3102` on the Mac. Using Gov's Copilot
improves it over time — this is deliberate. It is the teaching loop.

**Trust contract reminders that apply to the workflow itself**

- Nothing changes on the box without the founder running the command.
- The chat drafts; the founder executes.
- Every non-trivial change is backed up before being applied.
- Every change is verified by running a check or a test after.

**Where things live**

- Accord (the main app): `/home/bosly_accord/bosly-1.0`
- Keep (the second app): `/home/bosly_accord/bosly-keep`
- Gov (the custodian): `/home/bosly_accord/bosly-gov`
- Plan: `/home/bosly_accord/bosly-gov/PLAN.md`
- Memory: `/mnt/bosly/bosly-data/copilot-knowledge/<slug>/memory.json`
- Reports: `/mnt/bosly/bosly-data/reports/YYYY-MM-DD/`
- Data: `/mnt/bosly/bosly-data`

**Orientation command**

Type `bosly` to print a summary: pipeline state, top open plan items,
recent commits, recent memory, locations. Paste that output at the
start of a new chat.

---

## The Teaching Loop

Bosly Gov's Copilot is not a static tool. It improves the more it is
used, and this is deliberate, not incidental.

**How the loop works**

- Every prompt sent to Gov's Copilot, whether through the SSH-tunnelled
  UI at `http://localhost:3102` or through the terminal, is a teaching
  moment.
- Gov reads files on demand (its `read_on_demand_context` extracts paths
  from the message and loads them into the LLM prompt). The more files
  it reads, the better it understands the codebase.
- Every response is logged to
  `/mnt/bosly/bosly-data/.data/governor/gov-interactions.jsonl` with the
  mode (claude or civo), a preview of the question, and the length of
  the answer. That log is itself a record of how the system is learning.
- Session context that Gov helps produce — plans, memory entries, check
  designs — feeds back into Gov's next session as source of truth.

**When to use it**

- When you want a second opinion on a design decision.
- When you want to ask Gov a question that requires reading several
  files at once (the UI's file-reading is stronger than the terminal's
  for this).
- When you want to log a decision: the interaction log preserves what
  was asked and roughly what was answered, so a future session can see
  the reasoning.

**When not to bother**

- When you're already in a session with another Claude (like the browser
  session). The reasoning is equivalent; adding Gov to the loop is
  overhead unless it has specific knowledge the other instance lacks.
- When the question is a terminal command. Just run the command.

**The point**

Gov's job is to be the custodian of the integrity of Bosly. That job is
learned, not assumed. Every session that uses Gov's Copilot moves it
closer to being able to reason about the codebase without a human in the
loop. That is the long-term direction: reduce reliance on external LLMs
by building internal context. See the "Evolve" section of PLAN.md.

**The pattern that matters**

When a check is added, a memory entry written, or a plan item ticked,
ask: does Gov now know something it didn't know before? If yes, the
loop is working. If the same class of bug appears again and Gov's
Copilot doesn't catch it, the loop is failing — not the Copilot.
