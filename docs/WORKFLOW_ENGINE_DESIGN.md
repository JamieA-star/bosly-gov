WORKFLOW ENGINE DESIGN
======================

Created 24 September 2026.
Companion to the workflow map (WORKFLOW_ENGINE.md) and the
Accord. This document describes how the engine is built, not
what it does.

---

WHAT THIS IS

The workflow engine is the deterministic layer between the
user and their data. It answers questions about metadata —
counts, statuses, dates, categories — without reading content
and without calling an LLM.

It replaces chatWithTools. There is no LLM in the loop. The
tool-calling architecture is retired. In its place: an intent
classifier, a catalogue of workflows, and a response format.

The chatbot becomes one interface to this engine. The Active
pill becomes another. Every scheduled job becomes another.

---

THE THREE LAYERS

Tier 1 — Workflow (server, deterministic).
  The engine. Classifies intent. Routes to a workflow.
  Answers from metadata. Returns a response.

Tier 2 — Vault (browser, on demand).
  Called when a workflow needs content. The browser
  decrypts, computes, returns an outcome.

Tier 3 — Language (future local model).
  Called when a workflow needs phrasing. The model
  returns text. The reasoning stays in Tier 1.

Rule: use the lowest tier that can answer.

---

THE MODULE

Everything lives in lib/workflow/:

  index.ts          — the engine entry point
  classify.ts       — intent classification
  catalogue.ts      — the list of workflows
  types.ts          — shared types

  workflows/        — one file per workflow
    today.ts
    hours-this-week.ts
    overdue-invoices.ts
    briefing.ts
    check-conflict.ts
    relationships.ts
    wellness-check.ts
    scan-inbox.ts
    enrich-contacts.ts

  bridges/
    vault.ts        — how a workflow asks the browser
    language.ts     — how a workflow asks the future model

The engine is stateless. It reads from the metadata tables
and calls the vault bridge when needed. It does not cache.

---

THE WORKFLOW INTERFACE

Every workflow is a function with the same shape:

  type WorkflowInput = {
    userId: string;
    message: string;          — the user's original text
    params: Record<string, unknown>; — extracted from classify
  };

  type WorkflowOutcome =
    | { kind: "answer"; text: string }
    | { kind: "vault_request"; request: VaultRequest }
    | { kind: "language_request"; request: LanguageRequest }
    | { kind: "cannot_help"; reason: string };

  type Workflow = {
    id: string;
    match: (message: string) => boolean;
    run: (input: WorkflowInput) => Promise<WorkflowOutcome>;
  };

The engine calls `match` to see if a workflow applies. Then
`run` to get an outcome. The outcome is either:
  - A direct answer (no content needed)
  - A request to the browser for content
  - A request to the local model for phrasing
  - A "cannot help" so the engine falls through

---

THE CLASSIFIER

classify() takes the user's message and returns a ranked
list of workflow IDs to try. It does not pick one. The
engine tries them in order until one matches.

The classifier is a rewrite of the current
classifyIntent() in lib/chat/helpers.ts. Same idea, wider
coverage. It recognises:

  - Direct questions ("how many overdue invoices?")
  - Greetings ("good morning" → briefing)
  - Actions ("create an invoice" → draft workflow)
  - Disruption signals ("can't make it" → reschedule workflow)

It does not use an LLM. Pattern matching and keyword
extraction only.

---

THE ENGINE FLOW

  1. Message arrives at /api/chat.
  2. classify() returns a ranked list of workflow IDs.
  3. Engine tries each workflow's match() in order.
  4. First matching workflow runs.
  5. Workflow returns an outcome:
     a. answer          → sent to the user.
     b. vault_request   → engine asks the browser, browser
                          returns outcome, workflow runs again
                          with the outcome in params.
     c. language_request → engine asks the model, model
                          returns text, workflow returns
                          answer.
     d. cannot_help     → engine tries the next workflow.
  6. If no workflow matches, engine returns:
     "I can't help with that yet. Here's what I can do:
     [list]. If you want to do it yourself, [nearest pill]."
  7. Unknown intent is logged to
     /mnt/bosly/bosly-data/.data/governor/unknown-intents.jsonl
     for future workflow additions.

---

THE VAULT BRIDGE

