# Useful alerts and recurring research

## What runs locally

`watch_sources.py` performs one bounded public scan, writes a private report and
stores source observations as pending events. `jobhunt_ops.py alerts` adds current
pipeline events and lists all pending events. Neither command sends a notification
or installs a schedule. The first run may surface the whole initial inventory;
review it as a baseline, not newly posted jobs. The source monitor is unfiltered
discovery; Codex must review fit before presenting a lead as a match.

Event kinds include new/changed/not-observed source listings, source failure and
recovery, onboarding gaps, eligible-for-review jobs, active form holds, parked
owner decisions and recorded receipts. Identical observations do not create new
events. Repeated reads keep undelivered events pending. A new failure after a
recovery is a new event. Source failures preserve the last complete snapshot.

```text
python jobhunt_ops.py alerts --vault "PRIVATE_VAULT"
python jobhunt_ops.py ack --vault "PRIVATE_VAULT" --id "DELIVERED_EVENT_ID" --delivered
```

Repeat `--id` to acknowledge several delivered events. Acknowledge only after
the chosen approved channel actually receives the update. `--delivered` records
your attestation; it cannot verify external delivery. A failed sender leaves
the event pending. There is no automatic ack or inbox connector.

## Agree on notification rules

Use private `templates/OWNER-POLICY.md`. The owner chooses channel, recipients,
permitted content, timezone, quiet hours, cadence and urgency. A local report can
be sufficient; app notifications, email or another service require the owner's
own configured account and authorization. Do not copy credentials, tenant IDs or
integration settings from a friend. Never put candidate PII in a public workflow.

Notify for meaningful new in-mandate opportunities, a verified approaching
deadline, a changed requirement that affects fit, a source outage that matters,
a confirmed application/interview/outcome, or a concrete owner decision. Consolidate
related events into a short update with exact identity, reason, deadline/timezone,
private evidence location and next action. Distinguish discovery from qualification.
Unchanged state should be quiet. Do not send repeated reminders merely because
an event remains pending; dedupe delivery using the event ID and sender history.

The CLI does not parse deadlines, interviews, mailbox replies or follow-up dates.
Codex reviews those from authorized sources and records them in private notes.
It must verify the source, dates and timezone before sending an urgent alert.

## Schedule only after one verified manual cycle

Use `prompts/SET-UP-ALERTS.md` to request setup on the friend's machine. In a Codex
app with scheduling tools, prefer its supported automation UI/tools. Agree on
the schedule and scope, create it with owner authorization, read back the saved
configuration, and record the actual ID, enabled state and cancellation procedure
privately. Check a real run and notification; saved configuration alone does not
prove execution or delivery. See the
[official scheduling documentation](https://learn.chatgpt.com/docs/automations).

If an app scheduler is unavailable, the owner can authorize their OS scheduler
to run a one-shot wrapper with an absolute Python executable, toolkit path,
private vault path and source config. Record its real task ID and logs; do not
invent an active schedule. The wrapper should run the monitor, retain its exit
code, and create/read pending alerts even when a source fails. No mail sender is
bundled. A scheduled local report is not a push notification.

Scheduled work stays source/review/report only. No employer forms, submissions,
outreach, installations, account changes, credential setup or mandate expansion.
One local writer/lock remains mandatory. Limit source count, requests and runtime.
On an occupied lock, report blocked rather than deleting it. Device availability,
network and scheduler behavior must be verified on that machine.

## Stop and cancellation

When the owner says stop monitoring or no more repeat check-ins, disable/delete
the actual scheduler task through its supported control, read back its state,
and report cancellation. Do not replace cancellation with another status report.
Preserve application holds and private evidence; stopping research is not release
of an uncertain submission. Do not acknowledge pending events as a cancellation.

Events describe observations at collection time. Before delivering a pending event,
recheck the current report and exact job. Consolidate or explain superseded states;
do not present an old eligible event as current when a claim or receipt now exists.
