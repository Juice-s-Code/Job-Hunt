#!/usr/bin/env python3
"""Candidate-neutral, offline job-hunt records. Python 3.10+ standard library."""
import argparse
from contextlib import contextmanager
from datetime import date, datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unicodedata

FRAMEWORK = Path(__file__).resolve().parent
VERSION = 1
MAX_JSON_BYTES = 16 * 1024 * 1024
JOB_FIELDS = {"employer", "ats", "id", "title", "url", "country", "location", "role_family",
              "employment_type", "internship", "min_years_experience", "start_date",
              "source_text", "salary_min", "salary_currency", "salary_period", "no_ai"}
CANDIDATE_FIELDS = {"display_name", "email", "school", "degree", "graduation_date", "earliest_start"}
MANDATE_FIELDS = {"role_families", "countries", "preferred_locations", "salary_floor",
                  "salary_currency", "max_required_experience_years", "full_time_only",
                  "allow_internships"}
REVIEW_IDENTITY = ("employer", "ats", "id", "title", "url")


class Problem(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Problem(message)


def text(value, field, *, empty=False, multiline=False, padding=False):
    require(type(value) is str, field + ": expected text")
    require(len(value) <= (1000000 if multiline else 1000), field + ": text too long")
    require(empty or bool(value.strip()), field + ": empty text")
    require(not any(unicodedata.category(c) in {"Cc", "Cf", "Cs"}
                    and not (multiline and c in "\r\n\t") for c in value),
            field + ": unsafe control character")
    if not multiline and not padding:
        require(value == value.strip(), field + ": surrounding whitespace is not allowed")
    return value


def nullable_text(value, field):
    if value is not None:
        text(value, field)


def number(value, field, *, nullable=False):
    if nullable and value is None:
        return
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            field + ": expected finite nonnegative number")


def boolean(value, field, *, nullable=False):
    require(type(value) is bool or (nullable and value is None), field + ": expected boolean")


def iso_date(value, field, *, nullable=True):
    if nullable and value is None:
        return
    require(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is not None,
            field + ": expected ISO date")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise Problem(field + ": invalid date") from None


def fields(obj, expected, label):
    require(type(obj) is dict and set(obj) == expected, label + ": invalid or unknown fields")


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "JSON contains duplicate keys")
        result[key] = value
    return result


def invalid_constant(value):
    raise Problem("JSON contains a nonfinite number")


def read_json(path):
    safe_path(path)
    try:
        require(path.is_file(), "Required JSON file is missing")
        require(path.stat().st_size <= MAX_JSON_BYTES, "JSON file is too large")
        return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=no_duplicates,
                          parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise Problem("Invalid JSON document") from None


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def linked(path):
    try:
        stat = path.lstat()
        return path.is_symlink() or bool(getattr(stat, "st_file_attributes", 0) & 0x400)
    except FileNotFoundError:
        return False


def safe_path(path):
    for part in [path, *path.parents]:
        require(not linked(part), "Symlink or reparse-point paths are not allowed")


def vault_path(raw):
    p = Path(raw).expanduser().absolute()
    safe_path(p)
    p = p.resolve()
    require(p != FRAMEWORK and FRAMEWORK not in p.parents,
            "The private vault must be outside the starter framework")
    return p


def atomic_write(path, content):
    """Publish a fully flushed file without exposing a partial replacement."""
    safe_path(path)
    data = content if isinstance(content, bytes) else content.encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    temp = Path(tmp)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


@contextmanager
def mutation_lock(vault):
    directory = vault / ".jobhunt"
    require(directory.is_dir(), "Vault is not initialized")
    safe_path(directory)
    path = directory / "mutation.lock"
    safe_path(path)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise Problem("Exclusive lock exists; owner/manual recovery is required") from None
    identity = os.fstat(fd)
    token = os.urandom(24).hex()
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "created": now(), "token": token}))
            handle.flush()
            os.fsync(handle.fileno())
        yield
    finally:
        # Manual recovery must wait for cessation. If it nevertheless overlaps,
        # a prior invocation must not remove a replacement owner's lock.
        try:
            current = path.lstat()
            if (not linked(path) and (current.st_dev, current.st_ino) ==
                    (identity.st_dev, identity.st_ino) and current.st_size <= 4096):
                data = json.loads(path.read_text(encoding="utf-8"))
                if type(data) is dict and data.get("token") == token:
                    path.unlink()
        except (OSError, ValueError, UnicodeError):
            pass  # Missing/replaced/unreadable locks require manual review, not deletion.


