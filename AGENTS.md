# Portable job-hunt operating contract

This is a reusable framework, not a candidate vault. Codex reads `CODEX.md`; other agents follow the same contract. Read `docs/SCHEMA.md` for commands and `docs/PLAYBOOK.md` for the full cycle. Every agent and human operator follows the same exact-job and single-writer controls. Markdown is guidance, not a sandbox; retain normal permission mechanisms and human supervision.

## Candidate isolation

Only the new owner's explicitly approved external vault is canonical. Never read or copy a parent candidate repository, history, resumes, contacts, profile answers, secrets, live workflow resources or installed agent memories. The starter includes no real candidate facts. Test fixtures are synthetic and never become application evidence. Stop if global/ancestor instructions inject another person's facts.

Before work, inspect current Git/file state, private `Cursor.MD/HERMES COORDINATION.md`, `STATE.md`, `HANDOFF.md`, `SUBMIT LOCK.md`, the ledger, candidate mandate and approved evidence. A newer explicit owner policy controls; archived counts and roles are not authority. Never overwrite another writer's dirty files. Use a new disjoint handoff if ownership is unclear.

## Workflow

1. **Onboard:** owner interview; approve new external private path; `init`; approved profile/evidence; `doctor`; empty `ledger`. No applications during onboarding.
2. **Source:** complete public employer text and canonical URL, exact IDs, recorded evidence. `source_jobs.py` supplies unverified Greenhouse records. Save batches outside the framework. Read back/dedupe/count in code and state bounded coverage honestly.
3. **Review:** `import-jobs`, inspect full source, then explicit `review-job` enrichment of never-claimed sourced records. Unknown evidence remains review. No-AI means owner-manual, never prepare/claim. Disclosed compensation, graduation/start windows, minimum qualifications and program type must agree with the owner's mandate.
4. **Claim:** run `screen`; dedupe employer/role mirrors across applications and holds; `claim` exact returned key with stable actual operator label before first form navigation. One global active form. No auto-expiry or takeover.
5. **Inspect and prepare:** actual current form, all requirements/footer, document slots and hard stops. Evidence-only resume/cover selection, byte/hash and visual QA. Never alter transcripts. Stop for unknown personal answers and owner-only gates. Tool denial is not a reason to switch methods.
6. **Supervise:** final review/submit is outside the CLI. Obtain human authorization, maintain same exact claim and operator, and record whether data/upload/consent/Submit occurred. No n8n submission and no blind retry.
7. **Confirm:** employer/portal evidence plus exactly one matching inbox confirmation and verified current mailbox identity. Save private evidence. `receipt` hashes actual submitted resume/evidence and precedes applied bookkeeping. `ledger` reconciles and supplies counts; mismatches fail loudly.
8. **Hand back:** safe cessation or retained hold, exact last state, blockers and next permitted action. On clean definitely-unsent tasks only, `park` with owner/reason. Dirty, autosaved, ambiguous or attempted-Submit tasks retain both exact/global hold until explicit owner reconciliation.

## Coordination

Default: one Codex instance and supervising owner; other agents and Hermes are optional. If multiple agents work, route all assignments/questions/blockers/handoffs through the owner's chosen coordinator. Assign exact read/write paths, public targets/ATS IDs, allowed tools, bounded objective, forbidden actions and stop conditions. Receive explicit acceptance. No permanent model privilege, simultaneous form control or dual-writing. Process existence, queue delivery and a changed note do not prove acceptance or cessation.

A handoff records:

- Exact task/job key/ATS ID and actual operator.
- Verified current claim and files still occupied.
- Source/packet paths, real hashes and observed results.
- Full last URL/state; any field entry, autosave risk, attachment, consent or Submit attempt.
- Employer evidence versus tool failure versus unknown; exact required owner field.
- Explicit operator cessation and whether clean park or dirty/global hold applies.
- Safe next action and what is broken, including evidence distinguishing possible causes.

## Distribution boundary

Keep all candidate vaults private and separate from source code. Do not run `git add .` over candidate data or distribute a clone/fork/archive of a private vault. Share only `export_starter.py`'s reviewed allowlisted ZIP, with its verified manifest; a clean standalone repository may be initialized from those files with new history and explicit owner publication permission. No automatic remote visibility changes, pushes or account invitations. `.gitignore` is neither encryption nor a privacy guarantee.
