# BOSLY ACCORD v1.4.0

*Ratified: May 13, 2026 | Amended: May 30, 2026 | Revised: September 24, 2026*

---

## PREAMBLE

Bosly is a private workspace for freelancers, sole traders, and self-employed
people — particularly those with ADHD. Calendar, email, invoices, contacts,
finances, health, and social media in one calm place. Messages come in, Bosly
organises them, they become tasks, cards, or conversations, and the user acts.

Beneath that description is the real architecture: Bosly is a liberation engine
disguised as a productivity app. The mission is to empower every individual to
control their own data. Not a government database. Not a corporate cloud. Not
even Bosly's creator. The user is sovereign. Bosly serves.

This accord defines what Bosly is, what Bosly stands for, and what Bosly will
never do. Part I describes what Bosly is becoming. Part II is the
non-negotiables. Part III is where Bosly is today — the honest gap between
the target and the current state. Part IV is what's planned. Part V is how
this document can change.

There are two ways to use Bosly:

**Bosly** — Free. Five pills: Active, Contacts, Calendar, Health,
Invoicing. A real workspace a freelancer can run their business on,
forever. Encrypted client-side. No tracking, no ads, no expiry.

**Bosly Accord** — £25/month. The full workspace: all ten pills.
Active, Contacts, Calendar, Health, Invoicing, plus Inbox, Finance,
Social, Data health, and the chatbot. Replaces five or six separate
apps. Encrypted end to end. Sovereign by design.

Neither tier includes a cloud AI provider. The AI features described
in Part IV will arrive when Bosly runs its own model on its own
hardware. They are an addition to the £25 tier, not its reason. The
£25 tier's value is the whole workspace and the data protection that
holds it together.

The governance accord (this document) applies to both.

---

# PART I — WHAT BOSLY IS

*Every statement in Part I is true today. The compliance check verifies these
against the code.*

---

## ARTICLE I — SOVEREIGN DATA ARCHITECTURE

### 1.1 Zero-Access Encryption

Every piece of user data is encrypted on the user's device before it reaches
Bosly's server. The server stores ciphertext only. Bosly's creator,
administrators, and infrastructure providers cannot read user data. This is
not a promise — it is a mathematical constraint.

**Encrypted on the client before storage:**
- Contact details (names, email addresses, phone numbers, addresses)
- Calendar events (titles, descriptions, locations, attendees)
- Invoices and line items
- Financial transactions and tax records
- Health records, appointments, medications, blood tests
- Chatbot conversations with Bosly
- Tasks, cards, and project data

