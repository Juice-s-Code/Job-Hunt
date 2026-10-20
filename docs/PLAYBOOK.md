# The job-hunt operating cycle

The candidate's private vault is canonical. This public repository supplies the
tools and procedure. The owner's approved policy controls the current search;
neither another applicant's history nor a historical handoff supplies permission.

## Establish the search

Complete [ONBOARDING](ONBOARDING.md), write a private owner policy and evidence
bank, and verify `doctor` and `ledger`. For an existing search, use
[MIGRATION](MIGRATION.md) first. Agree on role families, locations, availability,
seniority, salary, exclusions, research time and application permissions. Keep
preferences separate from hard requirements. A location preference is not a ban.

Run a small pilot: a few employers, a handful of complete postings, one prepared
packet and one supervised application if authorized. Check that sources, screening,
documents, attachments and confirmations are correct before expanding volume.

## Daily cycle

1. **Reconcile.** Read the newest private handoff, owner policy, active claim and
   ledger. Inspect dirty files and pending owner questions. Run `doctor`, `ledger`
   and `jobhunt_ops.py report`. Any attempted/uncertain submission takes priority
   over another form. A lost tab or missing email never proves non-submission.
2. **Discover.** Use the approved employer list and [RESEARCH](RESEARCH.md).
   Run a bounded public scan or research official careers pages. Preserve complete
   text, URL, exact IDs, observation time and coverage. Job aggregators supply
   leads; confirm them with the employer. Count listings separately from verified
   eligible roles. A blocked endpoint is unknown coverage, not zero jobs.
3. **Qualify.** Check every hard mandate fact against the full posting. Unknowns
   stay review. Verify country/remote eligibility, program dates, required degree,
   experience, pay period/currency and applicant-AI restrictions. Manually dedupe
   office mirrors, job aliases and prior applications. `import-jobs` preserves
   identity; `review-job` records an audit trail while enriching only a never-claimed sourced record.
4. **Prioritize.** Sort by confirmed deadlines and fit, then evidence strength,
   candidate interest and preparation cost. A score only orders research; it
   cannot override eligibility. Surface an imminent verified deadline even when
   an owner decision blocks progress. Record unknown deadline timezone explicitly.
5. **Research and prepare.** Write a short employer/role brief and map each useful
   resume claim to approved evidence. Use [DOCUMENTS](DOCUMENTS.md) to build,
   render, inspect, hash and release the actual packet. The owner handles essays
   or assessments where authorship or employer rules prohibit AI assistance.
6. **Inspect one application.** Only after explicit application authority, eligible
   evidence and exact `claim`, inspect the full current form. Verify employer,
   requisition, account identity, required questions and document slots. Stop on
   unknown personal answers or owner-only gates. Opening/typing can transmit data.
7. **Submit under the approved scope.** Recheck current authority, all fields,
   exact released attachment hashes and terms. The core has no submit function.
   A supervised operator acts at most once. Any attempted Submit or ambiguous
   autosave keeps the exact/global hold until reconciliation. `park --unsent`
   is only an attestation of actual clean, definitely-unsent cessation.
8. **Confirm and close.** Preserve employer-side evidence, verify candidate/job
   identity and exactly one matching inbox confirmation, then use `receipt`.
   Record the actual submitted resume hash. Run `ledger`; a tool response, click
   or uploaded file alone adds no application. Record blockers and handoff.
9. **Alert.** Review pending events, consolidate useful updates, deliver through
   the approved channel and acknowledge only delivered event IDs. Stay quiet on
   unchanged state. [ALERTS](ALERTS.md) separates local events from delivery.

## Weekly review

Compare unique confirmed applications, replies, interviews and known outcomes.
Keep interview/outcome observations in private notes; the core ledger counts
confirmed applications only. Review conversion by role/source and ask the owner
before changing the mandate. Avoid drawing conclusions from a tiny sample.

Revisit stale sources, changed postings, blocked answers, unanswered follow-ups,
deadlines and duplicate aliases. Refresh evidence and resume releases when facts
change. Review permissions, scheduler health, pending notifications and backups.
Do not treat repeated daily zeroes as progress or silently expand the search.

## Owner-only and evidence boundaries

Accounts, credentials, CAPTCHA, human-verification codes, SSN/ITIN, compensation
expectations, test scores, referrals, legal/authorship attestations, offers and
spending stop the default workflow for the owner. Optional demographic fields
remain untouched. No applicant facts may be inferred from silence.

An employer's applicant no-AI prohibition ends all AI work on that application.
The candidate handles it manually. An employer using AI in hiring is a different
fact; read the actual applicant terms. Never change a known prohibition to pass
screening. Tool denials and failed checks require resolution, not a workaround.

## Coordination and reporting

One writer per file and one active form per private vault. Optional parallel
research needs acknowledged, disjoint assignments. A coordinator note is not
proof that a worker accepted or ceased. Do not take over a claim by age.

Every closeout states: observations and source coverage; prepared versus released
documents; actual form/data/Submit activity; receipt-backed count; held tasks;
owner decisions; exact private report/handoff paths. Templates are in `templates/`.
