#!/usr/bin/env python3
"""Evaluate frozen synthetic policy gold; labels never enter classifier requests."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = ROOT / 'evals/baselines/route.py'
spec = importlib.util.spec_from_file_location('baseline_route_v1', ROUTER_PATH)
route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(route)


def load_suite():
    cases = [json.loads(line) for line in (ROOT/'evals/cases.jsonl').read_text().splitlines() if line.strip()]
    gold = route.read(ROOT/'evals/gold.json')
    ids = [c['id'] for c in cases]
    if len(ids) != len(set(ids)) or set(ids) != set(gold):
        raise ValueError('case/gold ID mismatch')
    families = {}
    for c in cases:
        if c['split'] not in ('dev', 'heldout') or c['task']['id'] != c['id']:
            raise ValueError('invalid case')
        if c['family'] in families and families[c['family']] != c['split']:
            raise ValueError('family leaks across splits')
        families[c['family']] = c['split']
        g = gold[c['id']]
        if g['route'] not in route.ROLES or type(g['critical']) is not bool or not g['rationale']:
            raise ValueError('invalid gold')
    return cases, gold


def wilson(correct, total):
    if not total:
        return None
    z = 1.96; p = correct / total; d = 1 + z*z/total
    center = (p + z*z/(2*total))/d
    half = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/d
    return [center-half, center+half]


def score(cases, gold, result):
    predictions = {r['id']: r for r in result['routes']}
    matrix = defaultdict(Counter)
    correct = raw_correct = covered = selected_correct = errors = critical_under = 0
    misses = []
    tier = {'luna': 0, 'sol': 1, 'astra': 2, 'review': 3}
    for c in cases:
        g = gold[c['id']]; r = predictions[c['id']]
        expected, actual = g['route'], r['route']
        correct += actual == expected
        raw_correct += r['raw_choice'] == expected
        substantive = actual in ('luna','sol','astra')
        covered += substantive
        selected_correct += substantive and actual == expected
        errors += r['reason'] in ('provider_error','invalid_response')
        under = tier[actual] < tier[expected]
        critical_under += g['critical'] and under
        matrix[expected][actual] += 1
        if actual != expected:
            misses.append({'id': c['id'], 'gold': expected, 'route': actual,
                           'raw_choice': r['raw_choice'], 'reason': r['reason'], 'rationale': g['rationale']})
    n = len(cases)
    return {'n': n, 'correct': correct, 'accuracy': correct/n,
            'accuracy_wilson_95': wilson(correct,n),
            'raw_choice_correct': raw_correct, 'raw_choice_accuracy': raw_correct/n,
            'substantive_coverage': covered/n,
            'selective_accuracy': selected_correct/covered if covered else None,
            'provider_or_invalid_errors': errors, 'critical_underdelegations': critical_under,
            'confusion_matrix': dict(matrix), 'misses': misses}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--split', choices=['dev','heldout'], default='dev')
    p.add_argument('--limit', type=int)
    p.add_argument('--out', required=True)
    p.add_argument('--live', action='store_true')
    args = p.parse_args()
    cases, gold = load_suite()
    chosen = [c for c in cases if c['split'] == args.split]
    if args.limit is not None:
        if args.limit < 1:
            p.error('limit must be positive')
        chosen = chosen[:args.limit]
    tasks = []
    for c in chosen:
        t = {k: v for k,v in c['task'].items()}
        t['host'] = {'snapshot': route.VERSION, 'delegation_authorized': True,
                     'share_authorized': True, 'dependency_ready': True, 'write_conflict': False,
                     'trivial': False, 'attempt_count': 0, 'available': ['luna','sol','astra']}
        tasks.append(t)
    result = route.execute(tasks, args.out, args.live)
    hashes = {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
              for f in [ROOT/'evals/cases.jsonl',ROOT/'evals/gold.json',ROUTER_PATH]}
    summary = {'dataset': 'author-defined synthetic policy gold v1', 'router_version': route.VERSION, 'split': args.split,
               'model': route.MODEL, 'provider': 'typesafe', 'hashes': hashes,
               'ids': [c['id'] for c in chosen], 'live_requested': args.live,
               'jev_called': result['jev_called'], 'elapsed_seconds': result['elapsed_seconds'],
               'metrics': score(chosen, gold, result) if args.live else None,
               'limitations': ['Not human-validated gold or a public benchmark.',
                               'Classification agreement is not worker task success.',
                               'No monetary costs or savings inferred.']}
    route.save(Path(args.out)/'summary.json', summary)
    print(json.dumps(summary, indent=2))
    return 1 if args.live and summary['metrics']['provider_or_invalid_errors'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
