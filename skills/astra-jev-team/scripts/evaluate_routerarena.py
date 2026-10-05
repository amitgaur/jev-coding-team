#!/usr/bin/env python3
"""Run bounded, batched live Jev classification on prepared RouterArena tasks."""
import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path
import statistics

ROLES = ("luna", "sol", "astra")


def score(tasks, gold, predictions):
    matrix = {label: {pred: 0 for pred in (*ROLES, "review")} for label in ROLES}
    per_class = {}
    exact = raw_exact = covered = selective_correct = 0
    for role in ROLES:
        class_rows = [t for t in tasks if gold[t["id"]]["proxy_route"] == role]
        class_correct = sum(predictions[t["id"]]["route"] == role for t in class_rows)
        per_class[role] = {"n": len(class_rows), "effective_correct": class_correct,
                           "effective_accuracy": class_correct / len(class_rows) if class_rows else None,
                           "raw_choice_correct": sum(predictions[t["id"]]["raw_choice"] == role for t in class_rows)}
    for task in tasks:
        expected = gold[task["id"]]["proxy_route"]
        result = predictions[task["id"]]
        actual = result["route"]
        matrix[expected][actual] += 1
        exact += actual == expected
        raw_exact += result["raw_choice"] == expected
        if actual in ROLES:
            covered += 1
            selective_correct += actual == expected
    n = len(tasks)
    return {"n": n, "proxy_exact_effective_correct": exact,
            "proxy_exact_effective_accuracy": exact / n if n else None,
            "proxy_exact_raw_choice_correct": raw_exact,
            "proxy_exact_raw_choice_accuracy": raw_exact / n if n else None,
            "proxy_macro_effective_accuracy": statistics.mean(
                values["effective_accuracy"] for values in per_class.values()
                if values["effective_accuracy"] is not None),
            "review_count": n - covered, "review_rate": (n-covered)/n if n else None,
            "substantive_coverage": covered/n if n else None,
            "selective_accuracy": selective_correct/covered if covered else None,
            "per_class": per_class, "confusion_matrix_including_review": matrix,
            "reason_counts": dict(collections.Counter(predictions[t["id"]]["reason"] for t in tasks))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--skill-scripts", type=Path, required=True,
                        help="Path to astra-jev-team/scripts for the frozen route.py evaluator")
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live:
        parser.error("live official TypeSafe calls are required; pass --live")
    if args.limit not in (4, 60) or args.batch_size != 10:
        parser.error("frozen protocol: --limit 4 or 60; --batch-size 10")
    sys.path.insert(0, str(args.skill_scripts.resolve()))
    import route  # noqa: E402
    tasks = json.loads((args.dataset / "tasks.json").read_text())[:args.limit]
    gold = json.loads((args.dataset / "gold.json").read_text())
    args.out.mkdir(parents=True, exist_ok=False)
    batches, predictions, elapsed = [], {}, 0.0
    # route.execute always validates and saves a CLI dry-run before its one live call.
    for start in range(0, len(tasks), args.batch_size):
        batch = tasks[start:start + args.batch_size]
        batch_out = args.out / f"batch-{start//args.batch_size+1:02d}"
        result = route.execute(batch, batch_out, live=True)
        elapsed += result["elapsed_seconds"]
        predictions.update({entry["id"]: entry for entry in result["routes"]})
        batches.append({"ids": [task["id"] for task in batch],
                        "call_attempted": result["call_attempted"],
                        "jev_called": result["jev_called"],
                        "routes": result["routes"],
                        "elapsed_seconds": result["elapsed_seconds"]})
    summary = {
        "dataset": "RouterArena sub_10",
        "dataset_revision": json.loads((args.dataset / "manifest.json").read_text())["dataset_revision"],
        "dataset_manifest_sha256": hashlib.sha256((args.dataset / "manifest.json").read_bytes()).hexdigest(),
        "route_script_sha256": hashlib.sha256((args.skill_scripts / "route.py").read_bytes()).hexdigest(),
        "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "jev_model": route.MODEL, "provider": "official TypeSafe",
        "proxy_mapping": {"easy": "luna", "medium": "sol", "hard": "astra"},
        "proxy_warning": "Published task difficulty is not validated gold for Astra/Sol/Luna skill routing.",
        "answer_keys_and_difficulty_in_requests": False,
        "live_requested": True, "batches": batches,
        "calls_attempted": sum(b["call_attempted"] for b in batches),
        "jev_calls_confirmed": sum(b["jev_called"] for b in batches),
        "elapsed_seconds_total": elapsed,
        "metrics": score(tasks, gold, predictions),
        "protocol": "One smoke run at n=4 or one full run at n=60; frozen v1 thresholds; no tuning.",
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
