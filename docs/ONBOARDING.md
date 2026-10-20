# Onboarding and first supervised cycle

## 1. Validate before configuring anything

Use only the reviewed **allowlist-export ZIP download** or a new-history repository made from those exact reviewed files. Do not clone the original private repository, copy its `.git` directory, transfer its agent profile or read its vault. Extract outside any other candidate's project tree; instruction files and memories from parent directories must not become your personal facts.

Open the starter in your own Codex and use the first prompt in `../README.md`; Claude Code is an optional alternative. Read `CODEX.md` and `AGENTS.md`. Validate the code and configuration contract before adding personal data. Read `SCHEMA.md` and the actual CLI help. The core needs Python 3.10+ and only its standard library. On Windows:

```text
python --version
python -B jobhunt.py --help
python -B source_jobs.py --help
python -B -m unittest discover -s tests -v
python -B -m json.tool templates/n8n-greenhouse-source.json
```

On macOS/Linux, replace every `python` above and below with `python3`. `-B` avoids Python bytecode cache writes. Tests must be synthetic and use temporary vaults outside the framework. Require a nonzero number of passing tests; absent code/tests or failures mean STOP, not ready. The JSON command proves syntax only, not n8n import/runtime compatibility.

No install, login, extension pairing, connector, service, paid action, remote call to an account, scheduler, publishing or Git initialization is authorized merely by this guide. Ask for consent first unless the owner already authorized that scope. Keep tool permission prompts enabled. `CLAUDE.md` is instructional context, not an enforceable sandbox or a replacement for human supervision.

## 2. Interview the new owner

Ask in small groups, show the proposed interpretation, and obtain approval. Do not prefill from the framework author's life or an old session. The current candidate chooses role **families**, dates, pay and geography.

| Owner question | Private profile destination / interpretation |
| --- | --- |
| What display name and application email should this search use? | `candidate.display_name`, `candidate.email`. Do not guess account identity from an old message. |
| What school/degree, if relevant, and what verified graduation date? | `candidate.school`, `candidate.degree`, `candidate.graduation_date`. Graduation may be null for a nonstudent; do not fabricate a date to satisfy a form. |
| What is your earliest actual start date? | `candidate.earliest_start`, owner-provided ISO `YYYY-MM-DD`; not today's date or another person's cohort. |
| Which role families do you want? | `mandate.role_families`, a nonempty list of owner-approved labels used consistently during normalization. |
| Which countries are permitted? Which locations are only preferences? | `mandate.countries`, nonempty two-uppercase-letter values such as `US`, and `mandate.preferred_locations`. Record the approved mapping explicitly; do not enter `United States` where `US` is required. A preference is not an exclusion. Verify location/remote eligibility and country separately. |
| What annual minimum base salary and currency do you require? Do you intentionally want no floor? | `mandate.salary_floor`, `mandate.salary_currency`. If floor is null, explicitly record that decision in `Profile/Owner Answers.md`; a blank answer is not consent. |
| What maximum required experience should we consider? | `mandate.max_required_experience_years`. Confirm the initial value instead of assuming it is the owner's preference. |
| Full-time only? Are internships allowed? | `mandate.full_time_only`, `mandate.allow_internships`. Confirm both default controls. |
| Any additional exclusions, relocation constraints or school/program requirements? | Record exact approved answers and unresolved questions in `Profile/Owner Answers.md`. Do not pretend prose-only constraints are automatically enforced by the CLI. |
| Which existing documents and factual claims may be used, and in which tools? | Private evidence/approval notes. No transcript, resume or account access is inherited or authorized by its filename. |

Name, email, earliest start and nonempty family/country lists are readiness requirements. Preserve the exact JSON shape and types in `SCHEMA.md`; do not add unsupported schema keys for prose-only decisions. Explicit schema defaults are conservative starting controls, not completed onboarding. Never collect passwords, SSN/ITIN or other secrets in this interview. Account setup and sensitive employer questions remain owner-only tasks.

## 3. Approve a separate private vault

Choose a local absolute path to a new or empty directory **outside** the starter. Prefer one local filesystem and one machine for active work: the lock is not a distributed cloud-sync lock. Do not use a symlink or an existing populated job vault. Ask the owner to approve the exact path before writing.

Example Windows commands, after replacing the entire placeholder path:

```text
python -B jobhunt.py init --vault "C:/REPLACE_ME/Private Job Vault"
python -B jobhunt.py doctor --vault "C:/REPLACE_ME/Private Job Vault"
python -B jobhunt.py ledger --vault "C:/REPLACE_ME/Private Job Vault"
```

macOS/Linux:

```text
python3 -B jobhunt.py init --vault "/REPLACE_ME/private-job-vault"
python3 -B jobhunt.py doctor --vault "/REPLACE_ME/private-job-vault"
python3 -B jobhunt.py ledger --vault "/REPLACE_ME/private-job-vault"
```

An initial nonzero doctor result is expected: the owner has not completed the profile. `init` is not a migration/merge command and must refuse unsafe destinations without overwriting them. On refusal, inspect the actual error and choose a different approved path; never delete existing files to make initialization succeed.

