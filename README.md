# Job Hunt — a reusable operating system for your own Codex

Start a new search or continue an existing one with evidence-based research,
truthful application materials, a private tracker, and alerts that tell you what
needs attention. The public framework stays separate from your personal records.

**Python 3.10+, standard library only.** Codex is the primary agent entrypoint;
Claude and other assistants can follow the same contract. No paid integration,
Obsidian, n8n, browser driver or API key is required for the local tools. Your
chosen assistant/account is separate.

## Send this to your friend

Clone this public repository or download its ZIP:

```text
git clone https://github.com/Juice-s-Code/Job-Hunt.git
cd Job-Hunt
python -B -m unittest discover -s tests -v
```

On macOS/Linux use `python3` throughout. Open the folder in Codex and paste:

```text
Read AGENTS.md, CODEX.md and docs/PLAYBOOK.md. Validate the toolkit with its
synthetic tests, then help me start or continue MY job hunt. Interview me for
my goals, verified experience, geography, salary rules and availability. Use
only my answers and documents. Ask me to approve a separate private vault path
outside this repository. If I already have a tracker, reconcile it using
docs/MIGRATION.md instead of overwriting it. Build a research plan and tell me
what is missing. Agree with me on application permissions and useful alerts.
Do not apply, send messages, connect accounts or enable schedules during setup.
```

This handoff is also in [START-HERE.md](START-HERE.md). For later sessions paste
[prompts/CONTINUE.md](prompts/CONTINUE.md). Start with a small supervised batch;
expand after the candidate checks the results and approves the scope.

## What is included

| Step | Included | Evidence required |
|---|---|---|
| Onboard | Interview, blank private vault, owner policy and evidence templates | Your approved facts and search mandate |
| Discover | Public Greenhouse reader; bounded multi-board change monitor | Employer-confirmed slugs, full source text |
| Qualify | Conservative screening, audited enrichment, exact-ID dedupe | Role, location, start, pay and experience evidence |
| Research | Employer/role briefs, transferable-skills mapping, priorities | Official sources, dates and explicit gaps |
| Prepare | Resume/cover procedure and document-release manifest | Approved claims, rendered file review, real hashes |
| Apply | Serial exact-job claims, owner gates, receipt/ledger tooling | Current permission and a supervised form operator |
| Alert | Local pending events, acknowledgment, private Markdown reports | State changes; external delivery checked separately |
| Continue | Durable handoffs, migration runbook, recurring prompts | Reconciled private state and retained ambiguous holds |

The Python tools never fill or submit employer forms, inspect your inbox, or send
notifications. Codex can use its available, owner-authorized tools for those parts
under the operating contract. Resume rendering and live ATS compatibility require
operator review; the toolkit does not automatically certify documents.

## Create your private workspace

After approving a new empty path **outside this repository**:

```text
python jobhunt.py init --vault "YOUR_ABSOLUTE_PRIVATE_VAULT_PATH"
python jobhunt.py doctor --vault "YOUR_ABSOLUTE_PRIVATE_VAULT_PATH"
python jobhunt.py ledger --vault "YOUR_ABSOLUTE_PRIVATE_VAULT_PATH"
```

`doctor` correctly fails until the profile is complete. Use the
[onboarding interview](docs/ONBOARDING.md); record decisions under `Profile/`.
An empty ledger is expected. Never use a synthetic test profile as your own.
Active locking belongs on one local machine; cloud sync is not a shared lock.

## Source, review and track

See [docs/SCHEMA.md](docs/SCHEMA.md) for exact profile/job fields and lifecycle.
Replace these placeholders with your private paths and a board slug confirmed
from the employer's careers page:

```text
python source_jobs.py --board VERIFIED_BOARD_SLUG --employer "Employer" --output "NEW_PRIVATE_BATCH.json"
python jobhunt.py import-jobs --vault "PRIVATE_VAULT" --file "NEW_PRIVATE_BATCH.json"
python jobhunt.py screen --vault "PRIVATE_VAULT"
```

Unknown facts stay in review. After reading the full posting, save a normalized
object privately and use `review-job` with the import's returned key. Claims need
eligible evidence and one global form lane. Changed postings never overwrite
reviewed records silently. Follow [the playbook](docs/PLAYBOOK.md).

For repeated discovery, copy `templates/sources.example.json` into private
`Research/sources.json`, replace its placeholder, and run:

```text
python watch_sources.py --vault "PRIVATE_VAULT" --config "PRIVATE_VAULT/Research/sources.json"
python jobhunt_ops.py report --vault "PRIVATE_VAULT"
python jobhunt_ops.py alerts --vault "PRIVATE_VAULT"
```

The monitor compares successful board snapshots, preserves prior data on failure,
and distinguishes new/changed/not-observed postings. It makes no eligibility or
closure claim. Reports remain private. Events remain pending until acknowledged
after actual delivery. See [docs/ALERTS.md](docs/ALERTS.md).

## Read the procedure

- [CODEX.md](CODEX.md) / [AGENTS.md](AGENTS.md): startup and operating rules.
- [PLAYBOOK](docs/PLAYBOOK.md): daily/weekly process and application checkpoints.
- [RESEARCH](docs/RESEARCH.md): sourcing, evidence, fit and prioritization.
- [DOCUMENTS](docs/DOCUMENTS.md): truthful tailoring and attachment release.
- [ALERTS](docs/ALERTS.md): useful notifications and optional scheduling.
- [MIGRATION](docs/MIGRATION.md): continue an existing search safely.
- [INTEGRATIONS](docs/INTEGRATIONS.md): optional browser, mail, Obsidian and n8n.
- [OPERATIONS](docs/OPERATIONS.md): reports, monitor state, errors and recovery.
- [TESTING](docs/TESTING.md): deterministic tests, CI and export checks.

## Share the framework, keep the vault private

Public Git contains code, blank templates, synthetic tests and documentation.
Never upload filled profiles, resumes, receipts, contacts, inbox exports, browser
profiles, credentials, agent memories or private Git history. `.gitignore` helps
prevent accidents; it neither encrypts files nor certifies privacy.

Make a reproducible framework-only bundle with:

```text
python export_starter.py --output "NEW_RELEASE_PATH.zip"
```

The exporter uses an explicit allowlist and includes a SHA-256 manifest. Review
the result before sharing. [MIT license](LICENSE); [CONTRIBUTING](CONTRIBUTING.md).