def now():
    return datetime.now(timezone.utc).isoformat()


def hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


def key_for(job):
    identity = [job["employer"], job["ats"], job["id"]]
    return hash_bytes(json.dumps(identity, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def target_for(job):
    """A display rename cannot create a second copy of the same literal target."""
    return job["ats"], job["id"], job["url"]


def validate_job(job):
    fields(job, JOB_FIELDS, "Job")
    for name in ["employer", "ats", "id"]:
        text(job[name], name)
    text(job["title"], "title", padding=True)
    require(re.fullmatch(r"[a-z][a-z0-9_-]*", job["ats"]) is not None, "Invalid ATS kind")
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]*", job["id"]) is not None
            and ".." not in job["id"], "Invalid exact ATS identifier")
    text(job["url"], "url")
    from urllib.parse import urlsplit
    try:
        url = urlsplit(job["url"])
        require(url.scheme in {"https", "http"} and bool(url.hostname)
                and not url.username and not url.password, "Invalid public source URL")
        require(not any(c.isspace() for c in job["url"]), "Invalid public source URL")
    except ValueError:
        raise Problem("Invalid public source URL") from None
    for name in ["country", "location", "role_family", "employment_type",
                 "salary_currency", "salary_period"]:
        nullable_text(job[name], name)
    if job["country"] is not None:
        require(re.fullmatch("[A-Z]{2}", job["country"]) is not None, "Invalid country code")
    if job["salary_currency"] is not None:
        require(re.fullmatch("[A-Z]{3}", job["salary_currency"]) is not None, "Invalid currency")
    boolean(job["internship"], "internship", nullable=True)
    boolean(job["no_ai"], "no_ai", nullable=True)
    number(job["min_years_experience"], "min_years_experience", nullable=True)
    number(job["salary_min"], "salary_min", nullable=True)
    iso_date(job["start_date"], "start_date")
    text(job["source_text"], "source_text", empty=True, multiline=True)
    return job


def profile(vault):
    p = read_json(vault / "Profile/candidate.json")
    fields(p, {"candidate", "mandate"}, "Profile")
    c, m = p["candidate"], p["mandate"]
    fields(c, CANDIDATE_FIELDS, "Candidate")
    fields(m, MANDATE_FIELDS, "Mandate")
    for name in ["display_name", "email", "school", "degree"]:
        text(c[name], name, empty=True)
    iso_date(c["graduation_date"], "graduation_date")
    iso_date(c["earliest_start"], "earliest_start")
    for name in ["role_families", "countries", "preferred_locations"]:
        require(type(m[name]) is list, name + ": expected list")
        for item in m[name]:
            text(item, name)
        require(len(set(m[name])) == len(m[name]), name + ": duplicate values")
    require(all(re.fullmatch("[A-Z]{2}", item) for item in m["countries"]), "Invalid mandate country")
    text(m["salary_currency"], "salary_currency")
    require(re.fullmatch("[A-Z]{3}", m["salary_currency"]) is not None, "Invalid mandate currency")
    number(m["salary_floor"], "salary_floor", nullable=True)
    number(m["max_required_experience_years"], "max_required_experience_years")
    boolean(m["full_time_only"], "full_time_only")
    boolean(m["allow_internships"], "allow_internships")
    missing = [name for name in ["display_name", "email", "earliest_start"] if not c[name]]
    if c["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", c["email"]):
        missing.append("valid_email")
    missing += [name for name in ["role_families", "countries"] if not m[name]]
    if m["salary_floor"] is None:
        answers = vault / "Profile/Owner Answers.md"
        safe_path(answers)
        if not answers.is_file() or not answers.read_text(encoding="utf-8").strip():
            missing.append("owner_salary_approval_record")
    return p, missing


