"""Offline checks for public replay's bookkeeping and invalid-response handling."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import evaluate_routellm_gsm8k as replay

class PublicReplayTests(unittest.TestCase):
    def test_four_outcome_categories(self):
        self.assertTrue(replay.scorer_sanity_check()['passed'])

    def test_non_object_response_becomes_review(self):
        class Result:
            returncode = 0
            stdout = '[]'
        task = {'id':'a', 'goal':'g', 'work':'w','evidence':['e'],'acceptance':['a']}
        calibration = {'models': {m: {'correct':1,'n':2} for m in (replay.WEAK,replay.STRONG)}}
        with tempfile.TemporaryDirectory() as tmp, patch('evaluate_routellm_gsm8k.subprocess.run', return_value=Result()):
            result = replay.run_batch([task],calibration,Path(tmp)/'batch',Path('test-double'))
            self.assertFalse(result['jev_called'])
            self.assertEqual(result['routes'][0]['route'],'review')

    def test_failed_call_keeps_case(self):
        class Result:
            returncode = 1
            stdout = ''
        task = {'id':'a', 'goal':'g', 'work':'w','evidence':['e'],'acceptance':['a']}
        calibration = {'models': {m: {'correct':1,'n':2} for m in (replay.WEAK,replay.STRONG)}}
        with tempfile.TemporaryDirectory() as tmp, patch('evaluate_routellm_gsm8k.subprocess.run', return_value=Result()):
            result = replay.run_batch([task],calibration,Path(tmp)/'batch',Path('test-double'))
            self.assertEqual(len(result['routes']),1)
            self.assertEqual(result['routes'][0]['route'],'review')

if __name__ == '__main__':
    unittest.main()