**Stored in plaintext (operationally necessary):**
- Email address (login and notifications)
- Subscription tier (free or Accord)
- Encrypted data blobs (unreadable without the user's key)
- Session metadata (created at, last active)

**Not stored at all:**
- The recovery phrase
- The encryption key
- The PIN used for the backup

### 1.2 Key Architecture

Each user generates their encryption keys during the key ceremony, in the
browser, using the Web Crypto API.

- **AES-256-GCM** for symmetric encryption of stored data
- **HKDF** for key derivation from the recovery phrase
- **PBKDF2** (210,000 iterations) for the PIN-encrypted backup of the phrase
- **IndexedDB** for client-side key storage

The recovery phrase is 24 words. It encodes the user's keys. The phrase itself
never leaves the browser. It is presented once, during the ceremony, and is not
stored by Bosly.

Not every category of user data is yet behind client-side encryption. Invoices
and health records are. Contacts, calendar, cards, finance, conversations, and
client patterns are stored plaintext today. The migration to bring them behind
encryption is tracked as `accord.encrypt_all_pills`. See Part III for the
current state and Part IV for the plan.

The PIN backup is optional. It encrypts the recovery phrase with a 6-digit PIN
in the browser, then sends only the ciphertext to the server. If the user loses
their device, they can recover with the PIN — or with the phrase itself.

**If both the recovery phrase and the PIN are lost, the encrypted data is
unrecoverable.** Bosly cannot help. This is the price and the proof of
sovereignty.

### 1.3 Duress Mode

Users may generate a duress phrase in settings. If the user is forced to open
Bosly under pressure, entering the duress phrase unlocks a decoy vault instead
of the real one. The real vault stays hidden.

Duress mode exists to protect people operating under coercion — journalists,
activists, people in unsafe domestic situations, and anyone facing oppressive
regimes.

### 1.4 Server Architecture

Bosly runs on a self-hosted server in the United Kingdom, controlled by its
creator. The server holds ciphertext, handles authentication, and routes
requests. It cannot decrypt user data.

### 1.5 Creator Access Limitations

The creator cannot access user data. The architecture prevents it. There is no
admin backdoor, no master key, no override capability. Even with full server
access, all user data is ciphertext.

**The creator can:**
- See user count and database size
- Delete accounts (destroying ciphertext)
- Maintain server uptime and apply security patches
- Run governance checks against the system

**The creator cannot:**
- Read any user's messages, contacts, calendar, tasks, invoices, or health
  records
- Recover a lost recovery phrase
- Decrypt data in response to legal demands
- Access data for debugging without the user's explicit, temporary consent

### 1.6 Data Retention

When a user deletes their account, all rows tied to that account are deleted
in a single database transaction — either everything goes or nothing does. The
email address and a deletion record are retained for compliance.

---

## ARTICLE II — USER IDENTITY AND ACCESS

### 2.1 Account Creation

Users create an account with an email address and a password. The browser
offers to save the password. The password is a login credential, not an
encryption key; the encryption key is derived separately from the recovery
phrase.

### 2.2 Signup Flow

Landing page → email and password → account created → key ceremony (recovery
phrase generated, backup PIN set) → workspace. The key ceremony includes a
disclaimer explaining what's about to happen, and the phrase is stashed in
session storage so the ceremony can be resumed if the tab is closed
accidentally.

### 2.3 Recovery

Two recovery paths exist:

1. **Recovery phrase.** The 24-word phrase reconstructs the user's original
   encryption key, byte for byte. This is tested every night by an automated
   check.
2. **PIN backup.** If the user set a PIN during the ceremony, the phrase was
   encrypted with it and stored server-side. Entering the PIN decrypts it in
   the browser and restores the vault.

Bosly does not store the recovery phrase. Bosly cannot recover it. If both the
phrase and the PIN are lost, the data is irrecoverable.

### 2.4 Recovery Phrase Verification

Bosly asks the user to confirm three random words from the phrase during the
ceremony. This proves the user has written it down before proceeding.

---

## ARTICLE III — LEGAL COMPLIANCE

### 3.1 The Non-Negotiable Core

Regardless of jurisdiction, Bosly's encryption does not weaken. Bosly does not
implement backdoors. Bosly does not build key escrow. Bosly does not disable
encryption features based on location.

If a jurisdiction restricts strong encryption, Bosly warns the user. Bosly
does not geoblock. Bosly informs, and the user decides.

### 3.2 Legal Demands

If Bosly receives a legal demand for user data:

- Bosly can provide only: email address, subscription tier, and encrypted data
  blobs
- Bosly cannot provide plaintext because decryption is mathematically
  impossible without the user's keys
- Bosly maintains a warrant canary and transparency report
- Bosly publishes what it can where legally permitted

### 3.3 GDPR Compliance

Bosly follows UK GDPR principles. Users have the right to access, correct,
export, and delete their data at any time, from the settings page. Bosly is
not currently registered with the ICO; registration is planned.

Bosly is compliant by architecture:

- Data breaches reveal only ciphertext — not notifiable for content
- Subject Access Requests return ciphertext the user already possesses
- Right to erasure means deleting ciphertext, in a single transaction
- Data portability returns encrypted blobs the user decrypts with their own key

---

## ARTICLE IV — AI AND LEARNING

### 4.1 AI Processing

Bosly does not currently use any external AI provider. There is no cloud
LLM behind the chatbot. The chatbot is a deterministic workflow engine: it
answers questions about counts, statuses, dates, and categories using the
metadata the server holds in plaintext. It cannot read content, and it
cannot draft prose.

When Bosly runs its own model — after the hardware upgrade — the AI
features will be an addition to the £25 tier. The model will run on the
same infrastructure as the rest of Bosly. No user content will be sent to
any third party at any point. The workflow engine will call the model for
language tasks only: phrasing, drafting, understanding ambiguous requests.
The reasoning will remain deterministic and the content will remain in the
user's browser.

Until then, the chatbot tells the user plainly when it cannot help: "I
can't do that yet. But I can open the relevant view." No pretence that
something exists which does not.

### 4.2 Bosly's Learning

Bosly learns from the user's own data, on the user's own device, for that
user's benefit alone. Bosly does not train on aggregated user data. Bosly does
not harvest conversations for model improvement.

### 4.3 AI Provider Transparency

Bosly does not use any third-party AI provider. There is no Civo
dependency, no OpenAI dependency, no cloud LLM of any kind. When the local
model is ready, it will be described here and nowhere else. Until then,
this article describes a fact: no user data leaves Bosly's own
infrastructure.

---

## ARTICLE V — DATA AFTER CANCELLATION

### 5.1 Accord Cancellation

When a user cancels Bosly Accord:

- AI features stop at the end of the billing period
- All user data remains intact and accessible
- The free tier continues to work fully
- Encrypted data is retained

### 5.2 Account Deletion

Users may request immediate account deletion at any time. All ciphertext is
permanently destroyed, in a single transaction. Email address and deletion
record are retained for compliance.

---

## ARTICLE VI — TRANSPARENCY AND TRUST

### 6.1 Warrant Canary

Bosly maintains a public warrant canary at /transparency — a statement
affirming that Bosly has not received secret government requests for user
data. If the canary is not updated within 95 days, assume something has
changed.

### 6.2 Governance Checks

Bosly runs an automated governance pipeline nightly at 5am. The checks
currently include:

- **accord.invariants** — encryption recovery, deletion coverage, prompt
  route references, and the other code-level invariants
- **keep.invariants** — Keep's own invariant suite
- **gov.memory_schema** — memory files are well-formed
- **gov.consent_gating** — no changes without consent
- **gov.secrets_audit** — no secrets exposed
- **gov.cron_sanity** — every cron script can actually run

The pipeline is in `bosly-gov/manifests/checks.yml`. Results are written to
`/mnt/bosly/bosly-data/reports/`.

Accord compliance is not yet a check. The old `bosly-accord-check` was
retired in the commands cleanup on 17 September 2026 — and it was broken
(it referenced an EC2-era path that no longer exists). A new check,
`gov.accord_compliance`, is planned. It will verify Part III of this document
against the code — that the categories listed as encrypted actually are, and
that nothing claims a state it isn't in.

### 6.3 Honesty About State

Where Bosly describes itself — in this accord, in the marketing pages, in the
`llms.txt` file, in the FAQ — it states what is true today. Features not yet
built are listed in Part III. There are no false present-tense claims.

---

## ARTICLE VII — DESIGN PRINCIPLES

### 7.1 Calm by Design

Bosly's interface is calm: low noise, high clarity, deliberate spacing.
Single-surface workspace with expandable pills. No red alerts. No urgency
theatre. Time-aware greetings. Empty states that explain what goes where.

### 7.2 Honest Language

Bosly uses neutral, inclusive language. No gendered assumptions. No marketing
jargon. No "coming soon" where things aren't built. Features are either
working, planned, or not yet available — stated plainly.

### 7.3 Discovery, Not Selling

Users discover Bosly's capabilities through use. No popups. No onboarding
tours. No "upgrade now" banners. The Accord tier surfaces naturally when a
user tries an AI feature — with a calm explanation and a link to learn more.

---

## ARTICLE VIII — GOVERNANCE

### 8.1 Ownership

Bosly is creator-owned. No investors. No shareholders. No extraction. This
structure will transition to a steward-owned entity to ensure permanence
beyond the creator's lifetime.

### 8.2 The Governor

The Bosly Governor — Bosly Gov — is the custodian of the integrity of the two
production apps. It runs the nightly checks, holds the plan and the memory,
and reports when something is wrong. This accord, the plan, and Bosly's memory
are version-controlled.

### 8.3 Amendment Process

This accord is a living document. Amendments require proposal, deliberation,
ratification, and publication with a new version number and date. Amendments
must not contradict the core principles: user sovereignty, zero-access
encryption, and the liberation mission.

---

# PART II — WHAT BOSLY WILL NEVER DO

*These are the non-negotiables. They do not change with version. They do not
bend to features, jurisdictions, or business pressures.*

**Bosly will never:**
- Read user data in plaintext on the server
- Store a recovery phrase, encryption key, or PIN
- Implement a backdoor, key escrow, or admin override
- Weaken encryption based on the user's jurisdiction
- Train AI models on user data
- Sell, share, or trade user data with third parties
- Send an email on the user's behalf without explicit approval
- Delete data without the user's confirmation and a 60-second undo window
- Use dark patterns, urgency theatre, or engagement-maximising notifications
- Claim a feature works when it doesn't

---

# PART III — WHERE BOSLY IS TODAY

*The Accord describes what Bosly is becoming. This section describes what
Bosly is. It is updated as migrations land. The `gov.accord_compliance`
check verifies this section against the code.*

**As of 24 September 2026.**

### 3.1 Encrypted client-side

These categories of user data are encrypted in the browser before storage.
The server holds only ciphertext.

- **Invoices and line items** — clientName, clientEmail, amount,
  taskDescription, businessName, lineItems[]
- **Health records** — appointments, medications, blood tests, symptoms,
  health passport
- **Chat memory** — the conversation history (ChatMemory.encryptedMessages)

### 3.2 Stored plaintext, migration planned

These pills still store content in plaintext. The migration to bring them
behind client-side encryption is tracked as `accord.encrypt_all_pills`.

The migration preserves the **metadata schema** — Category A (operational)
and Category B (analytical) fields — and encrypts everything else
(Category C, content). The rule: metadata can be counted, filtered, sorted,
and compared; content cannot.

- **Contacts** — plaintext: `status`, `kind`, `isBusiness`,
  `lastContactAt`. Content: name, email, phone, address, notes, company,
  title, value, hourlyRate.
- **Calendar events** — plaintext: `startTime`, `endTime`, `isAllDay`,
  `status`, `isDone`. Content: title, description, location, clientName,
  clientPhone, clientEmail, extras.
- **Cards and tasks** — plaintext: `status`, `priority`, `dueDate`,
  `dueAt`, `completedAt`. Content: title, description, context,
  AI-generated text, estimatedValue, metadataJson.
- **Finance transactions** — plaintext: `date`, `type`, `category`,
  `book`, `reviewed`. Content: description, amountPence, receipts, jobId.
- **Inbox** — plaintext: `date`, `accountId`, `isRead`, `hasAttachment`,
  `kind`. Content: subject, from, body, attachments. Most complex —
  inbound email is on the IMAP server.
- **Social** — plaintext: `platform`, `status`, `scheduledAt`. Content:
  content, media, hashtags, tone.

The migration is blocked on `accord.workflow_engine`. Each pill must be
migrated only after the workflow engine's metadata requirements for that
pill are finalised — otherwise the engine loses the context it uses to
help, and the encryption breaks the product.

### 3.3 The chatbot

The chatbot is not an LLM. It is an interface to the workflow engine — a
deterministic layer that answers questions about counts, statuses, dates,
and categories using metadata the server holds in plaintext. No cloud AI
is involved.

**The chatbot can:**
- Answer "how many" questions (count from metadata)
- Answer "when" questions (date arithmetic)
- Answer "what's due" questions (status and dueDate filters)
- Answer "what needs attention" (Active pill aggregation)
- Open views for questions it cannot answer directly

**The chatbot cannot:**
- Draft prose (no LLM)
- Understand ambiguous requests (no LLM)
- Summarise content (no LLM)
- Make judgement calls that require language (no LLM)

When it cannot help, it says so plainly and offers to open the relevant
view. There is no pretence.

When Bosly runs its own model, the workflow engine gains a fifth action:
`phrase(context, intent)`. The model is a voice, not a brain. The
reasoning stays deterministic; the content stays in the user's browser.

### 3.4 Encryption at the transport layer

Independently of the client-side encryption model, all traffic between
the browser and the server is HTTPS. The server itself sits behind
Cloudflare with a Tunnel to the origin. Disk-level encryption applies at
the host.

This is separate from zero-access. The two layers are complementary: TLS
protects data in transit; client-side encryption protects data at rest
even from the operator.

### 3.5 What's working

For clarity, the following are live and functioning as described in Part I:

- Account creation with email and password
- Key ceremony with 24-word recovery phrase and optional PIN backup
- Recovery via recovery phrase or PIN (tested nightly)
- Duress mode (configured in settings)
- Client-side encryption of invoices and health records
- Account deletion in a single transaction
- Warrant canary at /transparency
- Nightly governance pipeline (see Article 6.2)
- Two-tier pricing: free workspace, £25/month for the AI features

### 3.6 What is not yet built

The following are described in Part IV (Planned) and are not currently
available:

- Face ID + PIN recovery
- Multi-device handoff
- Jurisdiction detection
- Legacy access
- Shared spaces
- Post-quantum encryption (Kyber-1024, X25519)
- Open source encryption
- ICO registration
- Local AI models

---

# PART IV — WHAT'S PLANNED

*These features are intended but not yet built. Where a plan item exists, it is
named. This section is not a promise of dates — only of direction.*

### 4.1 Face ID + PIN Recovery

A WebAuthn credential registered alongside the PIN backup, so the recovery
flow can authorise with Face ID or Touch ID rather than requiring the PIN to
be stored in a password manager. Tracked as `accord.face_id_recovery`.

### 4.2 Multi-Device Handoff

Encrypted device-to-device transfer of keys between a user's own devices,
without the server intermediating the exchange.

### 4.3 Jurisdiction Detection

An onboarding step that asks "Where are you based?" to determine which legal
framework applies. The setting will be changeable in Settings.

### 4.4 Legacy Access

A designated legacy contact who can access the vault under specified
conditions after death or incapacity. The Prisma model exists; the UI does
not.

### 4.5 Shared Spaces

Encrypted bridges between sovereign vaults, for small teams or collaborators.
Tracked as `accord.spaces_encryption`.

### 4.6 Post-Quantum Encryption

Kyber-1024 and X25519 key encapsulation. The code exists in
`lib/crypto/kyber.ts` but is not wired into any user flow. Tracked as
`accord.kyber_status_decision`.

### 4.7 Open Source Encryption

The client-side encryption code, key handling, and zero-access proof
mechanisms will be open source. Security researchers will be able to audit the
sovereignty claims. Application features and AI systems will remain closed.

### 4.8 ICO Registration

Registration with the UK Information Commissioner's Office. Tracked as
`ops.ico_registration`.

### 4.9 Local AI Models

On-device or self-hosted models that eliminate the dependency on external AI
providers.

### 4.10 Interface Dissolution

The long-term direction: Bosly as an extension of cognition rather than an
application the user opens. Not specified. Not scheduled.

---

# PART V — AMENDMENT

This accord is a living document. Amendments require:

1. Proposal — a written case for the change
2. Deliberation — the founder considers it against the non-negotiables
3. Ratification — the change is approved
4. Publication — a new version number and date

Amendments must not contradict Part II.

---

*Ratified May 13, 2026. Amended May 30, 2026 (v1.1.0). Revised September 24,
2026 (v1.2.0, v1.3.0, and v1.4.0). This accord is the single source of truth
for what Bosly is, what Bosly stands for, and what Bosly will never do.
Part III tracks where Bosly is on the journey. Part IV names what's planned.
Neither tier promises a cloud AI; neither uses one.*