def require_ready(vault):
    p, missing = profile(vault)
    require(not missing, "Onboarding incomplete: " + ", ".join(missing))
    return p


def markdown(value):
    return value.replace("\\", "\\\\").replace("|", "\\|")


def ledger_text(state):
    lines = ["# Application Ledger", "", "| Key | Employer | Role | Receipt |",
             "|---|---|---|---|"]
    for key, record in sorted(state["jobs"].items()):
        if record["status"] == "applied":
            job = record["job"]
            lines.append("| " + key + " | " + markdown(job["employer"]) + " | "
                         + markdown(job["title"]) + " | " + key + ".json |")
    return "\n".join(lines) + "\n"


def load_state(vault):
    state = read_json(vault / ".jobhunt/state.json")
    fields(state, {"version", "jobs", "active"}, "State")
    require(type(state["version"]) is int and state["version"] == VERSION, "Unsupported state version")
    require(type(state["jobs"]) is dict, "Invalid jobs state")
    require(state["active"] is None or type(state["active"]) is str, "Invalid active claim")
    active = []
    receipts = set()
    targets = set()
    for key, record in state["jobs"].items():
        require(type(key) is str and re.fullmatch("[0-9a-f]{64}", key), "Invalid state key")
        base_fields = {"job", "status", "owner", "reason", "receipt_sha256"}
        require(type(record) is dict and set(record) in
                (base_fields, base_fields | {"history"}), "Job state: invalid or unknown fields")
        validate_job(record["job"])
        require(key_for(record["job"]) == key, "Exact job identity mismatch")
        target = target_for(record["job"])
        require(target not in targets, "Duplicate exact ATS/ID/URL target; manual reconciliation required")
        targets.add(target)
        history = record.get("history", [])
        require(type(history) is list, "Invalid review audit history")
        for version in history:
            fields(version, {"job", "reviewed_utc"}, "Review audit")
            validate_job(version["job"])
            text(version["reviewed_utc"], "reviewed_utc")
            require(all(version["job"][n] == record["job"][n] for n in REVIEW_IDENTITY),
                    "Review audit identity mismatch")
            require(version["job"]["no_ai"] is not True or record["job"]["no_ai"] is True,
                    "Previously established no-AI restriction was cleared")
        require(record["status"] in {"imported", "claimed", "parked", "applied"}, "Invalid job status")
        for name in ["owner", "reason", "receipt_sha256"]:
            nullable_text(record[name], name)
        if record["status"] == "claimed":
            require(record["owner"] is not None, "Claim has no owner")
            active.append(key)
        if record["status"] == "imported":
            require(record["owner"] is None and record["reason"] is None,
                    "Sourced job contains an ownership checkpoint")
        if record["status"] in {"parked", "applied"}:
            require(record["owner"] is not None, "Checkpoint has no owner")
        if record["status"] == "parked":
            require(record["reason"] is not None, "Parked job has no reason")
        if record["status"] == "applied":
            receipts.add(key + ".json")
            rp = vault / "Receipts" / (key + ".json")
            receipt = read_json(rp)
            fields(receipt, {"key", "owner", "recorded_utc", "employer", "ats", "id",
                             "evidence_sha256", "resume_sha256", "evidence_file",
                             "confirmation_count", "identity_verified"}, "Receipt")
            require(record["receipt_sha256"] == hash_bytes(rp.read_bytes()), "Receipt hash mismatch")
            require(receipt["key"] == key and receipt["owner"] == record["owner"],
                    "Receipt identity mismatch")
            require(all(receipt[n] == record["job"][n] for n in ["employer", "ats", "id"]),
                    "Receipt exact employer/ATS identity mismatch")
            require(type(receipt["confirmation_count"]) is int and receipt["confirmation_count"] == 1
                    and receipt["identity_verified"] is True, "Receipt verification mismatch")
            for name in ["evidence_sha256", "resume_sha256"]:
                require(type(receipt[name]) is str and re.fullmatch("[0-9a-f]{64}", receipt[name]),
                        "Invalid receipt digest")
            require(receipt["evidence_file"] == key + ".evidence", "Invalid evidence filename")
            ep = vault / "Receipts" / receipt["evidence_file"]
            safe_path(ep)
            require(ep.is_file() and ep.stat().st_size > 0
                    and hash_bytes(ep.read_bytes()) == receipt["evidence_sha256"],
                    "Receipt evidence mismatch")
        else:
            require(record["receipt_sha256"] is None, "Unapplied job contains receipt bookkeeping")
    require(active == ([] if state["active"] is None else [state["active"]]),
            "Global active-claim mismatch")
    receipt_dir = vault / "Receipts"
    safe_path(receipt_dir)
    require(receipt_dir.is_dir(), "Receipt directory missing")
    require({p.name for p in receipt_dir.glob("*.json")} == receipts,
            "Receipt/state mismatch; owner/manual reconciliation is required")
    expected_evidence = {name[:-5] + ".evidence" for name in receipts}
    require({p.name for p in receipt_dir.glob("*.evidence")} == expected_evidence,
            "Receipt evidence/state mismatch; owner/manual reconciliation is required")
    ledger = vault / "Applications/Application Ledger.md"
    safe_path(ledger)
    require(ledger.is_file() and ledger.read_bytes() == ledger_text(state).encode("utf-8"),
            "Ledger/receipt state mismatch; owner/manual reconciliation is required")
    return state