The vault contract creates:

```text
Profile/                    # candidate.json; owner answers belong here
Applications/               # Application Ledger.md
Receipts/
Resume/
Cover Letters/
Research/
Networking/
Jobs/Sourced/
Cursor.MD/
  HERMES COORDINATION.md
  SUBMIT LOCK.md
  STATE.md
  HANDOFF.md
AGENTS.md
CLAUDE.md
.gitignore
[private internal state directory managed by the CLI]
```

Do not depend on an invented internal-state path. Generated evidence and resume areas start EMPTY, with ZERO real applications. Do not seed a real vault with the synthetic schema example or test receipts. Keep your filled profile, applications, evidence, notes, screenshots and agent state outside the framework and out of any public export.

Approve and save `Profile/candidate.json` and `Profile/Owner Answers.md` in the new vault, then rerun `doctor` and `ledger`. Read doctor literally: profile readiness and optional CLI presence are not proof of browser, inbox or service access. Do not claim onboarding complete while owner answers remain missing. Record consent for the next bounded activity; initialization does not authorize applications.

## 4. Create an evidence and document-release habit

A simple private Markdown evidence bank may live under `Profile/`; this is an operator convention, not a separate CLI feature. For each usable claim, record the exact fact, source artifact or owner statement, evidence locator, approval and any limits. Do not turn a plausible inference into a verified date, GPA, degree, skill or achievement. Conflicting evidence goes to the owner.

Before a real application:

1. Read the canonical posting and permitted application requirements. If the employer prohibits applicant AI use, stop all AI work on that application immediately, including research and drafting; leave it to the owner manually.
2. Tailor the resume and, when accepted by the employer, a cover letter using only approved evidence. Have the owner review factual claims and release the actual artifacts. The core does not render PDF/DOCX or certify document content.
3. Record each released file's actual SHA-256 and approval privately, then rehash the exact intended attachment before use. A matching filename is insufficient; check preselected portal attachments too.
4. A transcript must be supplied by the owner and explicitly approved by its actual SHA-256. **Never generate, alter, reformat or silently convert a transcript.** If unavailable, unapproved, changed or incompatible with the form, stop for the owner. No synthetic transcript is permitted.

A portable stdlib hash command (substitute the real approved path; `python3` on macOS/Linux):

```text
python -B -c "import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())" "APPROVED_ARTIFACT_PATH"
```

A hash proves byte identity, not truth, owner approval or employer receipt provenance. Do not paste private artifact content or identifiers into public diagnostics.

## 5. Source, normalize and screen without opening a form

The optional bundled `source_jobs.py` connector needs no extra account. With approval for a public network fetch, verify `PUBLIC_BOARD_SLUG` from the employer's real careers page; do not guess it. If the approved vault is a sibling named `MyCareerVault`, run from the starter directory:

```text
python source_jobs.py --board PUBLIC_BOARD_SLUG --employer "Employer Name" --output ../MyCareerVault/Jobs/Sourced/greenhouse.json
python jobhunt.py import-jobs --vault ../MyCareerVault --file ../MyCareerVault/Jobs/Sourced/greenhouse.json
python jobhunt.py screen --vault ../MyCareerVault
```

Use `python3` on macOS/Linux. Replace the board and employer placeholders with verified public values, and replace both vault paths with your approved path if different; quote paths containing spaces. The source output must be **outside the framework and new**. If it exists, use a new filename; do not overwrite evidence. The connector retains the complete source body/URL and leaves unverified eligibility, **including `no_ai`, null**. It does not clear jobs to apply. The raw n8n response is a different shape and must not be passed directly to `import-jobs`.

Read every relevant canonical source section, including compensation, degree/graduation windows, seniority and any program start language. After manually verifying employer-source evidence, save one reviewed normalized **JSON object** (not an array) in a new private file. Preserve exact `employer`, `ats`, `id`, `title` and `url`; edit only source-backed reviewable evidence fields. Keep the previous source and provenance. Use the opaque key returned by import:

```text
python jobhunt.py review-job --vault ../MyCareerVault --key EXACT_RETURNED_KEY --file ../MyCareerVault/Jobs/Sourced/reviewed-job.json
python jobhunt.py screen --vault ../MyCareerVault
```

Replace paths/key with actual approved values; use `python3` on macOS/Linux. `review-job` accepts only an imported, **never-claimed job still in sourced status**, atomically updates reviewable evidence and preserves a prior-version audit entry. It refuses identity changes, claimed/parked/applied objects and clearing an established no-AI prohibition. `import-jobs` rejects changed records instead of silently overwriting them. Never reimport with a different ID/namespace, edit internal state or clear a hold to make enrichment possible. If the command/help does not implement this contract, stop and report the package gap.

Conservative outcomes:

