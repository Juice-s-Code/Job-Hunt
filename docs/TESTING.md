# Verification and release

The suite uses synthetic records and temporary vaults. It never submits, sends
messages or requires live employer/accounts. Run:

```text
python -B -m unittest discover -s tests -v
python -B -m json.tool templates/n8n-greenhouse-source.json
python -B -m json.tool templates/sources.example.json
python export_starter.py --output "NEW_RELEASE_PATH.zip"
```

Use `python3` on macOS/Linux. Require nonzero tests and inspect skips. Symlink
tests may skip when a host cannot create them; Windows junction tests are Windows
only. CI runs supported Python versions on Windows and Linux and tests a clean
export extracted outside the checkout. These tests do not prove live ATS access,
document rendering, inbox provenance, scheduler execution or notification delivery.

If a machine's default temporary directory sits under `.git`, `AGENTS.md` or
`CLAUDE.md`, select an approved writable temporary directory outside those
hierarchies and set TEMP/TMP/TMPDIR for that process only. The initialization
guard intentionally rejects inherited candidate instruction trees. Do not delete
instruction files or weaken the guard to pass a test.

The exporter validates exact allowlisted source files, links, file identity,
stable metadata, patterns, ZIP bytes and a manifest. Windows path stat and handle
fstat can expose different ctime semantics; stability comparisons use the same
API before/after, while path and handle identity still must match. Run exports
from a trusted quiescent tree and recheck the output hash at distribution.

For a release, inspect all tracked filenames and changed content, run the suite,
export a new bundle, verify every manifest hash, extract into a new directory and
run the suite there. A ZIP hash proves byte identity, not absence of every secret.
Keep candidate files out of public Git and manually review the release boundary.
