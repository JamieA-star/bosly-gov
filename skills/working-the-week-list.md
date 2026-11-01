# Skill — working the week's list

Read this when the founder says "work this week's list", "draft
this week's emails", or similar. The procedure used to be carried
in the system prompt every turn; it is a skill now, read on demand.
Nothing was paraphrased — this is the procedure as written.

WORKING THE WEEK'S LIST. When the founder says "work this week's
list", "draft this week's emails", or similar:

1. Call read_leads(only_call_list=true, limit=10) to get the top 10
   as structured rows. Each row has a `contact_route` column. Work
   each row by its route:

   ROUTE = "email" (the audit found a real address):
     - Use draft_email with the address from audit_email.
     - Write ONE short email specific to that business. Mention the
       gap the audit found: no booking, no email, an old build, no
       mobile view. Use the fit_breakdown and audit facts. No
       template.
     - Send the draft to the founder with send_draft_to_me, and say
       which business it is for.
     - Only send_email with confirmed=True after the founder says yes.

   ROUTE = "contact_page" (website, but no email found):
     - Do NOT draft an email; there is no address.
     - Write a short note for the founder: the business name, the
       contact page URL (audit_contact_page is yes, but the URL is
       not in the CSV — tell the founder to open the site and use
       the contact form), what the audit found (no booking, old
       build), and one line to say on the form.
     - Send it with send_draft_to_me so the founder has it on their
       phone.

   ROUTE = "call" (no website or no other contact):
     - Write a CALL BRIEF: business name, town, phone number, the
       gap, one specific observation (years trading, a director's
       name) ONLY if match_confidence is medium or high. If low, say
       "Companies House match uncertain — do not cite the company
       details."
     - The opening line, and the ask (a 15-minute chat).
     - Send it with send_draft_to_me.

2. After all 10, say: "10 briefs sent — X emails, Y contact pages,
   Z calls." Then wait for the founder's approval before any client
   email goes out.

If a row has match_confidence "low" or the SIC looks wrong, flag it
in the brief and do not cite the company details in a draft.
2. Take the top 10 rows where call_list = yes.
3. For each one:
   - Check match_confidence. If it is "low", say so — the company
     match is a guess — and ask before drafting. Do not draft a
     letter to a business you are not sure is the right one.
   - Use the fit_breakdown, the Companies House data (ch_name,
     ch_directors, ch_incorporated), and the OSM details to write
     ONE short email specific to that business. Mention the gap:
     no website, or phone-only bookings. No generic template.
   - Send the draft to the founder with send_draft_to_me.
4. Then tell the founder: "10 drafts sent to your phone. Say
   'send them' to send all, or name the ones to send."
5. Only call send_email with confirmed=True after the founder's
   explicit yes. One confirmation covers the batch if they say
   "send them all"; a named list covers those only.

Do not invent a business's details. If a row is thin (no CH match,
no address), say so in the draft note to the founder.
