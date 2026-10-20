# Portable starter contract

This is a separate, candidate-neutral framework. Never copy the enclosing repository, its Git history, private configuration or candidate records. Export only the reviewed allowlist using `export_starter.py`. The new owner's vault must live OUTSIDE this starter checkout; fail before changing an existing/nonempty vault.

## Supported runtime and commands

Python 3.10+ standard library, Windows/macOS/Linux. Run commands from the starter directory. No dependency install, account login, employer submit or activation runs automatically.

- `python jobhunt.py init --vault PATH`: create a NEW empty private Obsidian-compatible Markdown vault and blank profile. Refuse pre-existing nonempty directories, paths inside this framework, and symlink destinations. Never overwrite existing candidate data.
- `python jobhunt.py doctor --vault PATH`: report readiness/missing profile fields and optional CLI presence without printing candidate values, credentials or private hostnames. Incomplete onboarding is not ready; nonzero exit.
- `python jobhunt.py import-jobs --vault PATH --file JSON`: validate/import a JSON array of normalized jobs; retain exact ATS IDs and employer namespace, dedupe, never mark applied. Invalid input must leave state unchanged.
- `python jobhunt.py review-job --vault PATH --key KEY --file JSON`: explicitly enrich/correct ONE imported, never-claimed sourced job using a normalized JSON OBJECT after manual employer-source verification. Require matching immutable employer/ATS/id/title/URL identity and status sourced, preserve a prior-version audit entry, and atomically replace only reviewable evidence fields. Never use import as a silent overwrite, never alter parked/claimed/applied objects, and never clear a previously established no-AI prohibition. Public-reader output can therefore move from unknown to verified without editing internal state directly.
- `python jobhunt.py screen --vault PATH`: report `eligible`, `review` or `ineligible`, reasons and evidence gaps. Require completed mandate; unknown start/type/experience/family/geography evidence is REVIEW, never assumed eligible. A disclosed below-floor annual salary is rejected; undisclosed pay alone is not a rejection. Nonannual pay or different currency requires review, not guessed conversion. Start date must have source text. No-AI prohibition is OWNER_MANUAL and never claimable.
- `python jobhunt.py claim --vault PATH --key KEY --owner LABEL`: claim ONE eligible exact job before a browser/form is opened, with atomic cross-process exclusivity and a serial global active-form lock. No auto-expiry, replacing another owner or claiming duplicates/applied/uncertain jobs.
- `python jobhunt.py park --vault PATH --key KEY --owner LABEL --reason TEXT --unsent`: record the original claim owner's verified cessation only for a clean, definitely-unsent task. The runtime requires `--unsent`; it attests an already verified fact, not permission to ignore transmission uncertainty. Success releases active control and leaves the job parked and non-reclaimable. If Submit was attempted or dirty/autosaved transmission or confirmation is uncertain, retain the exact claim and global serial hold; do not park, retry, take over or start another form pending owner-led reconciliation. No other owner's release or age-based release.
- `python jobhunt.py receipt --vault PATH --key KEY --owner LABEL --evidence FILE --resume FILE --confirmation-count 1 --identity-verified`: after operator verifies employer/portal evidence and exactly one confirmation in the matching inbox, save receipt with evidence and resume SHA-256 BEFORE recording applied in `Applications/Application Ledger.md`. Require owned active claim, real nonempty files, count exactly one, verified identity flag. Preserve conservative holds on error. This does not send an application, inspect inboxes or certify arbitrary files are employer receipts: a human-supervised operator must verify provenance and document it. No synthetic receipts in a real vault.
- `python jobhunt.py ledger --vault PATH`: read canonical ledger, output actual counts, reconcile against receipt-backed state or fail loudly. No remembered totals.

`--help` on each command is authoritative. JSON stdout for machine-readable results; errors stderr/nonzero. No package paths or personal profile values in normal output. Keys are opaque deterministic hashes of exact employer + ATS kind + exact ATS ID; output them at import/screen so callers never guess. Reject unknown keys, unsafe input/control characters, malformed types and identifiers rather than coercing defaults. Mandate changes cannot resurrect parked or applied jobs.

## Profile: `Profile/candidate.json`

```json
{
  "candidate": {"display_name": "", "email": "", "school": "", "degree": "", "graduation_date": null, "earliest_start": null},
  "mandate": {"role_families": [], "countries": [], "preferred_locations": [], "salary_floor": null, "salary_currency": "USD", "max_required_experience_years": 1, "full_time_only": true, "allow_internships": false}
}
```

