#!/usr/bin/env python3
"""Private reports and durable local alert events. Does not send messages."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import uuid

import jobhunt as core


def load_ops(vault):
    path = vault / '.jobhunt/operations.json'
    core.safe_path(path)
    if not path.exists():
        return {'version': 1, 'pending': {}, 'acknowledged': [], 'sources': {}}
    data = core.read_json(path)
    core.fields(data, {'version', 'pending', 'acknowledged', 'sources'}, 'Operations')
    core.require(type(data['version']) is int and data['version'] == 1, 'Unsupported operations version')
    core.require(type(data['pending']) is dict and type(data['sources']) is dict,
                 'Invalid operations maps')
    core.require(type(data['acknowledged']) is list and
                 all(type(x) is str for x in data['acknowledged']), 'Invalid acknowledgments')
    core.require(len(set(data['acknowledged'])) == len(data['acknowledged']), 'Duplicate acknowledgments')
    for key, event in data['pending'].items():
        core.require(type(event) is dict and set(event) == {'kind', 'details'}, 'Invalid pending event')
        core.require(key == core.hash_bytes(core.json_bytes(event)), 'Pending event digest mismatch')
        core.require(key not in data['acknowledged'], 'Pending/acknowledgment mismatch')
    return data


def save_ops(vault, data):
    content = core.json_bytes(data)
    core.require(len(content) <= core.MAX_JSON_BYTES, 'Operations state too large; manual archival required')
    core.atomic_write(vault / '.jobhunt/operations.json', content)


def enqueue(data, kind, details):
    event = {'kind': kind, 'details': details}
    key = core.hash_bytes(core.json_bytes(event))
    if key not in data['acknowledged']:
        data['pending'][key] = event
    return key


def private_report(vault, label, body):
    folder = vault / 'Research/Reports'
    core.safe_path(folder)
    folder.mkdir(exist_ok=True)
    path = folder / (core.now().replace(':', '-').replace('+', '_') + '-' + label + '-' + uuid.uuid4().hex[:8] + '.md')
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(body)
    return str(path.relative_to(vault))


def summary(vault):
    state = core.load_state(vault)  # Verifies receipt bytes, ledger and active claim.
    _, missing = core.profile(vault)
    rows = core.screen_jobs(vault, state) if not missing else []
    return state, {'recorded_utc': core.now(), 'ready': not missing,
                   'missing_fields': missing, 'inventory': len(state['jobs']),
                   'counts': dict(Counter(row['status'] for row in rows)),
                   'applications': sum(r['status'] == 'applied' for r in state['jobs'].values()),
                   'active_key': state['active'], 'jobs': rows}


def collect_alerts(vault, operations):
    state, report = summary(vault)
    if report['missing_fields']:
        enqueue(operations, 'onboarding_required', {'missing_fields': report['missing_fields']})
    rows = report['jobs']
    if report['missing_fields']:
        # Changing an owner profile must not hide an existing form/receipt hold.
        rows = [{'key': key, 'status': record['status']} for key, record in state['jobs'].items()
                if record['status'] in {'claimed', 'parked', 'applied'}]
    for row in rows:
        if row['status'] not in {'eligible', 'claimed', 'parked', 'applied'}:
            continue
        record = state['jobs'][row['key']]
        job = record['job']
        details = {'key': row['key'], 'employer': job['employer'], 'title': job['title'],
                   'ats': job['ats'], 'id': job['id'], 'url': job['url']}
        if row['status'] == 'parked':
            details['reason'] = record['reason']
        if row['status'] == 'applied':
            details['receipt_sha256'] = record['receipt_sha256']
        kind = {'eligible': 'eligible_for_review', 'claimed': 'active_form_hold',
                'parked': 'owner_action_required', 'applied': 'receipt_recorded'}[row['status']]
        enqueue(operations, kind, details)
    return report


def main(argv=None):
    parser = core.Parser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('report', 'alerts', 'ack'):
        sub = commands.add_parser(name)
        sub.add_argument('--vault', required=True)
        if name == 'ack':
            sub.add_argument('--id', required=True, action='append', help='Delivered event ID; repeat for several.')
            sub.add_argument('--delivered', action='store_true', help='Attest actual approved-channel delivery.')
    try:
        args = parser.parse_args(argv)
        vault = core.vault_path(args.vault)
        with core.mutation_lock(vault):
            if args.command == 'report':
                _, result = summary(vault)
                body = '# Private job-hunt report\n\nGenerated from verified local records.\n\n```json\n'
                body += json.dumps(result, indent=2, ensure_ascii=False) + '\n```\n'
                result['report'] = private_report(vault, 'pipeline', body)
                # Per-job details remain in the private report; stdout is a summary.
                result.pop('jobs')
            else:
                core.load_state(vault)
                data = load_ops(vault)
                if args.command == 'alerts':
                    collect_alerts(vault, data)
                    save_ops(vault, data)
                    result = {'pending': data['pending'], 'count': len(data['pending']),
                              'delivery': 'local-only; no message sent'}
                else:
                    core.require(args.delivered, 'Acknowledge only after verified delivery using --delivered')
                    core.require(len(set(args.id)) == len(args.id), 'Duplicate event IDs')
                    core.require(all(key in data['pending'] for key in args.id), 'Unknown pending event ID')
                    for key in args.id:
                        del data['pending'][key]
                        data['acknowledged'].append(key)
                    save_ops(vault, data)
                    result = {'acknowledged': len(args.id), 'pending': len(data['pending'])}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (core.Problem, OSError, ValueError, RecursionError):
        print(json.dumps({'error': 'Operations blocked; inspect private state and command arguments. No message sent.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
