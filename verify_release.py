#!/usr/bin/env python3
"""Verify a clean allowlisted export and run its synthetic suite after extraction."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

import export_starter as exporter


def verify(output):
    root = Path(__file__).resolve().parent
    for name in exporter.FILES:
        if name.endswith('.json'):
            json.loads((root / name).read_text(encoding='utf-8'))
        if name.endswith('.md'):
            for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)', (root / name).read_text(encoding='utf-8')):
                if '://' not in link and not link.startswith('#'):
                    target = (root / name).parent / link.split('#', 1)[0]
                    if not target.is_file():
                        raise ValueError('Broken local document link in ' + name)
    result = exporter.export(root, output)
    with tempfile.TemporaryDirectory(prefix='synthetic-clean-release-', dir=output.parent) as temp:
        base = Path(temp)
        with zipfile.ZipFile(output) as archive:
            manifest = json.loads(archive.read(exporter.PREFIX + 'BUNDLE-MANIFEST.json'))
            for name, expected in manifest['sha256'].items():
                if hashlib.sha256(archive.read(exporter.PREFIX + name)).hexdigest() != expected:
                    raise ValueError('Bundle manifest mismatch')
            archive.extractall(base)
        env = dict(os.environ, TEMP=str(base), TMP=str(base), TMPDIR=str(base), PYTHONDONTWRITEBYTECODE='1')
        run = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                             cwd=base / 'job-hunt-starter', env=env, capture_output=True, text=True, timeout=900)
        match = re.search(r'Ran ([1-9][0-9]*) tests?', run.stderr)
        if run.returncode or not match:
            sys.stderr.write(run.stderr[-16000:])
            raise ValueError('Clean exported suite failed or ran zero tests')
        result['clean_export_tests'] = int(match.group(1))
        result['test_summary'] = run.stderr.strip().splitlines()[-1]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New ZIP path with an existing parent directory')
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.output.expanduser().absolute()), sort_keys=True))
        return 0
    except (OSError, ValueError, exporter.ExportError, subprocess.SubprocessError):
        print('Release verification failed; inspect diagnostics and preserve source files.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
