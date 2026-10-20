#!/usr/bin/env python3
"""Export reviewed framework files only. Never copy a parent vault or Git history."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import zipfile

FILES = (
    ".gitignore", ".gitattributes", "README.md", "START-HERE.md", "CODEX.md",
    "CLAUDE.md", "AGENTS.md", "HANDOFF.md", "CONTRIBUTING.md", "LICENSE",
    "jobhunt.py", "source_jobs.py", "export_starter.py", "jobhunt_ops.py",
    "watch_sources.py", "verify_release.py",
    "docs/SCHEMA.md", "docs/ONBOARDING.md", "docs/INTEGRATIONS.md",
    "docs/PLAYBOOK.md", "docs/RESEARCH.md", "docs/DOCUMENTS.md", "docs/ALERTS.md",
    "docs/OPERATIONS.md", "docs/MIGRATION.md", "docs/TESTING.md",
    "prompts/CONTINUE.md", "prompts/SET-UP-ALERTS.md",
    "templates/n8n-greenhouse-source.json",
    "templates/sources.example.json", "templates/OWNER-POLICY.md", "templates/EVIDENCE.md",
    "templates/RESEARCH-BRIEF.md", "templates/PACKET-MANIFEST.md", "templates/HANDOFF.md",
    "templates/NETWORKING.md", ".github/workflows/tests.yml",
    "tests/test_core.py", "tests/test_export.py", "tests/test_source.py",
    "tests/test_operations.py",
)
PREFIX = "job-hunt-starter/"
# These checks supplement an exact file allowlist and a human review. They do not
# certify arbitrary text is free of all secrets or personal information.
SENSITIVE = (
    re.compile(r"^-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----$", re.M),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{30,}\b"),
    re.compile(r"https?://[^\s/]+\.(?:app\.)?n8n\.cloud\b", re.I),
    re.compile(r"https?://[^\s/@:]+:[^\s/@]+@", re.I),
)


class ExportError(ValueError):
    pass


def _linked(path):
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _source(root, relative):
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ExportError("Unsafe allowlist entry")
    path = root
    try:
        checked = [(root, root.lstat())]
        for part in rel.parts:
            path = path / part
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400):
                raise ExportError("Linked/reparse source refused: " + relative)
            checked.append((path, info))
        if not path.resolve(strict=True).is_relative_to(root) or not stat.S_ISREG(info.st_mode):
            raise ExportError("Source escapes framework or is not a file: " + relative)
        if info.st_nlink != 1:
            raise ExportError("Multi-linked source refused: " + relative)
        if info.st_size > 1024 * 1024:
            raise ExportError("Unexpectedly large source: " + relative)
        # Bind validation and reads to one file handle. The caller must still
        # use a trusted, quiescent tree: these checks are not an OS sandbox.
        with path.open("rb") as source:
            opened = os.fstat(source.fileno())
            if not os.path.samestat(info, opened) or opened.st_nlink != 1:
                raise ExportError("Source replaced before open: " + relative)
            for component, expected in checked:
                current = component.lstat()
                if not os.path.samestat(expected, current) or _linked(component):
                    raise ExportError("Source path replaced during open: " + relative)
            data = source.read(1024 * 1024 + 1)
            after = os.fstat(source.fileno())
            # Compare handle metadata with handle metadata. On Windows, path
            # stat and fstat may expose different ctime semantics for one file.
            before_state = (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns, opened.st_nlink)
            after_state = (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink)
            if len(data) > 1024 * 1024 or before_state != after_state:
                raise ExportError("Source changed during read: " + relative)
            current = path.lstat()
            if (not os.path.samestat(info, current) or _linked(path)
                    or (info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)
                    != (current.st_size, current.st_mtime_ns, current.st_ctime_ns, current.st_nlink)):
                raise ExportError("Source path changed during read: " + relative)
        text = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except (OSError, UnicodeError) as exc:
        raise ExportError("Missing/unreadable UTF-8 framework file: " + relative) from exc
    if any(pattern.search(text) for pattern in SENSITIVE):
        raise ExportError("Potential private material: " + relative)
    return data


def export(root, output):
    root, output = Path(root), Path(output)
    try:
        if _linked(root):
            raise ExportError("Linked framework root refused")
        root = root.resolve(strict=True)
        if output.exists() or output.is_symlink():
            raise ExportError("Destination already exists; choose a new file")
        if not output.parent.is_dir():
            raise ExportError("Destination parent must already exist")
        payloads = {name: _source(root, name) for name in FILES}
        manifest = {
            "format": 1,
            "purpose": "Reviewed framework only; no candidate vault or Git history",
            "sha256": {n: hashlib.sha256(d).hexdigest() for n, d in payloads.items()},
        }
        payloads["BUNDLE-MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
        memory = io.BytesIO()
        with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for name in sorted(payloads):
                info = zipfile.ZipInfo(PREFIX + name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, payloads[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        archive = memory.getvalue()
        # Exclusive creation protects an existing artifact, including a concurrent writer.
        with output.open("xb") as f:
            f.write(archive)
        readback = output.read_bytes()
        if readback != archive:
            raise ExportError("Written archive bytes changed during readback")
        with zipfile.ZipFile(io.BytesIO(readback)) as z:
            names = z.namelist()
            if z.testzip() is not None or len(names) != len(payloads) or set(names) != {PREFIX + n for n in payloads}:
                raise ExportError("Written archive failed readback")
            for name, data in payloads.items():
                if z.read(PREFIX + name) != data:
                    raise ExportError("Written archive payload or manifest mismatch")
        return {"file_count": len(payloads), "sha256": hashlib.sha256(readback).hexdigest(), "verified": True}
    except OSError as exc:
        raise ExportError("Export filesystem operation failed; no overwrite attempted") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New ZIP path; parent directory must exist")
    args = parser.parse_args()
    try:
        print(json.dumps(export(Path(__file__).resolve().parent, args.output), sort_keys=True))
    except ExportError as exc:
        print("EXPORT BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
