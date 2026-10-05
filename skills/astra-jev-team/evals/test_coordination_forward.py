import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import route
import dispatch


def task(mode='host', minimum='luna', available=None):
    host = {'snapshot':'tree-x','delegation_authorized':True,'share_authorized':True,
            'dependency_ready':True,'write_conflict':False,'trivial':False,'attempt_count':0,
            'available': available or ['luna','sol'], 'minimum_role':minimum,'retain_for_host':False,
            'routing_brief':{'goal':'Fix parser crash','work':'Implement scoped parser fix',
                'facts':['Empty token raises ValueError'],'acceptance':['Empty token returns a parse error']},
            'dispatch':{'phase':'implement','owned_paths':['src/parser.py'],'deliverable':'Parser fix',
                'checks':[{'id':'empty','acceptance_index':0,'method':'run focused regression'}]}}
    if mode is not None: host['coordination_mode'] = mode
    t={'id':'parser','goal':'Fix parser crash','work':'Implement scoped parser fix',
       'evidence':['Observed ValueError'],'acceptance':['Empty token returns a parse error'],'host':host}
    host['reviewed_sha256']=route.review_digest(t)
    return t


def rec(t, role):
    return {'id':t['id'],'route':role,'reason':'selected','raw_choice':role,
            'input_sha256':route.fingerprint(t),'snapshot':t['host']['snapshot']}


def report(choice):
    probs={r:(.94 if r==choice else .02) for r in route.ROLES}
    return {'mode':'jev_api','jev_called':True,'transport':'typesafe',
            'response':{'answers':{'q0':{'type':'choice','choice':choice,'probabilities':probs,'confidence':.9}}},
            'decisions':{'q0':{'value':choice,'status':'selected'}}}


def runtime(model='sol-model', coordinator='astra-model'):
    return {'bindings':{'luna':{'model':'luna-model','effort':'low'},
                        'sol':{'model':model,'effort':'medium'},
                        'astra':{'model':'astra-model','effort':'high'}},
            'catalog':{'luna-model':['low'],'sol-model':['medium'],'astra-model':['high']},
            'coordinator_model':coordinator,'workspace_root':'/repo',
            'native_delegation':True,'free_slots':1,'benefit_justified':True}


def dispatch_plan(t, role, rt=None): return dispatch.plan(t, rec(t,role), rt or runtime())


class CoordinationEvaluation(unittest.TestCase):
    def test_host_mode_allows_routine_sol_and_plan_records_mode_and_inventory(self):
        t=task(); decision=route.consume(t,'q0',report('sol'),0)
        self.assertEqual((decision['route'],decision['reason']),('sol','selected'))
        p=dispatch_plan(t,'sol')
        self.assertEqual(p['mode'],'worker')
        self.assertEqual(p['coordination_mode'],'host')
        self.assertEqual(p['available_roles'],['luna','sol'])

    def test_host_mode_astra_choice_is_retained_with_raw_choice(self):
        t=task(); result=route.consume(t,'q0',report('astra'),0)
        self.assertEqual((result['route'],result['reason'],result['raw_choice']),
                         ('review','complex_work_retained_by_host','astra'))
        checked=route.check_recommendation(t,rec(t,'astra'))
        self.assertEqual((checked['route'],checked['reason']),('review','complex_work_retained_by_host'))

    def test_host_mode_minimum_astra_with_astra_unavailable_stays_host(self):
        t=task(minimum='astra',available=['luna','sol'])
        self.assertEqual(route.gate(t),('review','complex_work_retained_by_host'))
        with tempfile.TemporaryDirectory() as d, patch('route.subprocess.run') as run:
            result=route.execute([t],Path(d)/'run',live=True)
            run.assert_not_called()
            self.assertEqual(result['routes'][0]['reason'],'complex_work_retained_by_host')

    def test_astra_minimum_in_astra_mode_skips_provider_and_dispatch(self):
        t=task(mode='astra',minimum='astra',available=['luna','sol','astra'])
        self.assertEqual(route.gate(t),('astra','host_minimum_role'))
        p=dispatch_plan(t,'astra')
        self.assertEqual(p['mode'],'host')
        self.assertEqual(p['role'],'astra')

    def test_invalid_modes_fail_closed(self):
        for bad in ('',None,'automatic','HOST',True,1):
            t=task(); t['host']['coordination_mode']=bad
            t['host']['reviewed_sha256']=route.review_digest(t)
            self.assertEqual(route.gate(t)[0],'review')

    def test_omitted_mode_preserves_legacy_astra_recommendation(self):
        t=task(mode=None,available=['luna','sol','astra'])
        self.assertEqual(route.coordination_mode(t),'astra')
        result=route.consume(t,'q0',report('astra'),0)
        self.assertEqual((result['route'],result['reason']),('astra','selected'))
        self.assertEqual(dispatch_plan(t,'astra')['mode'],'host')

    def test_omitted_mode_minimum_astra_preserves_host_floor(self):
        t=task(mode=None,minimum='astra',available=['luna','sol','astra'])
        self.assertEqual(route.gate(t),('astra','host_minimum_role'))
        self.assertEqual(dispatch_plan(t,'astra')['mode'],'host')

    def test_coordinator_sol_binding_remains_local(self):
        t=task(); rt=runtime(model='coordinator-sol',coordinator='coordinator-sol')
        rt['catalog']['coordinator-sol']=['medium']
        p=dispatch_plan(t,'sol',rt)
        self.assertEqual((p['mode'],p['reason']),('host','selected_model_is_coordinator'))

    def test_host_mode_capability_failure_never_escalates_to_astra(self):
        t=task(); p=dispatch_plan(t,'sol')
        receipt={'host_verified':True,'plan_sha256':p['plan_sha256'],'start_snapshot':p['snapshot'],
            'end_snapshot':'tree-y','workspace_root':p['workspace_root'],'agent_id':'a',
            'actual_model':p['spawn']['model'],'actual_effort':p['spawn']['reasoning_effort'],
            'changed_paths':['src/parser.py'],'checks':[{'id':'empty','passed':False,
            'evidence':'required package unavailable','exit_code':1}],'unresolved_risks':[],
            'failure_type':'capability'}
        out=dispatch.assess(p,receipt)
        self.assertEqual((out['status'],out['reason']),('review','capability_failure_needs_host'))

    def test_astra_capability_escalation_requires_actual_inventory(self):
        t=task(mode=None,available=['luna','sol']); p=dispatch_plan(t,'sol')
        receipt={'host_verified':True,'plan_sha256':p['plan_sha256'],'start_snapshot':p['snapshot'],
            'end_snapshot':'tree-y','workspace_root':p['workspace_root'],'agent_id':'a',
            'actual_model':p['spawn']['model'],'actual_effort':p['spawn']['reasoning_effort'],
            'changed_paths':['src/parser.py'],'checks':[{'id':'empty','passed':False,
            'evidence':'required package unavailable','exit_code':1}],'unresolved_risks':[],
            'failure_type':'capability'}
        self.assertEqual(dispatch.assess(p,receipt)['reason'],'no_available_escalation')


if __name__ == '__main__': unittest.main(verbosity=2)
