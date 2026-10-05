"""Checks for evaluation bookkeeping; no model or network calls."""
import unittest
import evaluate

class EvaluationTests(unittest.TestCase):
    def test_frozen_suite_integrity(self):
        cases, gold = evaluate.load_suite()
        self.assertEqual(len(cases), 48)
        for split, count in [('dev', 4), ('heldout', 8)]:
            for label in ('luna','sol','astra','review'):
                self.assertEqual(sum(c['split']==split and gold[c['id']]['route']==label for c in cases), count)

    def test_failures_and_abstention_stay_in_denominator(self):
        cases = [{'id': x} for x in ('a','b','c','d')]
        gold = {x: {'route': role, 'critical': True, 'rationale':'fixture'}
                for x, role in zip(('a','b','c','d'), ('luna','sol','astra','review'))}
        result = {'routes': [
            {'id':'a','route':'luna','raw_choice':'luna','reason':'selected'},
            {'id':'b','route':'review','raw_choice':'sol','reason':'uncertain'},
            {'id':'c','route':'review','raw_choice':None,'reason':'provider_error'},
            {'id':'d','route':'sol','raw_choice':'sol','reason':'selected'}]}
        score = evaluate.score(cases,gold,result)
        self.assertEqual(score['n'],4)
        self.assertEqual(score['accuracy'],.25)
        self.assertEqual(score['raw_choice_accuracy'],.5)
        self.assertEqual(score['substantive_coverage'],.5)
        self.assertEqual(score['selective_accuracy'],.5)
        self.assertEqual(score['provider_or_invalid_errors'],1)
        self.assertEqual(score['critical_underdelegations'],1)

    def test_no_substantive_predictions(self):
        cases=[{'id':'a'}]
        gold={'a': {'route':'astra','critical': True,'rationale':'fixture'}}
        result={'routes':[{'id':'a','route':'review','raw_choice':None,'reason':'invalid_response'}]}
        score=evaluate.score(cases,gold,result)
        self.assertEqual(score['accuracy'],0)
        self.assertIsNone(score['selective_accuracy'])
        self.assertEqual(score['critical_underdelegations'],0)

    def test_confidence_interval(self):
        lower, upper=evaluate.wilson(5,10)
        self.assertLess(lower,.5)
        self.assertGreater(upper,.5)
        self.assertIsNone(evaluate.wilson(0,0))

if __name__ == '__main__':
    unittest.main()
