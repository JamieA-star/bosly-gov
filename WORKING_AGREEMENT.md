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