Graduation may be null for a nonstudent; earliest_start must be an owner-provided ISO date. Salary floor may be null when the owner intentionally accepts undisclosed/unbounded pay, but initial onboarding must record the owner's approval in `Profile/Owner Answers.md`; code need not parse prose. Name, email, earliest start and nonempty family/country lists are readiness requirements. Defaults are conservative controls, not this repository owner's personal mandate. Evidence bank and resumes start EMPTY; do not invent claims or default to somebody else's geography, salary, GPA or graduation year. Optional field changes require actual owner answers.

## Normalized input job

```json
{
  "employer": "Example Employer",
  "ats": "greenhouse",
  "id": "EXAMPLE-1",
  "title": "Example Analyst",
  "url": "https://example.com/careers/EXAMPLE-1",
  "country": "US",
  "location": "Example City",
  "role_family": "finance",
  "employment_type": "full_time",
  "internship": false,
  "min_years_experience": 0,
  "start_date": "2030-07-01",
  "source_text": "SYNTHETIC SCHEMA EXAMPLE ONLY. Full-time analyst, 0 years required, July 1, 2030 start.",
  "salary_min": null,
  "salary_currency": "USD",
  "salary_period": null,
  "no_ai": false
}
```

The example is NOT a real job or an application. Public source connectors usually lack sufficient structured eligibility information: retain source body/URL, use null for unknowns, and have the operator verify/enrich against employer text before claiming. Never infer eligibility from a posting title, stored scorer flag or a blank page. The CLI screens explicit structured evidence; it cannot independently prove that an operator's transcription is truthful. Title seniority flags should fail closed to review/rejection; employment experience and any degree requirements need operator verification. Same-role location variants need employer-level dedupe as well as exact-ID dedupe.

## Generated vault contract

Create `Profile/`, `Applications/`, `Receipts/`, `Resume/`, `Cover Letters/`, `Research/`, `Networking/`, `Jobs/Sourced/`, `Cursor.MD/`, and a private internal state directory. Include `AGENTS.md`, `CLAUDE.md`, `Cursor.MD/HERMES COORDINATION.md`, `Cursor.MD/SUBMIT LOCK.md`, `Cursor.MD/STATE.md`, `Cursor.MD/HANDOFF.md`, and `Applications/Application Ledger.md` with ZERO real applications. The framework may use atomic local state internally, but ledger/receipt mismatch must fail instead of silently guessing. All mutating commands use a process-safe exclusive lock; fail-closed stale lock recovery is owner/manual. Never bypass an outstanding claim due to age. Create `.gitignore` preventing accidental sensitive artifacts; do not initialize/push Git, run integrations, install tools or change account settings.

## Data and platform limits

- Country values use two uppercase letters, such as `US`. Store owner-approved countries and reviewed job countries in the same format; the CLI does not translate country names or infer work authorization. Role-family labels must also match exactly. Preferred locations are advisory, not an automatic geographic filter.
- Use explicitly approved absolute paths for all commands. Quoted `~/...` expansion is not consistent across the core, source reader and exporter; do not rely on it.
- The generated application ledger and internal state/receipts are CLI-owned. Do not edit, reformat or normalize them in an editor. The ledger is checked byte-for-byte as UTF-8/LF; editor-only CRLF conversion correctly stops reconciliation and requires manual investigation rather than an automatic reset.
- Atomic file replacement and file flushing are not a multi-file database transaction or a verified power-loss durability guarantee. An interrupted receipt/state/ledger sequence may leave a reconciliation hold. Stop, preserve evidence and involve the owner; never delete locks or retry an application merely to clear bookkeeping errors.
- The isolation guard deliberately refuses vault creation under existing Git or agent-instruction hierarchies, including inherited markers in a temporary directory's ancestors. For synthetic tests, use an approved clean `TEMP`/`TMP`/`TMPDIR` for that test process only. Do not weaken the guard or remove someone else's instructions.

## Test acceptance

Use explicit synthetic fixtures in temporary directories outside the framework. Test blank init, refusal/unchanged existing vault, privacy defaults, import transactionality/dedupe/ID integrity, incomplete/unknown/rejected/eligible screening, no-AI, cross-process claim collision, ownership/park holds, receipt prerequisites/hash/order/duplicate protection, canonical ledger count and mismatch detection. Exercise CLI via subprocess in addition to unit-level tests. No browser, employer Submit or real candidate data in tests.
