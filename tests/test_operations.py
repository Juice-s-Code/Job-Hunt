"""Synthetic local events, source failures, receipts and immutable application state."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jobhunt as core
import jobhunt_ops as ops
import source_jobs as source
import watch_sources as watch
from test_core import example


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='synthetic-operations-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        core.initialize(self.vault)
        profile = core.read_json(self.vault / 'Profile/candidate.json')
        profile['candidate'].update(display_name='SYNTHETIC PRIVATE PERSON', email='synthetic@example.invalid',
                                    earliest_start='2030-06-01')
        profile['mandate'].update(role_families=['finance'], countries=['US'], salary_floor=70000)
        core.atomic_write(self.vault / 'Profile/candidate.json', core.json_bytes(profile))
        self.config = self.vault / 'Research/sources.json'
        self.set_boards([{'board': 'synthetic', 'employer': 'Synthetic Example Employer'}])

    def set_boards(self, boards):
        core.atomic_write(self.config, core.json_bytes({'version': 1, 'boards': boards}))

    def scan(self, jobs):
        with patch.object(source, 'collect', return_value=jobs):
            with core.mutation_lock(self.vault):
                return watch.scan(self.vault, self.config)

    def fail_scan(self):
        with patch.object(source, 'collect', side_effect=source.SourceError('synthetic failure')):
            with core.mutation_lock(self.vault):
                return watch.scan(self.vault, self.config)

    def run_ops(self, *args):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = ops.main([*args, '--vault', str(self.vault)])
        return code, output.getvalue(), errors.getvalue()

    def test_report_reconciles_without_exposing_profile(self):
        code, out, err = self.run_ops('report')
        self.assertEqual((code, err), (0, ''))
        self.assertNotIn('SYNTHETIC PRIVATE PERSON', out)
        self.assertNotIn('synthetic@example.invalid', out)
        result = json.loads(out)
        self.assertEqual(result['applications'], 0)
        self.assertTrue((self.vault / result['report']).is_file())
        self.assertTrue((self.vault / 'CODEX.md').is_file())

    def test_receipt_tamper_blocks_report(self):
        (self.vault / 'Applications/Application Ledger.md').write_text('TAMPERED', encoding='utf-8')
        self.assertEqual(self.run_ops('report')[0], 1)

    def test_profile_gap_never_hides_existing_form_hold(self):
        batch = self.root / 'jobs.json'
        batch.write_bytes(core.json_bytes([example()]))
        state = core.load_state(self.vault)
        key = core.import_jobs(self.vault, state, batch)['keys'][0]
        core.claim(self.vault, state, key, 'synthetic-operator')
        path = self.vault / 'Profile/candidate.json'
        profile = core.read_json(path)
        profile['candidate']['email'] = ''
        core.atomic_write(path, core.json_bytes(profile))
        pending = json.loads(self.run_ops('alerts')[1])['pending']
        self.assertEqual({event['kind'] for event in pending.values()},
                         {'onboarding_required', 'active_form_hold'})

    def test_eligible_alert_is_durable_and_ack_requires_delivery(self):
        batch = self.root / 'jobs.json'
        batch.write_bytes(core.json_bytes([example()]))
        state = core.load_state(self.vault)
        core.import_jobs(self.vault, state, batch)
        first = json.loads(self.run_ops('alerts')[1])
        second = json.loads(self.run_ops('alerts')[1])
        self.assertEqual(first, second)
        self.assertEqual(first['count'], 1)
        event_id = next(iter(first['pending']))
        self.assertEqual(self.run_ops('ack', '--id', event_id)[0], 1)
        self.assertEqual(self.run_ops('ack', '--id', 'unknown', '--delivered')[0], 1)
        self.assertEqual(self.run_ops('ack', '--id', event_id, '--delivered')[0], 0)
        self.assertEqual(json.loads(self.run_ops('alerts')[1])['count'], 0)

    def test_lock_prevents_operations_and_monitor(self):
        with core.mutation_lock(self.vault):
            self.assertEqual(self.run_ops('alerts')[0], 1)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(watch.main(['--vault', str(self.vault), '--config', str(self.config)]), 1)

    def test_unchanged_sources_queue_once_and_leave_core_untouched(self):
        before = (self.vault / '.jobhunt/state.json').read_bytes()
        first = self.scan([example()])
        self.assertTrue(first['results'][0]['initial_snapshot'])
        data = ops.load_ops(self.vault)
        self.assertEqual(len(data['pending']), 1)
        second = self.scan([example()])
        self.assertEqual(second['results'][0]['new'], [])
        self.assertEqual(ops.load_ops(self.vault), data)
        self.assertEqual((self.vault / '.jobhunt/state.json').read_bytes(), before)

    def test_changed_and_not_observed_are_distinct(self):
        self.scan([example()])
        changed = self.scan([example(source_text='SYNTHETIC changed requirements')])
        self.assertEqual(changed['results'][0]['changed'], ['EXAMPLE-01-A'])
        absent = self.scan([])
        self.assertEqual(absent['results'][0]['not_observed'], ['EXAMPLE-01-A'])
        kinds = {x['kind'] for x in ops.load_ops(self.vault)['pending'].values()}
        self.assertEqual(kinds, {'source_new', 'source_changed', 'source_not_observed'})

    def test_source_failure_retains_inventory_and_no_false_closure(self):
        self.scan([example()])
        old = ops.load_ops(self.vault)['sources']['synthetic']['jobs']
        failure = self.fail_scan()
        self.assertEqual(failure['status'], 'failed')
        self.assertIsNone(failure['results'][0]['observed'])
        self.assertEqual(failure['results'][0]['not_observed'], [])
        self.assertEqual(ops.load_ops(self.vault)['sources']['synthetic']['jobs'], old)
        data = ops.load_ops(self.vault)
        self.fail_scan()
        self.assertEqual(ops.load_ops(self.vault), data)

    def test_recovery_and_second_outage_are_new_alerts(self):
        self.fail_scan()
        first = ops.load_ops(self.vault)
        key = next(iter(first['pending']))
        self.run_ops('ack', '--id', key, '--delivered')
        recovery = self.scan([example()])
        self.assertTrue(recovery['results'][0]['initial_snapshot'])
        self.fail_scan()
        pending = ops.load_ops(self.vault)['pending']
        failures = [x for x in pending.values() if x['kind'] == 'source_failed']
        self.assertEqual(len(failures), 1)
        self.assertNotIn(key, pending)
        self.assertTrue(any(x['kind'] == 'source_recovered' for x in pending.values()))

    def test_partial_failure_is_degraded(self):
        self.set_boards([{'board': 'a', 'employer': 'A'}, {'board': 'b', 'employer': 'B'}])
        with patch.object(source, 'collect', side_effect=[[], source.SourceError('synthetic')]):
            result = watch.scan(self.vault, self.config)
        self.assertEqual(result['status'], 'degraded')
        self.assertEqual((result['boards_attempted'], result['boards_failed']), (2, 1))

    def test_invalid_config_rejected_before_network(self):
        for boards in ([], [{'board': 'REPLACE_ME', 'employer': 'X'}],
                       [{'board': '../escape', 'employer': 'X'}],
                       [{'board': 'a', 'employer': 'X'}] * 2):
            self.set_boards(boards)
            with patch.object(source, 'collect') as fetch:
                with self.assertRaises(core.Problem):
                    watch.scan(self.vault, self.config)
                fetch.assert_not_called()

    def test_bad_source_and_namespace_change_never_publish_false_empty(self):
        self.scan([example()])
        self.assertEqual(self.scan([{'bad': 'schema'}])['status'], 'failed')
        self.assertEqual(len(ops.load_ops(self.vault)['sources']['synthetic']['jobs']), 1)
        self.set_boards([{'board': 'synthetic', 'employer': 'Changed Name'}])
        with patch.object(source, 'collect') as fetch:
            with self.assertRaises(core.Problem):
                watch.scan(self.vault, self.config)
            fetch.assert_not_called()

    def test_checkpoint_failure_does_not_advance_baseline(self):
        self.scan([example()])
        before = ops.load_ops(self.vault)
        with patch.object(ops, 'save_ops', side_effect=OSError('synthetic disk failure')):
            with self.assertRaises(OSError):
                self.scan([])
        self.assertEqual(ops.load_ops(self.vault), before)

    def test_operations_digest_tampering_fails_loudly(self):
        self.scan([example()])
        path = self.vault / '.jobhunt/operations.json'
        data = core.read_json(path)
        next(iter(data['pending'].values()))['details']['title'] = 'TAMPERED'
        core.atomic_write(path, core.json_bytes(data))
        with self.assertRaises(core.Problem):
            ops.load_ops(self.vault)


if __name__ == '__main__':
    unittest.main()
