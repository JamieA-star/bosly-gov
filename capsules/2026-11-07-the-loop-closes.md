# Capsule — 7 November 2026 (the loop closes)

**Session name:** The loop closes
**Shape:** The corpus became a record you can cite, a build began writing to
it, and the spec began reading from it. One build ran. The loop that makes
every build cheaper than the last is closed — and it was closed by six
patchers, five of which were wrong the first time.

---

## What happened

The session opened on a plan item: the learning loop, designed but not built.
The design was three options — offered, staging, automatic — and it was
wrong. Reading the source found the real shape: the question email already
exists, in `scripts/night_build.py`, and it already tells the founder a build
has parked. What did not exist was the other half — a build writing back.

The session turned from a staging file and a promote tool to the corpus that
already exists. Memory holds every lesson, every decision, every build. It
was the right store, and it had never been read by a build or written by one.

Then the rule. `memory_schema` checked that fields existed; it never looked
at what an id was. Seven entries were unciteable — five real records with a
bad id, one a `"placeholder"`, one a fact with a build prefix. All seven are
fixed, and the rule is now `{type}-{YYYYMMDD}-{slug}`, with a synthetic hash
probe so a bad id cannot pass even when the corpus is clean.

A build writes its lesson: `record_lesson`, a dated, named `build` entry in
the same store the founder keeps by hand. Every build ends with that step —
`new_build` appends it at the door, next to the base gate, so no caller
remembers and no build finishes without it.

The spec reads back: decisions the founder marks `universal` are composed
into every spec, between the base and the build's own questions, newest
first, capped at 12. The base is the floor and is unconditional; the
universal decisions are judgment and are capped. Without the cap the spec
grows with the learning and the cost rises as the system gets smarter.

One build ran, the `new_build` build from the previous session, and it ticked
on a check's output. The tier closed 62 passed, 1 failed — the red is
`accord.invariants`.

## What was built

- `memory_schema`'s id rule, with a synthetic probe. Seven entries renamed or
  removed; the corpus is citeable.
- `record_lesson` — a build writes its lesson, dated, named, typed `build`.
- `new_build` appends the lesson step at the door. Every build ends with it.
- `write_spec` composes universal decisions, newest first, capped at 12.
- Three checks: `a_build_writes_its_lesson`,
  `every_build_ends_with_the_lesson_step`,
  `the_spec_inherits_universal_decisions`.
- Commits `198f267`, `f67b1e9`, `eeee2dc`, `8eb3c9d`.

## What went wrong, and what it taught

Six patchers were written from remembered code. `pathlib` twice, a gate
block, a `write_spec` anchor, a check's line 43, a `remove_probe` anchor.
Every one was caught — by an abort or a red check — and none by reading the
file first. The memory pattern
`a-patcher-reads-the-file-before-it-writes` existed and was not followed.

The check that crashed taught the sharper lesson: it asked `record_lesson`
for an entry, then searched the corpus for the name it had passed, while the
function wrote a sanitised id that did not contain it. The entry existed; the
check looked for the wrong string. A test asks the function what it wrote,
then verifies that thing.

And a check that raises `KeyError` on its expected-red path hides its own
red. `write_spec` creates a directory and a spec but no `state.json`; a spec
can exist for a thing that is not a build. The crash found the hole.

## The numbers

Tier 62 passed, 1 failed — `accord.invariants`. Memory 245, 0 malformed.
PLAN.md 96 open, 154 done. Four commits. One build run, one step, ticked on
its check.

## The lesson

The corpus is the system. A build writes to it, the spec reads from it, and
the rule keeps it citeable. The cap keeps it honest. And a patcher reads the
file before it writes — six misses is not a lesson, it is a step.

## What's next

1. `gov.a_spec_without_a_state_is_not_a_build` — the door refuses, or
   `write_spec` creates the state.
2. `gov.the_corpus_is_outside_git` — the training set and the ICO record has
   no deliberate backup. Test the restore.
3. `gov.a_patcher_reads_before_it_writes` — the agreement gains the step:
   print imports and anchors before writing.
4. `accord.invariants` — the invoice auth red, open since 4 November.
5. The receptionist — the first build on a foundation that learns.