def save_state(vault, state):
    atomic_write(vault / ".jobhunt/state.json", json_bytes(state))


def initialize(vault):
    require(not any((ancestor / marker).exists() or (ancestor / marker).is_symlink()
                    for ancestor in vault.parents for marker in [".git", "CLAUDE.md", "AGENTS.md"]),
            "Vault must be outside existing Git and agent-instruction hierarchies")
    require(not vault.exists() or vault.is_dir(), "Vault destination is not a directory")
    require(not vault.exists() or not any(vault.iterdir()), "Refusing existing nonempty vault")
    if not vault.exists():
        vault.mkdir(parents=True, mode=0o700)
    # Exclusive directory creation reserves initialization across processes.
    try:
        (vault / ".jobhunt").mkdir(mode=0o700)
    except FileExistsError:
        raise Problem("Vault initialization already reserved") from None
    with mutation_lock(vault):
        for folder in ["Profile", "Applications", "Receipts", "Resume", "Cover Letters",
                       "Research", "Networking", "Jobs/Sourced", "Cursor.MD"]:
            (vault / folder).mkdir(parents=True, mode=0o700)
        blank = {"candidate": {"display_name": "", "email": "", "school": "", "degree": "",
                                "graduation_date": None, "earliest_start": None},
                 "mandate": {"role_families": [], "countries": [], "preferred_locations": [],
                             "salary_floor": None, "salary_currency": "USD",
                             "max_required_experience_years": 1, "full_time_only": True,
                             "allow_internships": False}}
        state = {"version": VERSION, "jobs": {}, "active": None}
        files = {
            "Profile/candidate.json": json_bytes(blank),
            "Profile/Owner Answers.md": "",
            "Profile/Evidence.md": "# Verified experience evidence\n\n",
            "AGENTS.md": "# Independent job hunt\n\nUse only this owner's verified facts and answers. Coordinate one writer per file and one active application. Never submit automatically. Unknowns require review; receipts precede applied status.\n",
            "CLAUDE.md": "# Claude Code entrypoint\n\nRead AGENTS.md and Cursor.MD/HERMES COORDINATION.md. Complete this owner's onboarding before screening. Never reuse another person's data.\n",
            "CODEX.md": "# Codex entrypoint\n\nRead AGENTS.md, Profile/Owner Answers.md and Cursor.MD/HANDOFF.md. Use the separate public toolkit's CODEX.md for the operating procedure. Private CLI state controls exact claims. Never infer applicant facts or release an ambiguous submission hold.\n",
            "Cursor.MD/HERMES COORDINATION.md": "# Coordination\n\nThe owner designates the coordinator. Assign exact jobs and file ownership. Claim before forms; park with cessation; never bypass another owner or an outstanding hold.\n",
            "Cursor.MD/SUBMIT LOCK.md": "# Submission control\n\nThe private CLI state is authoritative for atomic claims. Use claim, park and receipt; no automatic expiry. No active application at initialization.\n",
            "Cursor.MD/STATE.md": "# State\n\nOnboarding incomplete. No applications. Use doctor and ledger for current counts.\n",
            "Cursor.MD/HANDOFF.md": "# Handoff\n\nRecord exact task, owner, evidence and cessation here. No assignment yet.\n",
            "Applications/Application Ledger.md": ledger_text(state),
            ".gitignore": "# This private vault is excluded from accidental Git staging.\n*\n!.gitignore\n",
        }
        for name, content in files.items():
            atomic_write(vault / name, content)
        save_state(vault, state)
    return {"initialized": True, "ready": False, "applications": 0}


