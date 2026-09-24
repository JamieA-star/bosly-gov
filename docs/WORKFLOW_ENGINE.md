WORKFLOW ENGINE MAP
===================

Created 24 September 2026.
Companion to the Accord. A working document, not a constitution.

The five metadata-only patches landed the same day (see the
app repo commits for detail). Five workflows reduced to
metadata. Three browser moves remain. One design decision
remains (scan-inbox Phase 1).

---

WHAT THIS IS

Bosly's server-side workflows answer questions about the user's
business without reading content. This document records what each
workflow computes, what it currently reads, and what it should read.

The decision that runs through all of them: names are metadata,
content is encrypted. The server holds the shape of the user's
business — who they work with, when, how often, what's outstanding.
It does not hold the substance — what was said, what was charged,
what was written.

---

THE THREE CATEGORIES

Metadata — always plaintext on the server.
  Statuses, dates, IDs, counts
  Names (contact names, client names on calendar events)
  Categories, flags, priority levels
  Booleans (paid, done, read)

Content — always encrypted client-side.
  Descriptions, notes, bodies of text
  Amounts, prices, totals
  Titles of events, subjects of emails
  Locations
  Line items
  Any user-written prose

The rule: metadata can be counted, filtered, sorted, and compared.
Content cannot. If a workflow needs to read a content field to do
its job, the workflow moves to the browser.

---

THE TRANSPARENCY STATEMENT

The user-facing version of this decision. It appears in the FAQ,
the transparency page, and the marketing.

  What the server can see.

  The server holds the shape of your business — your clients'
  names, when you meet them, how often you're in touch, what's
  overdue, what's paid. It cannot see the substance: what you
  discussed, what you charged, what you wrote in your notes, the
  contents of your emails, or the details of any invoice.

  Names are metadata. The reasoning: Bosly needs to know that
  Jane is overdue for a follow-up. It doesn't need to know why.
  The name identifies. The content explains. Only one of those
  is yours alone.

  Every field on every pill is categorised. Content is encrypted
  on your device before it reaches us. Metadata is not. The line
  between them is written down in the Accord, Part III.

---

THE TEN WORKFLOWS

Ten workflows exist today. Seven are API routes. Three are
fast-paths in the chat route.

Each entry below records: what it computes, what it currently
reads, and the verdict.

---

1. briefing
   File: app/api/bosly/briefing/route.ts

   Computes: today's appointments, this week's upcoming events,
   overdue invoices, draft invoice count, unread email count,
   pending task count, weekly hours, quiet contacts.

   Currently reads:
     CalendarEvent.title, clientName, location, startTime,
     endTime, isDone
     Invoice.invoiceNumber, status, dueDate
     Card.status
     Contact.name, lastContactAt
     Inbox cache seen flag

   Verdict: REDUCE. Remove title and location from calendar
   reads. clientName stays (metadata). The pill looks up titles
   and locations from the browser's local cache.

   After:
     select: { id, startTime, endTime, clientName, isDone }

---

2. check-conflict
   File: app/api/bosly/check-conflict/route.ts

   Computes: whether a proposed event overlaps existing ones;
   whether there are tight gaps (<30 min) between events.

   Currently reads:
     CalendarEvent.id, title, startTime, endTime, clientName,
     location

   Verdict: REDUCE. Remove title and location. The overlap and
   gap computations use only time fields. Response gains
   beforeId and afterId (event IDs) instead of titles; the pill
   resolves the names.

   After:
     select: { id, startTime, endTime, clientName }

---

3. relationships
   File: app/api/bosly/relationships/route.ts

   Computes: per-contact event count, days since last contact,
   quiet/new flags. Summary: total, active, quiet, new.

   Currently reads:
     Contact.id, name, email, hourlyRate, lastContactAt,
     createdAt, isBusiness, notes
     CalendarEvent.clientName, startTime

   Verdict: REDUCE. Remove email, hourlyRate, notes from the
   response. name and clientName stay (metadata). This workflow
   is the strongest justification for names as metadata — it's
   entirely about who you know, not what you said.

   After:
     Contact: { id, name, lastContactAt, createdAt, isBusiness }
     CalendarEvent: { clientName, startTime }

