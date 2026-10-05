"""Offline host-led and optional-Astra integration regressions."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import route
import dispatch
from test_route import report
from test_dispatch import fixture, reattest, receipt


def host_fixture():
    t, r, runtime = fixture()
    t['host'].update(coordination_mode='host', available=['luna', 'sol'])
    runtime['coordinator_model'] = 'gpt-6.1-sol'
    runtime['bindings']['luna'] = {'model': 'gpt-6-luna', 'effort': 'medium'}
    runtime['catalog']['gpt-6-luna'] = ['medium']
    reattest(t, r)
    return t, r, runtime


class CoordinationTests(unittest.TestCase):
    def test_sol_host_handles_sol_locally(self):
        p = dispatch.plan(*host_fixture())
        self.assertEqual(p['mode'], 'host')
        self.assertEqual(p['reason'], 'selected_model_is_coordinator')
        self.assertNotIn('spawn', p)

    def test_sol_host_can_delegate_luna(self):
        t, r, runtime = host_fixture()
        t['host']['minimum_role'] = 'luna'
        reattest(t, r)
        r = route.consume(t, 'q0', report('luna'), 0)
        p = dispatch.plan(t, r, runtime)
        self.assertEqual(p['mode'], 'worker')
        self.assertEqual(p['spawn']['model'], 'gpt-6-luna')

    def test_other_host_can_delegate_sol(self):
        t, r, runtime = host_fixture()
        runtime['coordinator_model'] = 'another-observed-host'
        self.assertEqual(dispatch.plan(t, r, runtime)['spawn']['model'], 'gpt-6.1-sol')

    def test_complex_floor_stays_host_without_provider(self):
        t, r, runtime = host_fixture()
        t['host']['minimum_role'] = 'astra'
        reattest(t, r)
        with tempfile.TemporaryDirectory() as temp, patch('route.subprocess.run') as provider:
            result = route.execute([t], Path(temp)/'run', live=True)
            provider.assert_not_called()
        rec = result['routes'][0]
        self.assertEqual(rec['reason'], 'complex_work_retained_by_host')
        self.assertEqual(dispatch.plan(t, rec, runtime)['mode'], 'host')

    def test_jev_complexity_signal_is_retained_even_with_astra_inventory(self):
        for available in (['luna', 'sol'], ['luna', 'sol', 'astra']):
            t, r, runtime = host_fixture()
            t['host']['available'] = available
            runtime['bindings']['astra'] = {'model': 'gpt-6-astra', 'effort': 'medium'}
            runtime['catalog']['gpt-6-astra'] = ['medium']
            reattest(t, r)
            rec = route.consume(t, 'q0', report('astra'), 0)
            self.assertEqual(rec['raw_choice'], 'astra')
            self.assertEqual(rec['reason'], 'complex_work_retained_by_host')
            self.assertEqual(dispatch.plan(t, rec, runtime)['mode'], 'host')

    def test_invalid_modes_fail_closed(self):
        for mode in (None, False, [], {}, 'automatic'):
            t, r, runtime = host_fixture()
            t['host']['coordination_mode'] = mode
            reattest(t, r)
            self.assertEqual(route.gate(t), ('review', 'invalid_coordination_mode'))

    def test_mode_change_invalidates_saved_route(self):
        t, r, runtime = fixture()
        t['host']['coordination_mode'] = 'host'
        self.assertEqual(dispatch.plan(t, r, runtime)['reason'], 'stale_recommendation')

    def test_host_policy_does_not_change_classifier_payload(self):
        t, r, runtime = fixture()
        expected = route.request_for([t])
        t['host']['coordination_mode'] = 'host'
        reattest(t, r)
        self.assertEqual(route.request_for([t]), expected)

    def test_legacy_astra_and_explicit_astra_still_work(self):
        for explicit in (False, True):
            t, r, runtime = fixture()
            if explicit:
                t['host']['coordination_mode'] = 'astra'
            t['host']['minimum_role'] = 'astra'
            reattest(t, r)
            self.assertEqual(route.gate(t), ('astra', 'host_minimum_role'))

    def test_host_mode_sol_failure_stays_host(self):
        t, r, runtime = host_fixture()
        runtime['coordinator_model'] = 'another-observed-host'
        p = dispatch.plan(t, r, runtime)
        observed = receipt(p)
        observed['checks'][0].update(passed=False, exit_code=1)
        observed['failure_type'] = 'capability'
        out = dispatch.assess(p, observed)
        self.assertEqual(out, {'status': 'review', 'reason': 'capability_failure_needs_host'})

    def test_absent_next_tier_not_suggested(self):
        t, r, runtime = fixture()
        t['host']['available'] = ['luna', 'sol']
        reattest(t, r)
        p = dispatch.plan(t, r, runtime)
        observed = receipt(p)
        observed['checks'][0].update(passed=False, exit_code=1)
        observed['failure_type'] = 'capability'
        self.assertEqual(dispatch.assess(p, observed)['reason'], 'no_available_escalation')

    def test_saved_astra_selection_cannot_bypass_host_mode(self):
        t, r, runtime = host_fixture()
        r.update(route='astra', raw_choice='astra')
        self.assertEqual(dispatch.plan(t, r, runtime)['reason'], 'complex_work_retained_by_host')


if __name__ == '__main__':
    unittest.main()
