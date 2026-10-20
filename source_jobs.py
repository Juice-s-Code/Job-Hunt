#!/usr/bin/env python3
"""Read one public Greenhouse board into an unqualified review queue. Never submit."""
import argparse
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib import error, parse, request
import jobhunt as core

HOST = "boards-api.greenhouse.io"
MAX_BYTES = 16 * 1024 * 1024


class SourceError(ValueError):
    pass


class PublicRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = parse.urlsplit(newurl)
        if target.scheme != "https" or target.hostname != HOST or target.username or target.password or target.port not in (None, 443):
            raise SourceError("Unexpected public-API redirect; no alternate host contacted")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, text):
        self.parts.append(text)

    def handle_starttag(self, tag, attrs):
        if tag in {'p', 'br', 'li', 'div', 'h1', 'h2', 'h3'}:
            self.parts.append('\n')


def fetch_json(url):
    try:
        req = request.Request(url, headers={"Accept": "application/json", "User-Agent": "JobHuntStarter/1 public-board-reader"}, method="GET")
        with request.build_opener(PublicRedirect()).open(req, timeout=30) as response:
            data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise SourceError("Public response exceeds bounded size; no partial success")
        return json.loads(data.decode("utf-8"), object_pairs_hook=core.no_duplicates,
                          parse_constant=core.invalid_constant)
    except (OSError, ValueError, core.Problem, RecursionError, error.URLError) as exc:
        if isinstance(exc, SourceError):
            raise
        raise SourceError("Public fetch/JSON decoding failed; board status remains unknown") from exc


def normalize(data, employer):
    if not isinstance(employer, str) or not employer.strip() or employer != employer.strip() or len(employer) > 160 or any(ord(c) < 32 for c in employer):
        raise SourceError("Provide a literal nonempty employer name without control characters")
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise SourceError("Unexpected upstream schema, not an empty job board")
    if 'meta' in data:
        meta = data['meta']
        if (type(meta) is not dict or type(meta.get('total')) is not int
                or meta['total'] != len(data['jobs'])):
            raise SourceError('Incomplete upstream inventory; no partial success')
    result, seen = [], set()
    for job in data["jobs"]:
        if not isinstance(job, dict):
            raise SourceError("Malformed upstream job object")
        value = job.get("id")
        if type(value) is int and value > 0:
            job_id = str(value)
        elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value, flags=re.ASCII):
            job_id = value
        else:
            raise SourceError("Malformed exact upstream ID; not repaired")
        if job_id in seen:
            raise SourceError("Duplicate upstream exact ID; inspect source before import")
        seen.add(job_id)
        title, url = job.get("title"), job.get("absolute_url")
        if not isinstance(title, str) or not title.strip() or not isinstance(url, str):
            raise SourceError("Missing title or canonical URL")
        try:
            parsed = parse.urlsplit(url)
            valid = parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password and parsed.port in (None, 443)
        except ValueError as exc:
            raise SourceError("Malformed canonical URL") from exc
        if not valid:
            raise SourceError("Unacceptable canonical URL")
        content = job.get("content")
        if content is None:
            content = ""
        if not isinstance(content, str):
            raise SourceError("Malformed source body")
        text = _Text()
        text.feed(unescape(content))
        text.close()
        location = job.get("location") or {}
        record = {
            "employer": employer, "ats": "greenhouse", "id": job_id,
            "title": title, "url": url,
            "location": location.get("name") if isinstance(location, dict) else None,
            "country": None, "role_family": None, "employment_type": None,
            "internship": None, "min_years_experience": None, "start_date": None,
            "source_text": "\n".join(text.parts),
            "salary_min": None, "salary_currency": None, "salary_period": None,
            "no_ai": None,
        }
        try:
            core.validate_job(record)
        except core.Problem as exc:
            raise SourceError('Source fields violate the normalized job contract') from exc
        result.append(record)
    return result


def collect(board, employer):
    if not isinstance(board, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", board, flags=re.ASCII):
        raise SourceError("Invalid public board slug; resolve it from employer careers links")
    url = "https://" + HOST + "/v1/boards/" + board + "/jobs?content=true"
    return normalize(fetch_json(url), employer)


def save_jobs(output, jobs):
    path = Path(output)
    root = Path(__file__).resolve().parent
    if path.resolve().is_relative_to(root):
        raise SourceError("Save personal research outside the framework checkout")
    if not path.parent.is_dir() or path.exists() or path.is_symlink():
        raise SourceError("Output must be a new file in an existing directory")
    try:
        with path.open("x", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
            f.write("\n")
        if json.loads(path.read_text(encoding="utf-8")) != jobs:
            raise SourceError("Output readback failed")
    except OSError as exc:
        raise SourceError("Output write failed; no existing file was overwritten") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", required=True, help="Verified public Greenhouse board slug, not a credential")
    parser.add_argument("--employer", required=True, help="Use the same exact namespace on every import")
    parser.add_argument("--output", required=True, help="New JSON file outside framework")
    args = parser.parse_args()
    try:
        # Refuse existing or in-framework destinations before making a network request.
        destination = Path(args.output)
        if destination.exists() or destination.is_symlink() or not destination.parent.is_dir() or destination.resolve().is_relative_to(Path(__file__).resolve().parent):
            raise SourceError("Choose a new output outside framework in an existing directory")
        jobs = collect(args.board, args.employer)
        save_jobs(destination, jobs)
        print(json.dumps({"retrieved": len(jobs), "distinct_exact_ids": len({j["id"] for j in jobs}), "eligibility": "unverified-review-only", "verified_readback": True}))
    except SourceError as exc:
        print("SOURCE BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
