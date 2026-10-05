#!/usr/bin/env python3
"""Prepare fixed RouteLLM GSM8K calibration/test splits from a pinned source."""
import argparse
import csv
import hashlib
import io
import json
import random
import urllib.request
from pathlib import Path

REPO = "lm-sys/RouteLLM"
REVISION = "0b64fdafe049e596a3f5657c219329f24af24198"
BASE = f"https://raw.githubusercontent.com/{REPO}/{REVISION}/routellm/evals/gsm8k"
SEED = 20261004
WEAK = "mistralai/Mixtral-8x7B-Instruct-v0.1"
STRONG = "gpt-4-1106-preview"
FILES = ("gsm8k_responses.csv", "contaminated_prompts.jsonl", "test.jsonl")


def download(name):
    with urllib.request.urlopen(f"{BASE}/{name}", timeout=60) as response:
        data = response.read()
    return data, hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    blobs, hashes = {}, {}
    for name in FILES:
        blobs[name], hashes[name] = download(name)
    test_prompts = {row["question"] for row in
                    (json.loads(line) for line in blobs["test.jsonl"].decode().splitlines() if line)}
    contaminated = {row["eval_prompt"] for row in
                    (json.loads(line) for line in blobs["contaminated_prompts.jsonl"].decode().splitlines() if line)}
    all_rows = list(csv.DictReader(io.StringIO(blobs["gsm8k_responses.csv"].decode("utf-8-sig"))))
    seen = set()
    clean = []
    for row in all_rows:
        prompt = row["prompt"]
        if prompt in contaminated or prompt not in test_prompts or prompt in seen:
            continue
        if row[WEAK] not in ("True", "False") or row[STRONG] not in ("True", "False"):
            raise ValueError("missing or non-boolean original model outcome")
        seen.add(prompt)
        clean.append({"prompt": prompt, WEAK: row[WEAK] == "True", STRONG: row[STRONG] == "True"})
    if len(clean) < 80:
        raise ValueError(f"expected >=80 unique uncontaminated test rows, found {len(clean)}")
    rng = random.Random(SEED)
    picked = rng.sample(clean, 80)
    calibration = picked[:20]
    heldout = picked[20:]

    def records(rows, prefix):
        result = []
        for i, row in enumerate(rows, 1):
            row_id = f"{prefix}-{i:03d}"
            prompt_hash = hashlib.sha256(row["prompt"].encode()).hexdigest()
            result.append({"id": row_id, "prompt_sha256": prompt_hash, "prompt": row["prompt"],
                           "correct": {WEAK: row[WEAK], STRONG: row[STRONG]}})
        return result

    calibration_records = records(calibration, "cal")
    heldout_records = records(heldout, "test")
    # Only aggregate calibration performance is sent with the heldout requests.
    summary = {"n": len(calibration), "models": {}}
    for model in (WEAK, STRONG):
        correct = sum(row["correct"][model] for row in calibration_records)
        summary["models"][model] = {"correct": correct, "n": len(calibration_records),
                                     "accuracy": correct / len(calibration_records)}
    best_calibration_model = max((WEAK, STRONG),
        key=lambda model: (summary["models"][model]["accuracy"], model == WEAK))
    summary["best_fixed_candidate"] = best_calibration_model
    summary["purpose"] = "Aggregate performance on disjoint 20-row calibration set; not per-item evidence."

    def save_json(path, value):
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    cal_path = args.out / "calibration.json"
    heldout_path = args.out / "heldout.json"
    tasks_path = args.out / "tasks.json"
    gold_path = args.out / "gold.json"
    summary_path = args.out / "calibration-summary.json"
    save_json(cal_path, calibration_records)
    save_json(heldout_path, heldout_records)
    tasks = []
    gold = {}
    for row in heldout_records:
        tasks.append({"id": row["id"], "goal": "Answer this GSM8K math question.",
            "work": "Read the problem and determine which of the two available historical models is more likely to answer correctly.",
            "evidence": [row["prompt"]],
            "acceptance": ["Select the lower-cost Mixtral model unless the GPT-4 model is more likely to change an incorrect answer to a correct one.",
                           "Use review when the supplied question does not support a confident capability judgment."]})
        gold[row["id"]] = {"correct": row["correct"], "prompt_sha256": row["prompt_sha256"]}
    save_json(tasks_path, tasks)
    save_json(gold_path, gold)
    save_json(summary_path, summary)
    manifest = {
        "benchmark": "RouteLLM GSM8K historical response replay",
        "repository": f"https://github.com/{REPO}", "revision": REVISION,
        "repository_license": "Apache-2.0 (RouteLLM repository); GSM8K source dataset is MIT per its official card.",
        "source_files": {name: {"url": f"{BASE}/{name}", "sha256": hashes[name]} for name in FILES},
        "source_rows": len(all_rows), "canonical_test_prompts": len(test_prompts),
        "contaminated_prompts_excluded": len(contaminated), "eligible_unique_rows": len(clean),
        "selected_rows": 80, "calibration_rows": 20, "heldout_rows": 60,
        "seed": SEED, "selection": "Sample 80 unique test prompts from exact-contamination-filtered rows, then first 20 calibration and next 60 heldout; fixed before observing selected outcomes.",
        "weak_model": WEAK, "strong_model": STRONG,
        "source_outcomes": "Boolean exact-answer correctness columns and original response completions exist in RouteLLM CSV; only the original correctness booleans are retained for selected rows.",
        "contamination_rule": "Exclude exact prompt strings listed as eval_prompt in RouteLLM contaminated_prompts.jsonl; also require exact match to official test.jsonl question.",
        "limitations": ["Historical 2024 model pair; results do not establish current Astra/Sol/Luna model outcomes.",
                        "Correctness is only on GSM8K math questions and one fixed prompt template.",
                        "No per-item heldout correctness or gold answers are sent to Jev.",
                        "No token usage or price data is available here; no monetary savings are reported."],
        "source_links": ["https://github.com/lm-sys/RouteLLM/tree/" + REVISION + "/routellm/evals/gsm8k",
                         "https://huggingface.co/datasets/openai/gsm8k"],
        "files_sha256": {}
    }
    for path in (cal_path, heldout_path, tasks_path, gold_path, summary_path):
        manifest["files_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    save_json(args.out / "manifest.json", manifest)
    print(json.dumps({"eligible_unique_rows": len(clean), "contaminated_excluded": len(contaminated),
                      "calibration": summary, "heldout_rows": len(heldout_records),
                      "files_sha256": manifest["files_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
