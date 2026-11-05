# Capsule — 5 November 2026 (the base spec)

**Session name:** The base spec
**Shape:** One plan item closed — the five standing decisions every build
inherits — and one regression caught by the tier: a gate that landed in
the wrong place and re-parked a finished build.

---

## What happened

The handover left the base spec as the next item: the five decisions
every build inherits, written so a check could assert them. The chat's
first read found the flaw before a line was written — the handover's
five included the budget rule, which is a fact about the loop, not an
instruction to a build. It was replaced with a build-actionable fifth:
a step's check is registered under its check_id and prints its proof.

The check was written first, and passed standalone: write_spec was
called on a throwaway build, the produced spec asserted against the
base, the probe torn down in a finally. Then write_spec was patched to
compose the base in, load_build was patched to return an empty spec
instead of raising, and a gate was added to run_build: a runnable build
whose spec lacks the base parks with a question.

The gate landed before the terminal-status return, and the tier caught
it. build_loop_stops went red — a probe build with a pre-base spec was
re-parked with the migration-guard question instead of the question its
stub model asked. The gate moved after the terminal-status return, the
probe was rewritten through write_spec, and the tier closed 58/1.

## What was built

- specs/base.md — the five standing decisions.
- write_spec composes one spec: goal, base, the build's own, permissions,
  escape hatch. One file, one read.
- _load_base_spec, shared by the gate and the check — one predicate.
- The gate in run_build, after the terminal-status return.
- checks/a_build_starts_from_the_base_spec.py, green in the tier.

Six commits, 7dfe96c..98b5794.

## What went wrong, and what it taught

The gate's placement. A gate exists to stop a build that would otherwise
run. Placed before the terminal-status return, it overwrote the reason a
finished build had stopped. build_loop_stops caught it; the tier caught
it. A check written for one failure caught a different one.

Two patchers ran against assumed state instead of reading it: one used
pathlib where the module imports Path, one tried to move a block an
earlier run had already moved. Both aborted or were caught; neither
damaged the tree. Anchors prove the edit lands — reading proves it is
needed.

One anchor carried an em-dash the file did not, and the patcher aborted
on a false negative. A correct file looked unpatched.

## The numbers

Tier 58 passed, 1 failed — the red is accord.invariants, the known
invoice auth test, not the build loop. Six commits. Memory 241 entries.
The base spec's own check runs in 36ms.

## The lesson

A gate belongs after the terminal return, and a patcher reads the file
before it writes.

## The second build, same night

The new_build build was created and run after the base spec closed. It
was one step, on an 80p budget, and it ticked on the check's own output:
new_build now refuses a build with no spec, or a spec without the five
standing decisions, naming write_spec. build_start keeps its signature;
its contract becomes write_spec first.

Its own lesson was paid immediately. The recreate deleted the build
directory — and the spec with it — so new_build wrote the stub "ignored".
The fix was write_spec, then new_build, then confirm the base before the
run. A spec lives in the build directory; write_spec is the only writer,
and a recreate is no exception.

Two more handover claims did not survive the source: pathlib where the
module imports Path, and build_quote, which does not exist. budget_rule
does. A budget with no quote behind it is a number with no basis —
gov.build_quote_is_missing is open for it.

The tier closed 59 passed, 1 failed: the red is accord.invariants. Memory
243, 0 malformed. Commits 60906bc and cae809b.

## What's next

1. gov.new_build_bypasses_the_base — new_build writes a spec without the
   base; delegate it to write_spec.
2. gov.the_batch_is_a_policy_not_a_flag — should_batch(steps), shared by
   run_build and the night job. Parked until a build is long enough.
3. The receptionist — the spec exists, from an earlier attempt; verify it.
4. accord.invariants — the invoice auth red.