def assessment(job, mandate, candidate):
    reasons, gaps = [], []
    if job["no_ai"] is True:
        return "OWNER_MANUAL", ["Employer prohibits AI assistance"], []
    if job["no_ai"] is None:
        gaps.append("AI policy evidence unknown")
    if not job["source_text"].strip():
        gaps.append("Source text missing")
    for name in ["start_date", "employment_type", "internship", "min_years_experience",
                 "country", "location", "role_family"]:
        if job[name] is None:
            gaps.append(name + " evidence unknown")
    if job["start_date"] is not None and job["start_date"] < candidate["earliest_start"]:
        reasons.append("Start precedes owner availability")
    if job["country"] is not None and job["country"] not in mandate["countries"]:
        reasons.append("Country outside mandate")
    if job["role_family"] is not None and job["role_family"] not in mandate["role_families"]:
        reasons.append("Role family outside mandate")
    if job["employment_type"] is not None:
        if job["employment_type"] not in {"full_time", "part_time", "contract", "temporary"}:
            gaps.append("Employment classification unrecognized")
        elif mandate["full_time_only"] and job["employment_type"] != "full_time":
            reasons.append("Not full time")
    if job["internship"] is True and not mandate["allow_internships"]:
        reasons.append("Internship outside mandate")
    if job["min_years_experience"] is not None and job["min_years_experience"] > mandate["max_required_experience_years"]:
        reasons.append("Required experience exceeds mandate")
    if job["salary_min"] is not None:
        if job["salary_currency"] != mandate["salary_currency"] or job["salary_period"] != "annual":
            gaps.append("Salary currency/period requires owner review")
        elif mandate["salary_floor"] is not None and job["salary_min"] < mandate["salary_floor"]:
            reasons.append("Disclosed annual salary below floor")
    elif ((job["salary_currency"] is not None and job["salary_currency"] != mandate["salary_currency"])
          or job["salary_period"] not in {None, "annual"}):
        gaps.append("Salary currency/period requires owner review")
    if re.search(r"\b(senior|sr\.?|vice president|vp|director|manager|principal|head|lead)\b", job["title"], re.I):
        gaps.append("Title seniority requires verification")
    if re.search(r"\b(MBA|Ph\.?D\.?|doctorate|master'?s)\b.{0,45}\b(required|mandatory|must)\b|\b(require[sd]?|must have)\b.{0,45}\b(MBA|Ph\.?D\.?|doctorate|master'?s)\b",
                 job["source_text"], re.I | re.S):
        gaps.append("Advanced degree requirement needs owner verification")
    return ("ineligible" if reasons else "review" if gaps else "eligible"), reasons, gaps


def screen_jobs(vault, state):
    p = require_ready(vault)
    rows = []
    for key, record in sorted(state["jobs"].items()):
        status, reasons, gaps = assessment(record["job"], p["mandate"], p["candidate"])
        if record["status"] in {"parked", "applied", "claimed"}:
            status = record["status"]
            reasons = ["Existing " + record["status"] + " state is retained"] + reasons
        rows.append({"key": key, "status": status, "reasons": reasons, "evidence_gaps": gaps})
    return rows


