#!/usr/bin/env python3
"""One bounded public Greenhouse scan; private snapshots and pending local alerts."""
import json
from pathlib import Path
import re
import sys

import jobhunt as core
import jobhunt_ops as ops
import source_jobs as source

MAX_BOARDS = 10
MAX_JOBS = 10000


def configuration(vault, path):
    path = Path(path).expanduser().absolute()
    core.require(path.is_relative_to(vault), 'Source configuration must be private and inside the vault')
    config = core.read_json(path)
    core.fields(config, {'version', 'boards'}, 'Source configuration')
    core.require(type(config['version']) is int and config['version'] == 1, 'Unsupported source config')
    boards = config['boards']
    core.require(type(boards) is list and 1 <= len(boards) <= MAX_BOARDS, 'Configure 1 to 10 verified boards')
    seen = set()
    for item in boards:
        core.fields(item, {'board', 'employer'}, 'Board')
        core.text(item['board'], 'board')
        core.text(item['employer'], 'employer')
        core.require(re.fullmatch(r'[A-Za-z0-9_-]{1,100}', item['board']) is not None
                     and 'REPLACE' not in item['board'].upper(), 'Replace placeholder with verified board slug')
        core.require(item['board'] not in seen, 'Duplicate board')
        seen.add(item['board'])
    return boards


def scan(vault, config_path):
    # The caller holds the same exclusive lock as the core. No applications mutate.
    core.load_state(vault)
    boards = configuration(vault, config_path)
    data = ops.load_ops(vault)
    results = []
    for item in boards:
        board, employer = item['board'], item['employer']
        previous = data['sources'].get(board)
        if previous is not None:
            core.fields(previous, {'employer', 'health', 'jobs', 'generation', 'has_snapshot'}, 'Source checkpoint')
            core.require(previous['employer'] == employer, 'Board namespace changed; manual reconciliation required')
            core.require(previous['health'] in {'ok', 'failed'} and type(previous['jobs']) is dict,
                         'Invalid source checkpoint')
            core.require(type(previous['generation']) is int and previous['generation'] > 0
                         and type(previous['has_snapshot']) is bool, 'Invalid source checkpoint version')
            for key, job in previous['jobs'].items():
                core.validate_job(job)
                core.require(key == job['id'], 'Source checkpoint identity mismatch')
        try:
            jobs = source.collect(board, employer)
            core.require(type(jobs) is list and len(jobs) <= MAX_JOBS, 'Source inventory exceeds budget')
            for job in jobs:
                core.validate_job(job)
            observed = {job['id']: job for job in jobs}
            core.require(len(observed) == len(jobs), 'Duplicate observed IDs')
            old = previous['jobs'] if previous else {}
            new = sorted(set(observed) - set(old))
            changed = sorted(key for key in observed.keys() & old.keys() if observed[key] != old[key])
            absent = sorted(set(old) - set(observed))
            generation = previous['generation'] if previous else 0
            if not previous or previous['health'] != 'ok' or new or changed or absent:
                generation += 1
            result = {'board': board, 'health': 'ok', 'observed': len(jobs),
                      'initial_snapshot': not previous or not previous['has_snapshot'], 'new': new,
                      'changed': changed, 'not_observed': absent}
            for kind, keys in [('source_new', new), ('source_changed', changed), ('source_not_observed', absent)]:
                for key in keys:
                    job = observed.get(key, old.get(key))
                    ops.enqueue(data, kind, {'board': board, 'generation': generation, 'employer': employer, 'id': key,
                                'title': job['title'], 'url': job['url'],
                                'before_sha256': core.hash_bytes(core.json_bytes(old[key])) if key in old else None,
                                'after_sha256': core.hash_bytes(core.json_bytes(observed[key])) if key in observed else None})
            if previous and previous['health'] == 'failed':
                ops.enqueue(data, 'source_recovered', {'board': board, 'generation': generation, 'observed': len(jobs),
                            'snapshot_sha256': core.hash_bytes(core.json_bytes(observed))})
            data['sources'][board] = {'employer': employer, 'health': 'ok', 'jobs': observed,
                                     'generation': generation, 'has_snapshot': True}
        except (source.SourceError, core.Problem, OSError, ValueError, RecursionError):
            result = {'board': board, 'health': 'failed', 'observed': None,
                      'new': [], 'changed': [], 'not_observed': []}
            # Failure is never an empty board. Preserve the last complete payload.
            data['sources'][board] = {'employer': employer, 'health': 'failed',
                                      'jobs': previous['jobs'] if previous else {},
                                      'has_snapshot': previous['has_snapshot'] if previous else False,
                                      'generation': (previous['generation'] + (previous['health'] != 'failed')) if previous else 1}
            ops.enqueue(data, 'source_failed', {'board': board, 'generation': data['sources'][board]['generation'],
                        'status': 'unknown; prior snapshot retained'})
        results.append(result)
    failed = sum(result['health'] == 'failed' for result in results)
    report = {'recorded_utc': core.now(), 'status': 'failed' if failed == len(results) else 'degraded' if failed else 'ok',
              'boards_attempted': len(results), 'boards_failed': failed, 'results': results,
              'eligibility': 'unverified; review sources before import', 'pending_alerts': len(data['pending'])}
    # Store snapshots and events atomically together. A failed publication never
    # advances the baseline independently of its alert events.
    ops.save_ops(vault, data)
    body = '# Public source observations (private report)\n\nNot proof of eligibility or closure.\n\n```json\n'
    report['report'] = ops.private_report(vault, 'sources', body + json.dumps(report, indent=2) + '\n```\n')
    return report


def main(argv=None):
    parser = core.Parser(description=__doc__)
    parser.add_argument('--vault', required=True)
    parser.add_argument('--config', required=True)
    try:
        args = parser.parse_args(argv)
        vault = core.vault_path(args.vault)
        with core.mutation_lock(vault):
            result = scan(vault, args.config)
        print(json.dumps(result, sort_keys=True))
        return 0 if result['status'] == 'ok' else 2
    except (core.Problem, OSError, ValueError, RecursionError):
        print(json.dumps({'error': 'Source monitor blocked; preserve checkpoints and inspect configuration.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