---

4. wellness-check
   File: app/api/bosly/wellness-check/route.ts

   Computes: overcommit warning (week hours > 40); frequent-
   reschedule warning (event updated 3+ times this week).

   Currently reads:
     CalendarEvent.id, title, clientName, startTime, endTime,
     updatedAt

   Verdict: RE-GROUP. The overcommit check needs only time
   fields — remove title. The reschedule check currently groups
   by title (content). Re-group by clientName (metadata). The
   message becomes "You've rescheduled Jane 5 times this week"
   instead of "You've rescheduled 'Kitchen refit visit' 5 times."

   Design decision: the client-name grouping is arguably more
   useful — it surfaces the relationship pattern, not the
   specific meeting. The signal is "I keep moving this person",
   not "I keep moving this meeting."

   After:
     select: { id, startTime, endTime, clientName, updatedAt }

---

5. scan-inbox
   File: app/api/bosly/scan-inbox/route.ts

   Computes: findings from recent emails (receipts,
   appointments, urgent items, commitments). Two phases:
   pattern matching on subject line, then LLM deep scan.

   Currently reads: email subject, from, date.

   Verdict: PARTIALLY FIXED 24 Sept, BLOCKED on inbox migration.

   Problem A (SOLVED): Phase 2 sent email metadata to OpenAI.
   Contradicted the 24 Sept decision (no cloud AI). Removed in
   commit fix(scan-inbox): remove Phase 2 LLM call.

   Problem B (BLOCKED): Phase 1 pattern-matches against
   plaintext email subjects. Subjects are content.

   New understanding: the inbox cache is encrypted at rest with
   a SERVER-SIDE key (ENCRYPTION_KEY), not the user's vault key.
   The server can read every subject. So the scan is server-side
   for now because that's where the data is readable.

   Making Phase 1 browser-side requires the inbox to be
   encrypted with the user's vault key first. That is the inbox
   pill migration, tracked as accord.encrypt_all_pills (Inbox).

   Until then: Phase 1 runs server-side on subjects the server
   can read anyway. Removing the LLM call was the win. Moving
   Phase 1 to the browser is part of the inbox migration.

---

6. preferences
   File: app/api/bosly/preferences/route.ts

   Computes: user's saved preferences (GET), saves new ones
   (POST), removes them (DELETE).

   Currently reads: MemoryFact.fact where category = "preference".

   Verdict: FULLY CONTENT-DEPENDENT. The MemoryFact.fact column
   is plaintext prose. Every read/write here is content.

   This workflow must move to the browser. The browser stores
   preferences in the encrypted memory path. The workflow engine
   asks the browser for preferences when it needs them.

   Additional problem: this route bypasses yesterday's neutering
   of saveFact/recallFacts/forgetFact in lib/chat/memory.ts.
   Those functions are now no-ops, but this route accesses
   MemoryFact directly. Inconsistent.

---

