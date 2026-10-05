#!/usr/bin/env python3
"""Fetch a pinned RouterArena sub_10 split and build a label-blind Jev input set."""
import argparse
import hashlib
import json
import random
import urllib.request
import io
from pathlib import Path

import pyarrow.parquet as pq

DATASET = "RouteWorks/RouterArena"
REVISION = "a4a062ce3313b56bb09c042e1bc37b61d34e3bd8"
SEED = 20261004
PARQUET = f"https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/data/sub_10-00000-of-00001.parquet"
GOLD_ROUTE = {"easy": "luna", "medium": "sol", "hard": "astra"}


def fetch_rows():
    with urllib.request.urlopen(PARQUET, timeout=60) as response:
        parquet = response.read()
    rows = pq.read_table(io.BytesIO(parquet)).to_pylist()
    if len(rows) != 809:
        raise ValueError(f"expected 809 source rows; received {len(rows)}")
    return rows, hashlib.sha256(parquet).hexdigest()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--count", type=int, default=60)
    args = parser.parse_args()
    if args.count != 60:
        parser.error("the frozen public pilot is exactly 60 rows (20 per difficulty)")
    args.out.mkdir(parents=True, exist_ok=False)
    rows, parquet_sha256 = fetch_rows()
    pools = {level: [r for r in rows if r["Difficulty"] == level]
             for level in GOLD_ROUTE}
    if any(len(pool) < 20 for pool in pools.values()):
        raise ValueError("source split does not have 20 rows for each difficulty")
    rng = random.Random(SEED)
    selected = []
    for level in ("easy", "medium", "hard"):
        selected.extend(rng.sample(pools[level], 20))
    rng.shuffle(selected)

    source_path = args.out / "selected_source.jsonl"
    task_path = args.out / "tasks.json"
    gold_path = args.out / "gold.json"
    with source_path.open("w") as source:
        for row in selected:
            source.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    tasks, gold = [], {}
    for i, row in enumerate(selected):
        task_id = f"ra-{i+1:03d}"
        question = row["Question"].strip()
        if row["Context"].strip():
            question = "Context:\n" + row["Context"].strip() + "\n\nQuestion:\n" + question
        if row["Options"]:
            question += "\n\nOptions:\n" + "\n".join(
                f"{chr(65+j)}. {option}" for j, option in enumerate(row["Options"]))
        task = {
            "id": task_id,
            "goal": "Answer the supplied benchmark question.",
            "work": "Read the supplied question and any choices, then provide the correct answer.",
            "evidence": [question],
            "acceptance": ["Give a correct answer supported by the supplied question and context."],
            "host": {"snapshot": f"routerarena:{REVISION}:sub_10:{row['Global Index']}",
                     "delegation_authorized": True, "share_authorized": True,
                     "dependency_ready": True, "write_conflict": False,
                     "trivial": False, "attempt_count": 0,
                     "available": ["luna", "sol", "astra"]},
        }
        tasks.append(task)
        gold[task_id] = {"proxy_route": GOLD_ROUTE[row["Difficulty"]],
                         "difficulty": row["Difficulty"], "answer": row["Answer"],
                         "global_index": row["Global Index"],
                         "domain": row["Domain"], "category": row["Category"]}
    task_path.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n")
    gold_path.write_text(json.dumps(gold, indent=2, ensure_ascii=False) + "\n")
    manifest = {
        "benchmark": "RouterArena",
        "dataset_id": DATASET,
        "dataset_revision": REVISION,
        "dataset_files_revision_url": f"https://huggingface.co/datasets/{DATASET}/tree/{REVISION}",
        "dataset_parquet_url": PARQUET,
        "dataset_parquet_sha256": parquet_sha256,
        "split": "sub_10",
        "source_rows": 809,
        "selected_rows": len(selected),
        "sample_seed": SEED,
        "sampling": "20 rows sampled without replacement within each published difficulty, then shuffled",
        "difficulty_proxy_mapping": GOLD_ROUTE,
        "mapping_status": "experimental proxy only; RouterArena difficulty is not a validated Astra/Sol/Luna skill-routing label",
        "dataset_license": "Not specified in Hugging Face dataset card metadata; source collections may have their own terms. Local evaluation copy only; do not redistribute absent rights review.",
        "repository_code_license": "Apache-2.0 (RouterArena GitHub repository; not evidence that all upstream data has the same license)",
        "limitations": ["No per-model correctness/outcome matrix in this dataset schema.",
                        "No answer key or difficulty label is included in tasks.json sent to Jev.",
                        "Benchmark includes varied QA/code/generation tasks, while the skill's role rubric was written for delegated work classification."],
        "source_links": [
            "https://huggingface.co/datasets/RouteWorks/RouterArena",
            "https://github.com/RouteWorks/RouterArena",
            "https://arxiv.org/abs/2510.00202",
        ],
        "preparation_dependency": "pyarrow",
        "files_sha256": {},
    }
    for path in (source_path, task_path, gold_path):
        manifest["files_sha256"][path.name] = digest(path)
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"selected": len(selected), "difficulty_counts": {k: 20 for k in GOLD_ROUTE},
                      "output": str(args.out), "sha256": manifest["files_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
