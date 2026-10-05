import copy
import unittest
import dispatch
import route


def fixture():
    task = {'id': 'parser-fix', 'goal': 'Reject empty names', 'work': 'Fix parser and regression test',
            'evidence': ['Empty input is currently accepted'], 'acceptance': ['Empty input raises ValueError'],
            'host': {'snapshot': 'revision-1', 'delegation_authorized': True, 'share_authorized': True,
                     'dependency_ready': True, 'write_conflict': False, 'trivial': False,
                     'attempt_count': 0, 'available': ['luna', 'sol', 'astra'], 'minimum_role': 'sol',
                     'retain_for_host': False,
                     'routing_brief': {'goal': 'Reject empty names', 'work': 'Fix parser',
                                       'facts': ['Empty names are accepted'], 'acceptance': ['Regression passes']},
                     'dispatch': {'phase': 'implement', 'owned_paths': ['src/parser.py', 'tests/test_parser.py'],
                                  'deliverable': 'Parser fix and regression test',
                                  'checks': [{'id': 'regression', 'acceptance_index': 0, 'method': 'Run parser regression tests'}]}}}
    task['host']['reviewed_sha256'] = route.review_digest(task)
    rec = {'id': task['id'], 'route': 'sol', 'reason': 'selected', 'raw_choice': 'sol',
           'snapshot': 'revision-1', 'input_sha256': route.fingerprint(task)}
    runtime = {'workspace_root': '/tmp/router-test-project', 'coordinator_model': 'gpt-6-astra', 'bindings': {'sol': {'model': 'gpt-6.1-sol', 'effort': 'medium'}},
               'catalog': {'gpt-6.1-sol': ['low', 'medium', 'high']}, 'native_delegation': True,
               'free_slots': 1, 'benefit_justified': True}
    return task, rec, runtime


def reattest(task, rec):
    task['host']['reviewed_sha256'] = route.review_digest(task)
    rec['input_sha256'] = route.fingerprint(task)


def receipt(plan):
    return {'workspace_root': plan['workspace_root'], 'host_verified': True, 'plan_sha256': plan['plan_sha256'], 'start_snapshot': 'revision-1',
            'end_snapshot': 'revision-2', 'agent_id': 'observed-agent-01',
            'actual_model': 'gpt-6.1-sol', 'actual_effort': 'medium',
            'changed_paths': ['src/parser.py', 'tests/test_parser.py'],
            'checks': [{'id': 'regression', 'passed': True, 'exit_code': 0, 'evidence': 'pytest: 4 passed'}],
            'unresolved_risks': []}


