# Optional integrations and verification boundaries

The core is a local Python 3.10+ standard-library CLI. It does not install, authenticate, launch a browser, submit applications, inspect inboxes, activate workflows or start services. Optional integrations below require the **new candidate owner's own setup and consent**. Do not copy the original owner's browser profile, credentials, private hosts, account/resource IDs, agent skills, memories or integration exports.

## Capability map

| Integration | Supplied here | Owner must supply/approve | Evidence before saying it works |
| --- | --- | --- | --- |
| Codex | `AGENTS.md`, `CODEX.md` and startup/continuation prompts | Own account and private-vault access | Instructions read, synthetic tests passed, actual permitted tool demonstrated |
| Claude Code | Required `CLAUDE.md`/`AGENTS.md` instruction entrypoints; package incomplete if absent; no bundled account or client | Their own installation, account/plan, permissions and data-sharing choices | Correct project instructions loaded; local code/tests run; exact allowed tool demonstrated. |
| Claude browser integration | Guidance only; no built-in browser driver in `jobhunt.py` | Supported browser/extension, eligible account, login, site permissions and supervised operation | Correct current browser and exact public target read successfully; a connected label alone is insufficient. |
| Email/inbox | Verification procedure only | Their own mailbox, credentials/OAuth scopes or manual human mailbox checks | Observed current mailbox identity and exactly one matching confirmation for the actual job/candidate. |
| Public Greenhouse source CLI | `source_jobs.py`; no credentials/account needed | Approved public board slug, employer namespace and new outside-framework output path; permission for the public GET | Actual command result and validated saved rows, separately from eligibility review. |
| n8n | Inactive manual-trigger + public HTTP GET JSON template | Own n8n instance/account if desired, consent to import/manual run, verified public board slug | JSON parse, import, manual draft execution and published execution are distinct facts; only claim the one actually observed. |
| Obsidian | Plain Markdown-compatible private vault structure | Optional app installation and permission to open the approved vault | Actual files open; no plugin or Sync is needed for core use. |
| Hermes | Temporary-assignment protocol only | Own installation/provider, fresh profile, tools, permissions and spend approval | Actual acknowledged assignment, scoped result/artifacts and verified cessation; not merely a process or profile name. |
| Graphify | Navigation/privacy guidance only | Optional local installation, reviewed public-only input allowlist and indexing/egress approval | Real query output and source-note check; no automatic indexing or uploading of the private vault. |
| Document renderer | Evidence/release instructions only | Optional local editor/converter and approved artifact format | Human-reviewed final bytes and recorded hash, not just a generated filename. Never convert/alter a transcript automatically. |

`doctor` reports profile gaps and optional executable presence; it does not check every product, account, permission or live connection. A test passing on one machine does not certify another owner's installation.

## Codex: default operator

Open the framework in your installed Codex and read `AGENTS.md` and `CODEX.md`.
Use the README startup prompt or `prompts/CONTINUE.md`. Verify the actual available
browser, inbox and scheduling tools; none are assumed. One agent and the human
are sufficient. An application form needs the exact claim and current authority.
For schedules read `ALERTS.md`; the Python tools never schedule or send messages.

## Claude Code: optional alternative

Use the candidate's own existing Claude Code installation. If missing or unauthenticated, present the [official setup documentation](https://code.claude.com/docs/en/overview) for the owner; do not install or sign in automatically. Start `claude` in the clean starter directory, with normal approval prompts, and use the first prompt in `../README.md`. The prompt begins by validating code/tests/configuration, not by installing a tool stack.

