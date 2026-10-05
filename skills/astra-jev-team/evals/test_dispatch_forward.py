import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import route
import dispatch


def fixture():
    task = {
        'id': 'parser-fix', 'goal': 'Fix empty-token parser crash',
        'work': 'Implement a scoped parser fix in the host checkout',
        'evidence': ['Observed ValueError from parse("")'],
        'acceptance': ['Empty token returns a parse error', 'Existing parser regression suite passes'],
        'host': {
            'snapshot': 'tree-001', 'delegation_authorized': True,
            'share_authorized': True, 'dependency_ready': True,
            'write_conflict': False, 'trivial': False, 'attempt_count': 0,
            'available': ['luna', 'sol', 'astra'], 'minimum_role': 'sol',
            'retain_for_host': False,
            'routing_brief': {'goal': 'Fix parser crash', 'work': 'Scoped parser fix',
                'facts': ['Empty token raises ValueError'],
                'acceptance': ['Empty token returns a parse error', 'Existing parser regression suite passes']},
            'dispatch': {'phase': 'implement', 'owned_paths': ['src/parser.py', 'tests/test_parser.py'],
                'deliverable': 'Parser fix with regression coverage',
                'checks': [{'id': 'parse-empty', 'acceptance_index': 0, 'method': 'run focused parser test'},
                           {'id': 'parser-suite', 'acceptance_index': 1, 'method': 'run parser regression suite'}]}
        }
    }
    task['host']['reviewed_sha256'] = route.review_digest(task)
    return task


def recommendation(task, role='sol'):
    return {'id': task['id'], 'route': role, 'reason': 'selected', 'raw_choice': role,
            'input_sha256': route.fingerprint(task), 'snapshot': task['host']['snapshot']}


def runtime():
    return {'bindings': {'sol': {'model': 'runtime-sol-2026', 'effort': 'high'}},
            'catalog': {'runtime-sol-2026': ['low', 'medium', 'high']},
            'coordinator_model': 'runtime-astra-2026', 'workspace_root': '/workspace/repo',
            'native_delegation': True, 'free_slots': 1, 'benefit_justified': True}


def receipt(plan):
    return {'host_verified': True, 'plan_sha256': plan['plan_sha256'],
            'start_snapshot': plan['snapshot'], 'end_snapshot': 'tree-002',
            'workspace_root': plan['workspace_root'], 'agent_id': 'agent-7',
            'actual_model': plan['spawn']['model'],
            'actual_effort': plan['spawn']['reasoning_effort'],
            'changed_paths': ['src/parser.py', 'tests/test_parser.py'],
            'checks': [{'id': 'parse-empty', 'passed': True, 'evidence': 'focused test output: 1 passed', 'exit_code': 0},
                       {'id': 'parser-suite', 'passed': True, 'evidence': 'parser suite output: 24 passed', 'exit_code': 0}],
            'unresolved_risks': []}


class DispatchEvaluation(unittest.TestCase):
    def test_valid_task_pins_runtime_model_effort_and_host_root(self):
        task = fixture(); plan = dispatch.plan(task, recommendation(task), runtime())
        self.assertEqual(plan['mode'], 'worker')
        self.assertEqual(plan['spawn']['model'], 'runtime-sol-2026')
        self.assertEqual(plan['spawn']['reasoning_effort'], 'high')
        self.assertEqual(plan['workspace_root'], '/workspace/repo')
        self.assertIn('/workspace/repo', plan['spawn']['message'])
        self.assertEqual(dispatch.assess(plan, receipt(plan))['status'], 'accepted')

    def test_stale_recommendation_cannot_build_worker_plan(self):
        task = fixture(); old = recommendation(task)
        task['host']['snapshot'] = 'tree-002'
        task['host']['reviewed_sha256'] = route.review_digest(task)
        self.assertEqual(dispatch.plan(task, old, runtime())['mode'], 'host')

    def test_missing_acceptance_coverage_is_blocked(self):
        task = fixture(); task['host']['dispatch']['checks'].pop()
        task['host']['reviewed_sha256'] = route.review_digest(task)
        plan = dispatch.plan(task, recommendation(task), runtime())
        self.assertEqual(plan['reason'], 'uncovered_acceptance_criteria')

    def test_legacy_freeform_check_schema_is_blocked(self):
        task = fixture(); task['host']['dispatch']['checks'] = [{'id': 'anything', 'criterion': 'say hello'}]
        task['host']['reviewed_sha256'] = route.review_digest(task)
        self.assertEqual(dispatch.plan(task, recommendation(task), runtime())['reason'], 'invalid_dispatch_contract')

    def test_string_false_independent_review_flag_is_blocked(self):
        task = fixture(); task['host']['dispatch']['independent_review'] = 'false'
        task['host']['reviewed_sha256'] = route.review_digest(task)
        rt = runtime(); rt['bindings']['sol'] = {'model': rt['coordinator_model'], 'effort': 'high'}
        rt['catalog'][rt['coordinator_model']] = ['high']
        self.assertEqual(dispatch.plan(task, recommendation(task), rt)['reason'], 'invalid_independent_review_flag')

    def test_runtime_model_effort_must_be_supported(self):
        task = fixture(); rt = runtime(); rt['bindings']['sol']['effort'] = 'ultra'
        self.assertEqual(dispatch.plan(task, recommendation(task), rt)['reason'], 'unsupported_model_or_effort')

    def test_receipt_must_match_root_model_effort_and_owned_paths(self):
        task = fixture(); plan = dispatch.plan(task, recommendation(task), runtime())
        for name, change in [('root', {'workspace_root': '/other'}),
                             ('model', {'actual_model': 'other'}),
                             ('effort', {'actual_effort': 'low'}),
                             ('path', {'changed_paths': ['src/parser.py', 'outside.txt']})]:
            with self.subTest(name=name):
                r = receipt(plan); r.update(change)
                self.assertEqual(dispatch.assess(plan, r)['status'], 'review')

    def test_paths_reject_traversal_and_non_exact_globs(self):
        for invalid in ['../outside.py', 'src//parser.py', 'src/.git/config', 'src/*.py']:
            with self.subTest(path=invalid):
                task = fixture(); task['host']['dispatch']['owned_paths'] = [invalid]
                task['host']['reviewed_sha256'] = route.review_digest(task)
                self.assertEqual(dispatch.plan(task, recommendation(task), runtime())['reason'], 'invalid_dispatch_contract')

    def test_only_bounded_capability_failure_gets_one_retry_recommendation(self):
        task = fixture(); plan = dispatch.plan(task, recommendation(task), runtime())
        r = receipt(plan); r['checks'][0].update(passed=False, evidence='required dependency missing', exit_code=1)
        r['failure_type'] = 'capability'
        result = dispatch.assess(plan, r)
        self.assertEqual((result['status'], result['suggested_minimum_role']), ('revise', 'astra'))
        task['host']['attempt_count'] = 1
        task['host']['reviewed_sha256'] = route.review_digest(task)
        second = dispatch.plan(task, recommendation(task), runtime())
        r2 = receipt(second); r2['checks'][0].update(passed=False, evidence='required dependency missing', exit_code=1)
        r2['failure_type'] = 'capability'
        self.assertEqual(dispatch.assess(second, r2)['status'], 'review')


if __name__ == '__main__':
    unittest.main(verbosity=2)
