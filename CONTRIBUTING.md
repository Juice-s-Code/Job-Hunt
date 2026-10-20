# Contributing

Use an isolated worktree and read AGENTS.md/HANDOFF.md before editing. Claim
non-overlapping files when sharing a checkout. Preserve others' dirty work;
stage explicit paths only. Test synthetic fixtures, never real candidate data.

Run the full suite and validate the allowlisted export as described in
docs/TESTING.md. Add focused regressions for changed behavior, especially source
coverage, identity, locks, privacy, event delivery and receipt ordering. Keep the
core standard-library-only unless the tradeoff is explicitly reviewed.

No PR may include personal documents, filled profiles, contacts, credentials,
browser/inbox captures, agent memories or private repository history. A pattern
scanner supplements review; it cannot certify arbitrary content is safe.

If adding a distributable file, update export_starter.py's exact FILES tuple.
Document what the new feature actually verifies and what it leaves unverified.
Never add a source failure path that turns unknown coverage into zero/closed,
or an automatic retry/takeover that can duplicate a real application.

Public changes should explain the resulting behavior, validation and limits.
Do not activate live schedules, call employer submit endpoints or send messages
as a test of this repository.