[Claude memory documentation](https://code.claude.com/docs/en/memory) explains how `CLAUDE.md` and ancestor/user instructions are loaded. Check `/context` and the actual files rather than assuming the right policy loaded. Do not transfer global memory or a previous candidate's instruction files. Markdown guidance does not technically block unsafe actions; the CLI's tested state guards and human oversight serve separate roles. Do not disable permissions or weaken a denial to make onboarding work.

### Optional browser access

Consult the [official Chrome integration guide](https://code.claude.com/docs/en/chrome) for current browser, plan, authentication and platform requirements; they differ from the portable core's requirements. Do not assume a working API-key session guarantees extension access or that every Windows/WSL setup has the same browser capabilities.

Only after the owner separately approves and performs required installation/authentication:

```text
claude --chrome
```

Use `/chrome` to inspect the current connection and select the intended browser. Verify one permitted public careers-page read before claiming browser readiness. Keep that check separate from applicant-form navigation, which requires the exact job claim. Discover the actual available tool schemas; do not hardcode another person's tab/session IDs or guessed upload tools. Restrict access to the exact employer target and avoid unrelated tabs/screenshots.

Account creation, passwords, CAPTCHA and legal/authorship attestations remain human stops. Browser login state is personal. A tool timeout, permission denial or lost tab does not authorize relinking, a different tool path or retrying Submit. If an application may be dirty/autosaved or Submit was attempted, retain the active claim and global serial hold until owner reconciliation; do not park or start another form.

If no browser integration exists, keep Claude as the single local operator and have the human use their browser under the same claim/checkpoint rules. No Hermes installation is required for this mode.

## Email: owner credentials or manual verification

No Gmail, Microsoft Graph, IMAP or SMTP connector is bundled. The owner may use a manual inbox check, or separately authorize their chosen email tool with their own account and least-privilege read access. Do not request credentials in chat, paste them into notes, copy another person's `.env`, or create an app password/OAuth connection without consent. Sending mail, outreach and calendar mutations are separate permissions, not side effects of verifying a receipt.

Before receipt recording, verify the current mailbox identity against the candidate's application address; preserve only minimal private identity-match evidence. Search/read the exact employer/job confirmation and establish **exactly one** corresponding confirmation. Generic recruiting mail, a matching subject alone, a historical recipient header or another connector's identity is not enough. If delivery lags, perform read-only checks without repeating Submit; zero/multiple/unknown confirmations leave the exact active/global hold intact. The `receipt` CLI accepts human-supervised verification inputs but does not independently inspect mail or prove provenance.

## Account-free public Greenhouse source CLI

This connector uses Greenhouse's unauthenticated public job-board GET API. It is a source importer, **not** an application submitter, form reader or eligibility verifier. Verify the board slug on the employer's real public careers page and choose a stable exact employer namespace. No private host or account identifier should be involved.

Run from the starter directory after approving the public fetch. This example assumes the approved vault is a sibling directory named `MyCareerVault`; replace paths if not. Output must be new and outside the framework:

```text
python source_jobs.py --board PUBLIC_BOARD_SLUG --employer "Employer Name" --output ../MyCareerVault/Jobs/Sourced/greenhouse.json
python jobhunt.py import-jobs --vault ../MyCareerVault --file ../MyCareerVault/Jobs/Sourced/greenhouse.json
python jobhunt.py screen --vault ../MyCareerVault
```

On macOS/Linux use `python3`. Replace board/employer placeholders, and quote any paths containing spaces. Consult `source_jobs.py --help` for the installed command contract. Do not overwrite old output; use a new file on a later fetch.

The connector retains full source body/URL and exact job identity, and leaves unverified eligibility fields, **including `no_ai`, null**. They remain **REVIEW** until the operator verifies the complete canonical source. Do not infer full-time status, zero experience, country, start date, family, pay or permission for applicant AI use from missing metadata. Do not convert a malformed ID, error payload or missing field into a plausible job. Raw API and verified normalized data are distinct stages. The operator still needs employer-level dedupe for role/location mirrors.

To enrich one imported job after manual employer-source verification, save a normalized **JSON object** in a new private file with unchanged `employer`, `ats`, `id`, `title` and `url`, then use the exact returned import key:

```text
python jobhunt.py review-job --vault ../MyCareerVault --key EXACT_RETURNED_KEY --file ../MyCareerVault/Jobs/Sourced/reviewed-job.json
python jobhunt.py screen --vault ../MyCareerVault
```

Use `python3` on macOS/Linux and substitute approved paths/key. Only a never-claimed job still in sourced status may be reviewed. The command preserves a prior-version audit entry and updates only reviewable evidence atomically; it cannot edit claimed/parked/applied records or clear an established no-AI prohibition. Immutable import is not an enrichment/overwrite route. Do not change identity or edit internal state to evade these restrictions.

## n8n: inactive source-only template

File: `../templates/n8n-greenhouse-source.json`.

```text
Manual Trigger -> GET Public Greenhouse Board -> raw source response
```

The JSON has `active: false`, no credentials, no private resource/instance IDs, no schedule/webhook, no subworkflow, no submission endpoint and no candidate payload. Its two node IDs are template-local labels, not copied service resources. HTTP method is explicitly GET, authentication is none, body/headers are disabled, redirects and automatic retries are disabled, TLS validation remains on, and a bounded timeout is set. The only URL is:

```text
https://boards-api.greenhouse.io/v1/boards/REPLACE_ME/jobs?content=true
```

This is **template JSON validation only**, not a claim of live import, publication, activation or runtime compatibility with the owner's n8n version. The supplied template does not normalize, screen, save into a vault, call `jobhunt.py`, read private notes or submit an application. n8n may only source/screen in an owner-approved future extension, **NEVER submit**. Do not add applicant APIs, browser actions, uploads, inbox credentials or automatic activation to this template.

### Optional owner-supervised import and manual source test

1. If the owner wants n8n, let them choose/provision their own instance and accounts using [official n8n documentation](https://docs.n8n.io/). Do not start containers/services, buy hosting or authenticate for them without consent. No n8n account is needed when using `source_jobs.py` instead.
2. Parse locally with `python -B -m json.tool templates/n8n-greenhouse-source.json` (`python3` on macOS/Linux). Inspect the exact two nodes and public URL. This makes no network request.
3. With explicit import permission, use the editor's **Import from File** as described in [n8n export/import documentation](https://docs.n8n.io/workflows/export-import/). Keep the imported workflow inactive/unpublished. Read back the imported target and inspect its actual state/nodes; a successful import response alone is insufficient.
4. Replace only `REPLACE_ME` with the board slug verified from the canonical employer page. Confirm GET, no auth/body, public target, no private inputs and no schedule. Do not use a credential-bearing cURL export. If node options are incompatible with that n8n version, stop and review rather than claiming compatibility.
5. With separate permission for a public fetch, select **Execute Workflow** manually. Record the exact saved draft revision and its observed run result privately. Read back the execution outcome and validate that the result is a jobs payload, not an error object or incomplete page. Do not fabricate a successful run.
6. Keep it inactive/unpublished. A **manual draft run is not a run of a published version**. Import success, draft execution, publishing and published execution are different assertions. No automatic publication or activation is authorized; no published/live execution has been tested by shipping this JSON.

A response is raw public source, not the normalized array required by `import-jobs`. Preserve full content and canonical URLs, validate exact IDs, and explicitly map supported fields only after source verification. Unknown eligibility and `no_ai` stay null/review. Do not promote arbitrary API metadata or an n8n scorer flag into eligibility. The standalone source CLI is the simpler supplied normalization route; no n8n-to-vault adapter is included.

Official references: [Greenhouse public job-board API](https://developers.greenhouse.io/job-board.html), [n8n Manual Trigger](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.manualworkflowtrigger/), [HTTP Request](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/). Greenhouse documents the `content=true` list-jobs option and public GET access; its application POST API is expressly outside this starter's scope.

## Obsidian: optional editor, not a required service

The vault is ordinary local Markdown plus the CLI's structured profile/state. Use a text editor or, if already installed/approved, Obsidian's **Open folder as vault** on the new private vault, not on the framework. No plugin, paid service or account is needed for local Markdown use. See [Obsidian Help](https://help.obsidian.md/).

Do not automatically enable Obsidian Sync, publish notes, install community plugins, expose a local API or upload attachments. The owner decides backup/encryption/sync policy. Active state should stay on one machine/local filesystem; syncing folders does not make the serial lock safe across machines. Never make the vault public simply because the framework is reusable.

## Hermes: optional temporary exact assignments

Hermes is not required; one Codex operator plus a supervising human is the default. For an owner who opts into orchestration, use the [authoritative documentation index](https://hermes-agent.nousresearch.com/docs/llms.txt) to discover current installation, CLI, profile and delegation instructions. Consult local `hermes --help` after installation. Do not guess nested documentation URLs or run an installer/authentication flow on the owner's behalf without approval.

If the owner has installed Hermes and approves a new profile, [official profiles documentation](https://hermes-agent.nousresearch.com/docs/user-guide/profiles) documents:

```text
hermes profile create career-starter
hermes -p career-starter setup
```

These are **optional setup actions for the owner**, not commands run by this starter. Stop if that name already exists rather than overwriting it. Create fresh: never use clone/import/export of someone else's profile or copy their configuration, keys, skills, memory or history. Verify this owner's provider/account binding. Profiles isolate agent state but are not filesystem sandboxes; keep explicit path and tool boundaries. Do not start a gateway, scheduler, daemon or persistent fleet as part of onboarding.

Use temporary, acknowledged assignments in the private vault's `Cursor.MD/HERMES COORDINATION.md` and current handoff, not permanent model ownership. Each assignment should state:

```text
Assignment: owner-chosen unique label
Operator: actual acknowledged agent/session or human
Objective: one bounded task
Exact target: canonical public URL + employer/ATS/ID + returned job key if applicable
Read scope: explicit approved files/URLs only
Write scope: exact non-overlapping private output paths; one writer per file
Allowed actions: source reads OR evidence-only draft OR one claimed supervised form
Forbidden: other forms/files, account/login changes, secrets, submit unless separately
           human-authorized, n8n activation/publication, legal/authorship answers,
           compensation/test scores/referrals/offers/spending, optional EEO
Stop: any employer applicant no-AI prohibition ends ALL AI work on that application
Claim/hold: current verified owner and active serial state; no timeout release
End: bounded completion or hard stop; acknowledge cessation
Handback: actual observations, evidence paths/hashes, changed artifacts, last UI state,
          any input/upload/Submit attempt, unresolved questions, exact hold and safe next action
```

The coordinator verifies the actual assignment acknowledgment, artifacts and final cessation; a note written is not a message delivered or task accepted. Source research/draft work may be parallel only in disjoint scopes. All applicant-form inspection and entry remain serial. No second form operator and no simultaneous writers to profile/ledger/state. A changed assignment or quiet worker does not release an occupied task. Keep active/global holds on any attempted Submit, ambiguous autosave/dirty state or missing confirmation; `park` is only for clean definitely-unsent cessation. Never let a general scheduler's stale-task recovery clear an application claim.

## Graphify: optional navigation, never truth

No Graphify dependency, hook or private graph is shipped. If the owner chooses an installed Graphify tool, consult that installation's help/instructions for commands and costs rather than assuming a version. Graph results are an index: verify the cited current Markdown/evidence before using any candidate fact, status or count. The receipt-backed ledger and owner-approved evidence remain authoritative.

**Do not automatically index private files or upload notes.** Any public graph must be built only from a separate reviewed public/synthetic allowlist, excluding PII, contact details, filled profiles, resumes/transcripts, applications/receipts, inbox/browser evidence, local paths, private host/resource/session IDs, hidden metadata and identifying links. Review both nodes and edges plus any generated reports before sharing. Local/AST-only processing reduces some egress risk but does not make private graph output public-safe. No whole-vault or ancestor-repository indexing/update is authorized by this starter.

## Keep readiness claims narrow

Report what was actually observed: local test pass, parsed JSON, verified public-source output, imported inactive draft, successful manual draft fetch, approved document bytes or matching inbox identity. Do not collapse those into "fully integrated" or "applied." Never copy live workflow exports containing credential references or private resource IDs into the reusable package. Share only the reviewed allowlist-export download, or a new clean Git repository made from it, with no original history or candidate data.
