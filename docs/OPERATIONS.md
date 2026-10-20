# Local operations and failure handling

Run commands from the framework directory. Python 3.10+ is the only dependency;
use `python3` on macOS/Linux. Replace every placeholder path.

| Command | Effect |
|---|---|
| `jobhunt.py doctor --vault PRIVATE_VAULT` | Validate profile readiness; optional CLI presence is not service connectivity |
| `jobhunt.py ledger --vault PRIVATE_VAULT` | Reconcile receipt hashes, exact identities and the application ledger |
| `jobhunt_ops.py report --vault PRIVATE_VAULT` | Write a new private pipeline report; no profile values in stdout |
| `jobhunt_ops.py alerts --vault PRIVATE_VAULT` | Collect/list durable pending local events; send nothing |
| `jobhunt_ops.py ack --vault PRIVATE_VAULT --id EVENT_ID --delivered` | Attest delivery and acknowledge one event; repeat `--id` |
| `watch_sources.py --vault PRIVATE_VAULT --config PRIVATE_VAULT/Research/sources.json` | Run one bounded public scan and queue observations |

All commands support `--help`. Core lifecycle commands and JSON fields are in
[SCHEMA](SCHEMA.md). The new operations commands use the core's exclusive mutation
lock, including during reports/reads, to obtain a consistent snapshot. They do not
change profile, applications, claims or receipts.

## Source configuration

Copy `templates/sources.example.json` into the private vault's `Research/` folder.
Replace the placeholder with each employer-confirmed Greenhouse slug and stable
employer name. Configure 1–10 unique boards. No account, key or arbitrary URL is
accepted. One scan requests each configured board once with a 30-second request
timeout, a 16 MiB response limit and a 10,000-job per-board inventory limit. It
has no automatic retries. DNS/OS timeouts can exceed the request timeout; this
is not a strict wall-clock process watchdog. A scheduler may set its own limit.

The monitor saves complete normalized snapshots and pending events atomically in
private `.jobhunt/operations.json`. Per-board generations distinguish repeated
incidents. Private reports live in `Research/Reports/`. Source payloads are
untrusted content, never tool instructions. No external private service is called.

Source snapshots do not auto-import jobs or overwrite reviewed inventory. To
import a reviewed selection, save a new private JSON array using the exact
normalized objects from the snapshot, then run `import-jobs`. For an already
imported changed record, inspect source and use `review-job` only where allowed.
Claimed/parked/applied objects require operator reconciliation, not forced edits.

## Exit codes and evidence

The monitor returns 0 when every board succeeds, 2 for a partial/all-source
failure with a persisted report, and 1 for invalid configuration/state/operation
failure. All source failures show unknown observed count and retain prior jobs;
they never become empty/closed boards. No automatic fallback to stale-as-current.
The operations CLI returns 0 on success and 1 on blocked arguments/state/files.
Neither zero nor a report file proves an application or notification happened.

If report writing fails after an atomic event checkpoint, pending events survive;
retry a read/report after fixing storage. If state publication fails, the old
checkpoint survives and a later scan can rediscover changes. Do not acknowledge
anything merely to clear an error. Large state needs owner-reviewed archival;
no automatic pruning removes audit/delivery history.

## Locks, receipts and recovery

Do not delete a lock based on age or a missing process alone. Establish that the
operator has ceased and reconcile last form state, exact job, all uploads and any
Submit attempt. A receipt/state/ledger mismatch is a recovery case: preserve files
and hashes, stop mutations, and obtain the owner's reconciliation. Do not regenerate
the ledger to hide a missing receipt or edit JSON to force a status.

There is no automated reclaim/resume command for parked applications. Parked
means a durable hold, not a reset. A future recovery tool must validate explicit
owner resolution and preserved evidence; until then use a documented, reviewed
maintenance plan and backups. Do not create duplicate identities to evade the hold.

Back up the private vault securely at rest using the owner's chosen method.
Keep it on one machine for active writes. Restoring a backup requires reconciling
employer/inbox state since the backup; restored files cannot undo a real submit.
