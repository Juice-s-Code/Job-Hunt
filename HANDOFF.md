# Public toolkit maintenance handoff

## 2026-10-20 portable release

The public toolkit now includes Codex startup/continuation prompts, onboarding,
research and document procedures, supervised application controls, migration,
private reports, durable local alerts and a bounded public-source monitor.
START-HERE.md is the new owner's entrypoint. Candidate onboarding belongs in a
separate private vault; this maintenance note grants no application permission.

Verification: the clean exported code ran 72 synthetic tests successfully on
Windows, with one host-dependent symlink skip. The verifier also checked local
document links, JSON templates, archive contents and every manifest hash. CI
defines Windows/Linux checks on Python 3.10 and 3.14; inspect the actual run result
for a particular commit rather than treating workflow configuration as a pass.

The source snapshot and existing candidate vaults were read-only references.
No candidate documents, personal history, inboxes, forms, credentials, running
agents, integrations or schedulers were changed. New functionality is standard
library only. The exporter still requires an exact reviewed file allowlist.

Public implementation work used an isolated Git worktree and explicit staging.
No candidate/form file claims are held by this release. Future maintenance should
check Git status and claim disjoint paths before editing, run the whole suite,
and validate a fresh export. Keep candidate facts and private history out of Git.

External delivery, scheduling, rendered documents and live application outcomes
require the new owner's tools, authorization and observed evidence. They are not
verified by the synthetic suite. Follow docs/ALERTS.md and docs/INTEGRATIONS.md.
