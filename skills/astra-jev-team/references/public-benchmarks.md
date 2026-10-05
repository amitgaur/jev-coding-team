# Public benchmark reproduction

Luna ran the first evaluation. [Results](results.md) record why this version remains
experimental. Downloaded public data stays outside the skill package; the packaged
[summary receipts](reports/) contain metrics and source manifests, not source text.

All commands below assume the current directory is this skill folder. Use fresh
output paths. A live flag invokes paid official TypeSafe requests after a saved
CLI dry-run. Existing authorization is necessary. The frozen protocol uses a
four-item transport smoke and one 60-item run; do not sum their denominators.

These public results use the frozen v1 classifier. The v2 input contract requires
a reviewed host brief; these datasets do not supply one, so silently applying v2
would not reproduce the same experiment. Do not tune on their evaluation labels.

## RouterArena: complexity proxy only

[Official repository](https://github.com/RouteWorks/RouterArena),
[dataset revision](https://huggingface.co/datasets/RouteWorks/RouterArena/tree/a4a062ce3313b56bb09c042e1bc37b61d34e3bd8).

The preparation script needs `pyarrow==25.0.1`, used in the verified run. Other
benchmark helpers use the Python standard library. Use an existing environment
with PyArrow or `uv run --with pyarrow==25.0.1` for preparation.

```
uv run --with pyarrow==25.0.1 python scripts/prepare_routerarena.py --out /tmp/ajev-ra-data
python3 scripts/evaluate_routerarena.py --skill-scripts evals/baselines --dataset /tmp/ajev-ra-data --out /tmp/ajev-ra-smoke --limit 4 --live
python3 scripts/evaluate_routerarena.py --skill-scripts evals/baselines --dataset /tmp/ajev-ra-data --out /tmp/ajev-ra-full --limit 60 --live
```

The Parquet URL pins the HF commit; hashes are recorded. Seed 20261004 samples
20 cases per difficulty. Full prompts/context/options are retained; gold answer,
difficulty and category are excluded from Jev input. easy→Luna, medium→Sol,
hard→Astra is an experimental proxy only. Do not call it official routing accuracy.
No answer generation or official leaderboard evaluation is performed.

RouterArena is evaluation-only: do not train, fit or tune on it. Its repository
code is Apache-2.0, but the HF metadata omits a dataset-wide license and constituent
sources have their own terms. Fetch locally; do not redistribute source rows
without confirming the necessary rights.

## RouteLLM GSM8K: historical outcome replay

[Official pinned source](https://github.com/lm-sys/RouteLLM/tree/0b64fdafe049e596a3f5657c219329f24af24198/routellm/evals/gsm8k).

```
python3 scripts/prepare_routellm_gsm8k.py --out /tmp/ajev-rl-data
python3 scripts/evaluate_routellm_gsm8k.py --self-test
python3 scripts/evaluate_routellm_gsm8k.py --dataset /tmp/ajev-rl-data --out /tmp/ajev-rl-smoke --limit 4 --live
python3 scripts/evaluate_routellm_gsm8k.py --dataset /tmp/ajev-rl-data --out /tmp/ajev-rl-full --limit 60 --live
python3 scripts/supplement_routellm_analysis.py --dataset /tmp/ajev-rl-data --run /tmp/ajev-rl-full --out /tmp/ajev-rl-supplement.json
```

Pinned CSV and JSON are parsed as data, never unpickled or executed. The loader
joins exact canonical test prompts, excludes listed contaminated prompts, and
samples 20 calibration plus 60 disjoint test rows using seed 20261004. Only
aggregate calibration scores enter test requests. Test outcomes stay local.

This is a separate selection prompt with the original Mixtral and GPT-4 model IDs,
not a remapping of their outcomes to Astra/Sol/Luna. Abstentions fall back to
GPT-4 by a frozen declared policy; both review coverage and fallback correctness
are reported. All rows remain in the denominator on errors. Baselines include
always-weak, always-strong, calibration-best fixed, one seeded random realization,
and oracle. The offline supplement computes expected-random baselines and a
Wilson interval without rerunning Jev. These records provide no token-price
accounting, so selection share cannot be reported as monetary savings.

RouteLLM repository code is Apache-2.0; the original GSM8K dataset is MIT. Preserve
upstream attribution and licenses in any future data redistribution. This skill
ships download scripts and derived summaries only.