When a workflow needs content, it returns a vault_request:

  type VaultRequest = {
    action: "count" | "sum" | "fetch" | "draft" | "open";
    target: string;         — "invoices", "contacts", etc.
    filter?: Record<string, unknown>;
    field?: string;         — for sum
    template?: string;      — for draft
    context?: Record<string, unknown>;
  };

The engine sends this to the browser through the chat stream.
The browser executes against its local (decrypted) data. The
browser returns an outcome:

  type VaultOutcome = {
    ok: boolean;
    result?: number | string | Record<string, unknown>;
    action?: string;
    error?: string;
  };

The engine passes the outcome back to the workflow, which
runs again with the outcome in params. The workflow decides
whether to answer, request more, or defer to language.

---

THE LANGUAGE BRIDGE

When a workflow needs phrasing, it returns a
language_request:

  type LanguageRequest = {
    intent: string;          — what the workflow is trying to say
    context: Record<string, unknown>;
    constraints?: {
      maxLength?: number;
      tone?: string;
    };
  };

The engine calls the local model (when it exists). The model
returns text. The workflow wraps it in an answer.

For now: the language bridge is stubbed. It throws
"language_not_available". Workflows that need phrasing return
a plain-language answer instead, generated from the outcome
by a deterministic formatter.

When the model exists, the stub becomes a real call. The
workflows don't change.

---

THE RESPONSE FORMAT

The engine returns a single string to the chat route. The
string is the message the user sees.

It is composed from the workflow's outcome, formatted by:
  - The workflow's own formatter (deterministic), OR
  - The language bridge (when the model exists)

Same shape either way. The user doesn't know which was used.

---

WHAT THIS REPLACES

  lib/chat/helpers.ts — chatWithTools is retired.
    classifyIntent moves to lib/workflow/classify.ts.
    The fast-paths become workflows.
    The LLM tool loop is removed.
    The memory context loading is removed (memory was
    neutered 24 Sept).

  app/api/chat/route.ts — the tool definitions are removed.
    The route becomes: get message, call engine, return
    response. Much smaller.

  The chat prompt — no longer needs the schema block, the
    endpoint list, the tool descriptions. It becomes a short
    prompt describing the engine's capabilities.

---

WHAT THIS DOES NOT REPLACE

  The workflows themselves — they already exist as routes
    and fast-paths. The engine calls them. Their logic is
    unchanged. Only their interface changes (they become
    functions in lib/workflow/workflows/, not API routes).

  The vault — the browser-side encryption. Untouched.

  The pill UI — unchanged. The workflows read the same
    metadata, the pills read the same content.

---

THE FIRST THREE WORKFLOWS

Not all ten at once. Start with three:

  1. today             — "what's on today?"
  2. hours-this-week   — "how many hours this week?"
  3. overdue-invoices  — "any overdue invoices?"

Why these three:
  - They're the cleanest (already metadata-only)
  - They cover the three shapes (list, count, count)
  - They prove the engine without needing the vault bridge
  - They're the reference implementations

Once those three run through the engine, the pattern is
proven. The other seven follow.

---

WHAT THIS DOES NOT SOLVE

  Memory — retired. If a memory system is designed later,
    it goes in the browser, encrypted.

  Drafting — needs the local model. Deferred.

  Ambiguous requests — needs the local model. Deferred.

  Unknown intents — logged, not answered. The catalogue
    grows when real use shows what's needed.

---

ESTIMATE

  Design: this document. Done when it's reviewed.
  Build the engine skeleton: half a day.
  Build the first three workflows: one day.
  Wire it into /api/chat: half a day.
  Test end to end: half a day.

Total: 2-3 focused days for the first working version.

The other seven workflows: one per session.

---

WHAT THIS DOCUMENT COMMITS TO

1. The engine replaces chatWithTools. No LLM in the loop.
2. Every workflow has the same interface.
3. Unknown intents are logged, never guessed.
4. The vault bridge is a small protocol, not a rewrite.
5. The language bridge is stubbed until the model exists.
6. The first three workflows are today, hours-this-week,
   overdue-invoices.

The engine is small. The workflows are small. The whole
thing is a rebuild of what already works, with a cleaner
interface and no LLM.

---

END OF DESIGN