def import_jobs(vault, state, source):
    jobs = read_json(Path(source).expanduser().absolute())
    require(type(jobs) is list, "Job input must be a JSON array")
    pending = {}
    keys = []
    for job in jobs:
        validate_job(job)
        key = key_for(job)
        existing = state["jobs"].get(key, pending.get(key))
        if existing is not None:
            require(existing["job"] == job, "Conflicting data for an exact job; manual review required")
        else:
            require(not any(target_for(r["job"]) == target_for(job)
                            for r in [*state["jobs"].values(), *pending.values()]),
                    "Display rename collides with an existing exact ATS/ID/URL target")
            pending[key] = {"job": job, "status": "imported", "owner": None,
                            "reason": None, "receipt_sha256": None, "history": []}
        keys.append(key)
    state["jobs"].update(pending)
    save_state(vault, state)
    return {"imported": len(pending), "duplicates": len(jobs) - len(pending), "keys": keys}


def review_job(vault, state, key, source):
    require(key in state["jobs"], "Unknown exact job key")
    record = state["jobs"][key]
    require(record["status"] == "imported" and record["owner"] is None,
            "Only sourced, never-claimed jobs can be reviewed")
    job = validate_job(read_json(Path(source).expanduser().absolute()))
    require(all(job[n] == record["job"][n] for n in REVIEW_IDENTITY),
            "Review must preserve exact employer/ATS/id/title/URL")
    require(record["job"]["no_ai"] is not True or job["no_ai"] is True,
            "Review cannot clear a known no-AI prohibition")
    record.setdefault("history", []).append({"job": record["job"], "reviewed_utc": now()})
    record["job"] = job
    save_state(vault, state)
    return {"key": key, "status": "imported", "reviewed": True,
            "prior_versions": len(record["history"])}


def owned(state, key, owner):
    text(owner, "owner")
    require(key in state["jobs"], "Unknown exact job key")
    record = state["jobs"][key]
    require(state["active"] == key and record["status"] == "claimed"
            and record["owner"] == owner, "An owned active claim is required")
    return record


def claim(vault, state, key, owner):
    text(owner, "owner")
    require(key in state["jobs"], "Unknown exact job key")
    require(state["active"] is None, "Another form claim is active")
    record = state["jobs"][key]
    require(record["status"] == "imported", "Job is already claimed, parked or applied")
    p = require_ready(vault)
    status, _, _ = assessment(record["job"], p["mandate"], p["candidate"])
    require(status == "eligible", "Job is not eligible; review or owner/manual work required")
    job = record["job"]
    for other in state["jobs"].values():
        same_role = (other["job"]["employer"].casefold() == job["employer"].casefold()
                     and other["job"]["title"].casefold() == job["title"].casefold())
        require(not (same_role and other["status"] in {"claimed", "parked", "applied"}),
                "Same-employer role variant has an existing claim, hold or application")
    record.update(status="claimed", owner=owner)
    state["active"] = key
    save_state(vault, state)
    return {"key": key, "status": "claimed"}


def park(vault, state, key, owner, reason, *, unsent=False):
    record = owned(state, key, owner)
    require(unsent is True, "Park requires --unsent attestation; ambiguous submissions keep the active hold")
    text(reason, "reason")
    record.update(status="parked", reason=reason)
    state["active"] = None
    save_state(vault, state)
    return {"key": key, "status": "parked", "control_released": True}


def receipt(vault, state, args):
    record = owned(state, args.key, args.owner)
    require(type(args.confirmation_count) is int and args.confirmation_count == 1,
            "Exactly one matching confirmation is required")
    require(args.identity_verified, "Operator identity/provenance verification is required")
    blobs = []
    for raw in [args.evidence, args.resume]:
        p = Path(raw).expanduser().absolute()
        safe_path(p)
        require(p.is_file() and p.stat().st_size > 0, "Evidence and resume must be nonempty real files")
        require(p.stat().st_size <= 64 * 1024 * 1024, "Evidence or resume file is too large")
        blobs.append(p.read_bytes())
    key = args.key
    rp = vault / "Receipts" / (key + ".json")
    ep = vault / "Receipts" / (key + ".evidence")
    require(not rp.exists() and not ep.exists(), "Receipt artifacts already exist; reconcile manually")
    data = {"key": key, "owner": args.owner, "recorded_utc": now(),
            "employer": record["job"]["employer"], "ats": record["job"]["ats"], "id": record["job"]["id"],
            "evidence_sha256": hash_bytes(blobs[0]), "resume_sha256": hash_bytes(blobs[1]),
            "evidence_file": ep.name, "confirmation_count": 1, "identity_verified": True}
    # Any interruption retains the active claim or causes a detectable receipt/state/ledger mismatch.
    atomic_write(ep, blobs[0])
    atomic_write(rp, json_bytes(data))
    record.update(status="applied", receipt_sha256=hash_bytes(rp.read_bytes()))
    state["active"] = None
    save_state(vault, state)
    atomic_write(vault / "Applications/Application Ledger.md", ledger_text(state))
    load_state(vault)
    return {"key": key, "status": "applied", "receipt_sha256": record["receipt_sha256"]}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Problem("Invalid command arguments; use --help")