7. enrich-contacts
   File: app/api/bosly/enrich-contacts/route.ts

   Computes: signature extraction from email bodies. Suggests
   new contacts or contact enrichments.

   Currently reads: email body (full text).

   Verdict: FULLY CONTENT-DEPENDENT. Email bodies are the most
   sensitive content in the app. Signature parsing requires
   reading the body.

   This workflow must move to the browser. The browser fetches
   emails, parses signatures locally, and sends only the
   extracted result to the server ("found: Jane Smith, Acme
   Ltd, +44…").

   The signature-parsing code moves to the browser. It's already
   pure — no server dependencies.

---

8. "What's on today?"
   File: lib/chat/helpers.ts (fast-path)

   Computes: today's or this week's events, formatted as a list.

   Currently reads: CalendarEvent.title, startTime, clientName,
   location, isDone.

   Verdict: REDUCE. Remove title and location from the select.
   The chat response becomes "3 appointments today" rather than
   listing each. Or, if the user wants detail, the browser opens
   the calendar pill.

---

9. "How many hours?"
   File: lib/chat/helpers.ts (fast-path)

   Computes: total hours booked in the next 7 days.

   Currently reads: CalendarEvent.startTime, endTime.

   Verdict: CLEAN. Already metadata-only.

---

10. "Any overdue invoices?"
    File: lib/chat/helpers.ts (fast-path)

    Computes: list of overdue invoices by number and due date.

    Currently reads: Invoice.invoiceNumber, status, dueDate.

    Verdict: CLEAN. Already metadata-only, with a comment
    explaining why. This is the reference implementation — the
    pattern the other workflows should follow.

---

SUMMARY

  1. briefing            REDUCE (2 fields)
  2. check-conflict      REDUCE (2 fields)
  3. relationships       REDUCE (3 fields)
  4. wellness-check      RE-GROUP by clientName
  5. scan-inbox          REMOVE LLM; move Phase 1 to browser
  6. preferences         MOVE to browser
  7. enrich-contacts     MOVE to browser
  8. What's on today?    REDUCE (2 fields)
  9. How many hours?     CLEAN
 10. Any overdue?        CLEAN

Four small patches. One design decision. Three browser moves.

---

THE PATCHES (do first, small)

Patch 1 — briefing
  Remove title and location from both calendar selects.

Patch 2 — check-conflict
  Remove title and location. Response returns beforeId/afterId
  instead of before/after.

Patch 3 — relationships
  Remove email, hourlyRate, notes from both the contact select
  and the response.

Patch 4 — wellness-check
  Remove title from both selects. Group the reschedule check by
  clientName instead of title. Reword the message.

Patch 5 — "What's on today?" fast-path
  Remove title and location. Return counts and times.

Each patch is one commit. All five are 1-2 hours of work total.

---

THE BROWSER MOVES (do after)

Move 1 — scan-inbox
  STATUS: Partial. LLM call removed 24 Sept.
  REMAINING: Depends on the inbox pill migration. Once the
  inbox cache is encrypted with the user's vault key, Phase 1
  moves to the browser. Until then, Phase 1 stays server-side.
  Not an independent move — part of accord.encrypt_all_pills
  (Inbox).

Move 2 — preferences
  Remove the server route. Browser stores preferences in
  encrypted memory. Engine asks browser.

Move 3 — enrich-contacts
  Move signature parsing to the browser. Server receives only
  extracted results.

Moves 2 and 3 are independent and can proceed.

Move 1 is blocked. It will happen as part of the inbox
migration, not as a separate piece of work.

---

THE DESIGN DECISION (pending)

scan-inbox Phase 1 — do email subjects stay plaintext
(enabling server-side pattern matching) or move to the browser?

Lean: move to browser. Subjects are not reliably metadata.

Decide before Move 1.

---

THE ENGINE (after the patches and moves)

Once the ten workflows are metadata-only or browser-side, the
workflow engine formalises them.

The shape:

  One module (lib/workflow/) with a common interface
  Each workflow is a function: (input, context) -> outcome
  The engine classifies intent, routes to a workflow, returns
    the outcome
  When a workflow needs content, it returns a vault_request that
    the browser fills in
  When a workflow needs language (future), it returns a
    language_request that the local model fills in

The chatbot becomes one caller of the engine. The Active pill
becomes another. Every scheduled job becomes another.

Not designed here. This document is the map. The engine design
follows once the patches and moves are done.

---

WHAT THIS DOCUMENT COMMITS TO

1. Names are metadata. Stated plainly, and the reason given.
2. Content is encrypted. No exceptions.
3. The line is written down. Every field on every pill is
   categorised in the Accord, Part III.
4. The user is told. The transparency statement appears in the
   FAQ, the transparency page, and the marketing.

This is a promise. The workflows are the code that keeps it.