class DispatchTests(unittest.TestCase):
    def test_valid_worker_is_explicit_and_context_minimal(self):
        p = dispatch.plan(*fixture())
        self.assertEqual(p['mode'], 'worker')
        self.assertEqual(p['spawn']['model'], 'gpt-6.1-sol')
        self.assertEqual(p['spawn']['fork_turns'], 'none')
        self.assertNotIn('reviewed_sha256', p['spawn']['message'])

    def test_stale_policy_and_evidence_prevent_dispatch(self):
        for field, value in [('snapshot', 'changed'), ('delegation_authorized', False),
                             ('minimum_role', 'astra'), ('write_conflict', True)]:
            with self.subTest(field=field):
                t, r, runtime = fixture()
                t['host'][field] = value
                self.assertEqual(dispatch.plan(t, r, runtime)['mode'], 'host')

    def test_runtime_constraints_keep_work_with_host(self):
        for field, value in [('catalog', {}), ('bindings', {}), ('free_slots', 0),
                             ('native_delegation', False), ('benefit_justified', False),
                             ('coordinator_model', 'gpt-6.1-sol')]:
            with self.subTest(field=field):
                t, r, runtime = fixture()
                runtime[field] = value
                self.assertEqual(dispatch.plan(t, r, runtime)['mode'], 'host')

    def test_independent_review_can_use_same_model(self):
        t, r, runtime = fixture()
        t['host']['dispatch'].update(phase='review', owned_paths=[], independent_review=True)
        reattest(t, r)
        runtime['coordinator_model'] = 'gpt-6.1-sol'
        self.assertEqual(dispatch.plan(t, r, runtime)['mode'], 'worker')

    def test_invalid_contracts_cannot_dispatch(self):
        for update in [{'owned_paths': ['../secret']}, {'owned_paths': ['/tmp/file']},
                       {'owned_paths': ['src/*.py']}, {'owned_paths': ['.git/config']},
                       {'owned_paths': ['src//file']}, {'checks': []},
                       {'phase': 'review'}, {'checks': [{'id': [], 'criterion': 'x'}]}]:
            with self.subTest(update=update):
                t, r, runtime = fixture()
                t['host']['dispatch'].update(update)
                reattest(t, r)
                self.assertEqual(dispatch.plan(t, r, runtime)['mode'], 'host')

    def test_every_acceptance_criterion_needs_a_check(self):
        t, r, runtime = fixture()
        t['acceptance'].append('Public API unchanged')
        reattest(t, r)
        self.assertEqual(dispatch.plan(t, r, runtime)['reason'], 'uncovered_acceptance_criteria')

    def test_nonboolean_review_flag_is_rejected(self):
        t, r, runtime = fixture()
        t['host']['dispatch']['independent_review'] = 'false'
        reattest(t, r)
        self.assertEqual(dispatch.plan(t, r, runtime)['mode'], 'host')

    def test_host_verified_complete_receipt_passes(self):
        p = dispatch.plan(*fixture())
        self.assertEqual(dispatch.assess(p, receipt(p))['status'], 'accepted')

    def test_missing_or_mismatched_observations_do_not_pass(self):
        p = dispatch.plan(*fixture())
        for update in [{'host_verified': False}, {'agent_id': ''}, {'start_snapshot': 'other'},
                       {'actual_model': 'gpt-6-luna'}, {'actual_effort': 'high'},
                       {'changed_paths': ['src/other.py']}, {'checks': []},
                       {'unresolved_risks': ['Untested path']}, {'plan_sha256': 'wrong'}]:
            with self.subTest(update=update):
                r = receipt(p)
                r.update(update)
                self.assertEqual(dispatch.assess(p, r)['status'], 'review')

    def test_claimed_success_with_failed_exit_is_rejected(self):
        p = dispatch.plan(*fixture())
        r = receipt(p)
        r['checks'][0]['exit_code'] = 1
        self.assertEqual(dispatch.assess(p, r)['reason'], 'contradictory_check_evidence')

    def test_duplicate_checks_do_not_establish_coverage(self):
        p = dispatch.plan(*fixture())
        r = receipt(p)
        r['checks'] *= 2
        self.assertEqual(dispatch.assess(p, r)['status'], 'review')

    def test_changed_plan_is_rejected(self):
        p = dispatch.plan(*fixture())
        r = receipt(p)
        p['owned_paths'].append('secret')
        self.assertEqual(dispatch.assess(p, r)['reason'], 'changed_plan')

    def test_only_capability_failure_suggests_escalation(self):
        p = dispatch.plan(*fixture())
        r = receipt(p)
        r['checks'][0].update(passed=False, exit_code=1)
        for failure in ('infrastructure', 'missing_requirements', None):
            r['failure_type'] = failure
            self.assertEqual(dispatch.assess(p, r)['status'], 'review')
        r['failure_type'] = 'capability'
        self.assertEqual(dispatch.assess(p, r)['suggested_minimum_role'], 'astra')

    def test_second_failure_stops(self):
        t, r, runtime = fixture()
        t['host']['attempt_count'] = 1
        reattest(t, r)
        p = dispatch.plan(t, r, runtime)
        r = receipt(p)
        r['checks'][0].update(passed=False, exit_code=1)
        r['failure_type'] = 'capability'
        self.assertEqual(dispatch.assess(p, r)['status'], 'review')


if __name__ == '__main__':
    unittest.main()