def parser():
    p = Parser(prog="jobhunt", description="Offline private job-hunt records; never submits applications.")
    commands = p.add_subparsers(dest="command", required=True)
    helptext = {
        "init": "Create a new empty private vault outside this framework.",
        "doctor": "Check onboarding and optional local CLI presence without exposing values.",
        "import-jobs": "Transactionally import a normalized JSON job array.",
        "review-job": "Audit and enrich one sourced, never-claimed job without changing its identity.",
        "screen": "Screen explicit evidence against the completed owner mandate.",
        "claim": "Atomically reserve one eligible exact job and global form control.",
        "park": "Record definitely-unsent clean cessation; ambiguous Submit keeps the active claim.",
        "receipt": "Record operator-verified receipt before ledger; does not submit or check inbox.",
        "ledger": "Verify receipt-backed canonical ledger and report actual counts.",
    }
    for name, description in helptext.items():
        sub = commands.add_parser(name, help=description, description=description)
        sub.add_argument("--vault", required=True)
        if name in {"import-jobs", "review-job"}:
            sub.add_argument("--file", required=True)
        if name == "review-job":
            sub.add_argument("--key", required=True)
        if name in {"claim", "park", "receipt"}:
            sub.add_argument("--key", required=True)
            sub.add_argument("--owner", required=True)
        if name == "park":
            sub.add_argument("--reason", required=True)
            sub.add_argument("--unsent", action="store_true",
                             help="Attest clean, definitely-unsent cessation; never use for ambiguous Submit.")
        if name == "receipt":
            sub.add_argument("--evidence", required=True, help="Operator-verified, nonempty employer evidence.")
            sub.add_argument("--resume", required=True, help="Exact nonempty submitted resume to hash.")
            sub.add_argument("--confirmation-count", type=int, required=True)
            sub.add_argument("--identity-verified", action="store_true",
                             help="Attest exact employer/job/candidate and matching inbox provenance checked.")
    return p


def main(argv=None):
    try:
        args = parser().parse_args(argv)
        vault = vault_path(args.vault)
        if args.command == "init":
            result = initialize(vault)
        elif args.command in {"import-jobs", "review-job", "claim", "park", "receipt"}:
            with mutation_lock(vault):
                state = load_state(vault)
                if args.command == "import-jobs":
                    result = import_jobs(vault, state, args.file)
                elif args.command == "review-job":
                    result = review_job(vault, state, args.key, args.file)
                elif args.command == "claim":
                    result = claim(vault, state, args.key, args.owner)
                elif args.command == "park":
                    result = park(vault, state, args.key, args.owner, args.reason, unsent=args.unsent)
                else:
                    result = receipt(vault, state, args)
        else:
            state = load_state(vault)
            if args.command == "doctor":
                _, missing = profile(vault)
                result = {"ready": not missing, "missing_fields": missing,
                          "optional_cli": {name: bool(shutil.which(name)) for name in ["python", "codex", "claude", "git"]}}
                if missing:
                    print(json.dumps(result))
                    raise Problem("Onboarding is incomplete")
            elif args.command == "screen":
                result = {"jobs": screen_jobs(vault, state)}
            else:
                result = {"applications": sum(r["status"] == "applied" for r in state["jobs"].values()),
                          "receipts": sum(r["status"] == "applied" for r in state["jobs"].values()),
                          "active_claims": int(state["active"] is not None),
                          "parked": sum(r["status"] == "parked" for r in state["jobs"].values())}
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except Problem as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print(json.dumps({"error": "Local data or filesystem operation failed; preserve holds and review manually"}),
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