- Unknown start date, employment type, experience, role family or geography is **review**, never eligible. Source absence is not zero required experience or a full-time offer. Start-date fields need corresponding source text.
- Disclosed below-floor annual pay is rejected. Undisclosed pay alone is not rejection; nonannual or different-currency amounts require review, not guessed conversion.
- A known applicant no-AI prohibition is **OWNER_MANUAL**, not claimable. Unknown `no_ai` is review until the relevant full posting and terms are verified; an employer's own use of AI is not automatically a ban on applicants.
- Validate malformed identifiers as received and reject rather than repair. Preserve exact employer, ATS kind and ID; use the returned opaque key, not a reconstructed hash. Manually dedupe same-role location variants and prior submissions beyond exact-ID dedupe.
- A source count, scored flag, API 200, parseable error payload, empty careers shell or missing question in an API is not eligibility evidence. Public sourcing is not candidate-form inspection.

## 6. Claim, then inspect one form under human supervision

For a fully verified eligible job only, obtain the exact opaque key from CLI output. Commands below are templates; replace all placeholders with actual approved values. Do not open the applicant form first.

```text
python jobhunt.py claim --vault "VAULT_PATH" --key "EXACT_RETURNED_KEY" --owner "OPERATOR_LABEL"
```

The claim must succeed and the operator must own the sole active-form lane. This coordinates cooperating operators on the same vault; it is not a browser access-control system. Read the entire live form, attachment slots, trailing prose and terms before entering candidate information. Truncated instructions or unknown required fields are blockers. Recheck exact employer/job/candidate and released attachment hashes immediately before any owner-authorized Submit.

**Human-only stops:** account creation/login, passwords, CAPTCHA, SSN/ITIN, legal or authorship attestations, compensation questions, test scores, referrals, offers and spending. Do not guess, provide defaults, click acceptance or work around a denied tool/account boundary. Required unresolved questions require an owner decision. Leave optional compensation and **optional EEO untouched**. An employer no-AI prohibition stops the entire application immediately, including further AI inspection or packet work.

The stdlib core has **no browser or submit command**. If browser integration is absent, the human may operate the form while Codex keeps the local claim/checkpoints, provided all rules and receipt prerequisites can still be met. Do not invent a browser tool or assume the candidate's inbox is connected.

### Clean cessation versus uncertain/dirty work

Use `park` **only after the operator has ceased and the task is clean and definitely unsent**, with no ambiguous dirty/autosaved state:

```text
python jobhunt.py park --vault "VAULT_PATH" --key "EXACT_RETURNED_KEY" --owner "OPERATOR_LABEL" --reason "ACTUAL_CLEAN_UNSENT_BLOCKER" --unsent
```

`--unsent` is required by the runtime and records an already verified clean, definitely-unsent state; never add it merely to bypass a refusal. Use the same actual operator label that owns the exact active claim. Parking releases active control but preserves a blocked, non-reclaimable job. It is not a reset or permission to resume later automatically.

**If Submit was attempted, the form may have autosaved/sent data ambiguously, or a confirmation is missing: KEEP the exact active claim and global serial hold. Do not call `park`, retry, refresh/reopen the form or begin another form until the owner reconciles.** Stop browser actions, preserve the tab if possible, and record the exact last observed URL, input/upload state, attempt status, timestamp from a tool, blocker and read-only reconciliation needs in `Cursor.MD/HANDOFF.md`. Age, worker exit, lost tab or a quiet inbox never releases the hold. Do not delete stale locks or hand-edit internal state to proceed.

## 7. Verify first, receipt second, count last

A click, local success message or worker self-report is not proof of an application. The human-supervised operator must verify:

- The employer/portal's actual confirmation belongs to the exact employer, job and candidate.
- Current connected mailbox identity matches the verified application email. Historical recipient headers do not establish the active mailbox identity. Manual human inbox verification is acceptable; the core has no inbox reader.
- There is **exactly one** matching employer application confirmation, identified by actual content and job/candidate context, not only subject text. Check delivery delay without repeating Submit. Zero, multiple, ambiguous or unverified confirmations remain unresolved with the active/global hold intact.
- Saved evidence is real, nonempty, private and attributable to that employer/portal event. Preserve provenance and inbox-verification notes privately. The resume file is the actual submitted, released artifact.

Only after these facts are established, with the original owned active claim:

```text
python jobhunt.py receipt --vault "VAULT_PATH" --key "EXACT_RETURNED_KEY" --owner "OPERATOR_LABEL" --evidence "VERIFIED_RECEIPT_EVIDENCE_FILE" --resume "ACTUAL_SUBMITTED_RESUME_FILE" --confirmation-count 1 --identity-verified
python jobhunt.py ledger --vault "VAULT_PATH"
```

The flags record **operator-verified inputs**. The helper cannot inspect an inbox, establish employer provenance or turn an arbitrary file into proof. It computes SHA-256 for evidence and resume and saves the receipt **before** recording applied in `Applications/Application Ledger.md`. Never invent evidence to satisfy prerequisites; preserve conservative holds on any error.

Use the actual receipt-backed `ledger` output for totals. Fail loudly on a mismatch; do not manually reconcile by guessing or counting drafts/claims/n8n runs as applications. End with confirmed changes, evidence paths, held state, owner decisions and verified operator cessation. No onboarding or application claim is complete merely because an agent finished its turn.
