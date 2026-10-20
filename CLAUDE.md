# Independent job hunt — Claude Code entrypoint

Read `AGENTS.md`, `README.md`, `docs/SCHEMA.md`, `docs/ONBOARDING.md` and relevant integration guidance before acting. This framework contains NO candidate facts. Never inherit another applicant's facts, instructions, accounts, browser profile, agent memory or Git history. A friend's permission to use the framework is not permission to access the original private vault.

## First run

1. Inspect current local state and run `python -B -m unittest discover -s tests -v` (use `python3` on macOS/Linux). Missing files, zero tests or failures mean NOT READY. Do not install tools or activate integrations automatically.
2. Interview the owner using `docs/ONBOARDING.md`. Ask approval for a NEW private vault outside this framework and all other candidates' instruction hierarchies. Never initialize over existing data.
3. Run `jobhunt.py init`, record only approved owner facts inside that private vault, then run `doctor` and `ledger`. A blank profile correctly fails doctor and has zero applications. No application work during onboarding.
4. Use normal tool permission prompts. Do not disable approval/sandbox controls or reroute a denied action through another tool/session.

## Working rules

- Objective: genuinely eligible, evidence-supported applications under THIS owner's approved mandate. Volume never justifies weakening it.
- Unknown personal facts stay unknown; ask the owner. Evidence-only tailoring selects verified claims and never invents responsibilities, dates, metrics, honors or skills. Provide a cover letter when accepted, using approved evidence.
- Read complete canonical employer descriptions and full live questions/footer. Source snippets, stored flags, title years, blank pages and guessed ATS tokens do not clear eligibility. An employer applicant-GenAI prohibition ends ALL AI work on that application, including drafting, preparation and form inspection.
- Preserve exact employer/ATS/job IDs. Import is immutable. Use `review-job` only for reviewed, never-claimed source enrichment. No direct internal-state edits to evade checks.
- Before any applicant form: complete profile, current eligibility, full employer-level mirror dedupe, and the exact `claim`. One active form across all operators, including humans. Source work may be parallel only with separate exact write scopes.
- Stop for accounts/sign-in/passwords, CAPTCHA or human-verification codes, SSN/ITIN, compensation expectations, standardized test scores, referrals, legal/authorship attestations, offers and spending. The human performs these. Optional EEO, gender, race, veteran and disability fields remain untouched.
- Opening or typing may autosave/transmit. Never describe no Submit as no transmission. Use only owner-approved, inspected, hash-verified attachments. Never generate, alter or rerender a transcript.
- The code has NO employer submit command. A human-supervised browser operator needs explicit authority and current full-form/attachment/identity checks. Final Submit happens at most once; a timeout or missing confirmation does not permit retry.
- On dirty/ambiguous state or any Submit attempt, retain exact claim AND global serial hold until owner reconciliation. Do not `park` to escape a missing receipt. Record last URL/state, changes and attempt time privately; preserve the tab. `park` is only for definitely-unsent, clean tasks after operator cessation.
- Write verified employer evidence and receipt with exact submitted resume hash BEFORE applied/ledger bookkeeping. Independently check the correct current mailbox and exactly ONE matching confirmation. Allow delivery delay; recheck read-only, never resubmit from an early negative. CLI verification flags record checked facts, not truth supplied by software.
- `ledger` is the count. Drafts, uploads, clicks, worker reports and n8n runs are not applications. Failure, partial coverage and unverified integrations must be reported explicitly.

## Privacy and optional services

Do not share or publish a candidate vault. Do not log credentials, cookies, codes, private tenant hosts/resource IDs, profile values or contact records. No automatic installations, account linking, workflow publication/activation, mail sending, spending, or background fleet. n8n may source/screen but NEVER submit. Use only this owner's approved separate integrations. Graphify is optional navigation, not evidence or authority; no private indexing/egress without permission. Hermes may coordinate multiple tools with acknowledged temporary assignments; no model owns a permanent lane. See `AGENTS.md` for handoffs.
