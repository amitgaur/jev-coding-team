#!/usr/bin/env python3
"""Recompute secondary expected-random and Wilson diagnostics from frozen receipts."""
import argparse
import json
from pathlib import Path


def wilson(correct, total, z=1.96):
    if total == 0:
        return None
    p = correct / total
    denom = 1 + z*z/total
    center = (p + z*z/(2*total)) / denom
    half = z*((p*(1-p)/total + z*z/(4*total*total)) ** .5) / denom
    return [center-half, center+half]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads((args.run / "summary.json").read_text())
    gold = json.loads((args.dataset / "gold.json").read_text())
    rows = [gold[row_id]["correct"] for row_id in summary["test_ids"]]
    metrics = summary["metrics"]
    weak = metrics["always_weak"]; strong = metrics["always_strong"]
    fallback = metrics["jev_effective_with_strong_fallback"]
    pstrong = fallback["strong_call_fraction"]
    n = len(rows)
    output = {
        "based_on_run_summary_sha256": __import__("hashlib").sha256((args.run / "summary.json").read_bytes()).hexdigest(),
        "n": n,
        "jev_strong_fallback_accuracy_wilson_95": wilson(fallback["correct"], n),
        "independent_50_50_random_expected": {
            "expected_accuracy": (weak["accuracy"] + strong["accuracy"]) / 2,
            "expected_strong_call_fraction": .5,
            "formula": "0.5 * always_weak_accuracy + 0.5 * always_strong_accuracy",
        },
        "random_matched_to_jev_strong_call_share_expected": {
            "expected_accuracy": (1-pstrong)*weak["accuracy"] + pstrong*strong["accuracy"],
            "strong_call_fraction": pstrong,
            "formula": "(1-p) * always_weak_accuracy + p * always_strong_accuracy",
            "note": "Expected value for random independent model assignment at the Jev+fallback strong-call rate; not another model call run.",
        },
        "seeded_random_realization": metrics["seeded_random_50_50"],
        "oracle": metrics["oracle_per_item"],
    }
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
