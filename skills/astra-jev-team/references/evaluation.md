# Evaluation protocol v1

There are three different questions. Keep their scores separate:

1. **Policy agreement:** Does Jev classify a described subtask according to our
   role definitions? `evals/cases.jsonl` and the separate `evals/gold.json` test this.
2. **Host behavior:** Does the consumer abstain on invalid/uncertain responses,
   preserve authority, handle dependencies, and verify worker artifacts?
3. **Task outcomes:** Does selecting a worker preserve completion quality at a
   measured total cost, compared with always using a fixed model?

Good scores on the first two do not establish the third.

The original synthetic and RouterArena evaluations explicitly load frozen
`evals/baselines/route.py` (v1). Keep those results and cases unchanged. V2
mitigation tests are regression checks; they do not restore held-out status to
previously inspected cases.

## Synthetic gold

48 author-defined synthetic cases: 16 development and 32 held-out, balanced over
`luna`, `sol`, `astra`, `review`; 48 distinct families. A separate Sol agent authored
cases and labels from the frozen role policy. Codex reviewed their evidence and
rationales before live scoring. These are policy fixtures, **not human-validated
benchmark gold**. Ambiguity, prompt injection, scoped security work, difficult but
answerable tasks, writing/research, and text-length controls are represented.

Related future variants must stay in one split. Do not add gold route, rationale,
critical flag, split, or family to classifier state. The runner's allowlist includes
only task ID, goal, work, evidence and acceptance. Cases use synthetic data only.

```
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/evaluate.py --split dev --limit 4 --out /tmp/ajev-dry
python3 scripts/evaluate.py --split dev --limit 4 --out /tmp/ajev-pilot --live
python3 scripts/evaluate.py --split dev --out /tmp/ajev-dev --live
python3 scripts/evaluate.py --split heldout --out /tmp/ajev-heldout --live
```

Use a fresh output directory each time. The pilot checks transport and parsing;
overlap with development is disclosed and never added to its denominator.
Each invocation runs a dry-run before any paid TypeSafe request. Do not repeatedly
rerun held-out cases or tune from them; preserve first-run results. A held-out case
seen during authoring is not hidden from the authors, only from the classifier.

Report effective accuracy and Wilson 95% interval, raw Choice accuracy, substantive
coverage, selective accuracy, confusion matrix, provider/invalid errors and critical
underdelegations. A correct semantic `review` differs from an uncertainty fallback.
`critical_underdelegations` counts less demanding effective routes for marked gold
cases (including substantive routing when critical gold is `review`). Failures stay
in the denominator. Report class counts, actual model/provider, request and input
hashes, elapsed time, and raw response receipts. CLI elapsed time is not end-to-end
agent latency. No monetary cost is inferred from model reputation or route counts.

## Host and orchestration tests

`test_route.py` and `test_evaluate.py` run deterministic, offline tests using clearly identified test
doubles. It exercises typed responses, candidate membership, distribution validity,
provider identity, uncertainty, authorization, missing models, retry bounds, evidence-hash
sensitivity, dry-run ordering and evidence exclusion. Passing does not mean Jev
was called or an agent completed work. File ownership, current repository state,
actual permissions, free slots, and attempt counts are host observations; the
helper does not independently inspect or enforce them against external state.

For behavioral forward-testing, give another agent only the skill and the `prompt`
and `observations` fields of a row in `evals/orchestration.json`. Withhold `expected`
until scoring. Evaluate actual tool traces and artifacts where available; a written
plan alone is a dry run. Never fabricate model invocation receipts. For a live
workflow, use a temporary isolated workspace and synthetic input, then inspect
outputs and rerun acceptance checks. Public network or paid calls need existing
scope authorization; tests do not grant it.

## Public benchmarks

Public benchmark adapters belong alongside this protocol with pinned revisions,
file hashes, sampling seed, exclusions, attribution and license status. Download
scripts should fetch exact revisions; avoid bundling datasets with unclear rights.
Never train or tune on an evaluation-only dataset such as RouterArena.

RouterArena difficulty labels can test an explicitly declared complexity proxy:
`easy→luna`, `medium→sol`, `hard→astra`. This is **not** published gold for these model
roles, an official RouterArena score, or worker correctness. The skill's role
policy also considers evidence completeness and work type, so disagreement may
expose proxy mismatch as well as classifier failure. Hide difficulty, answer,
category labels and recorded model outcomes from classifier inputs.

For public per-model outcome matrices, preserve native model IDs and replay only
recorded outcomes; do not rename historical models Astra/Sol/Luna. Choose any
capability profile, threshold and baseline on a disjoint calibration partition.
Score against a held-out partition with identical complete-case eligibility.
Report always-cheapest, best fixed model, seeded random and oracle baselines,
coverage, quality regret and observed cost where provided. Test-time outcomes
must never enter the routing prompt. This validates the selection mechanism on
that historical roster, not current Astra/Sol/Luna task performance.

## Publication decision

Starter targets, set before live results: all deterministic safety tests pass;
zero critical underdelegations on synthetic held-out cases; synthetic effective
accuracy at least 90%, selective accuracy at least 95%, substantive coverage at
least 60%. These are project release targets, not statistically proven guarantees.

Public proxy scores are diagnostic, not a substitute for outcome validation. To
claim validated efficiency of the actual team, collect an outcome matrix for the
actual models on representative tasks and include total classifier/worker/retry/
verification usage against fixed-model baselines. Until then, publish only as an
experimental skill with transparent results if the user chooses to do so. Do not
submit an official leaderboard entry or claim general superiority from a subset.

## V2 regression diagnostics

See [injection-fix.md](injection-fix.md) for paired singleton and original-context
diagnostics. Run `scripts/evaluate_injection.py --help` for its explicit inputs.
Gold remains separate. These known cases cannot serve as new held-out evidence.
The operational v2 router isolates tasks; historical batched evaluators use the
frozen v1 baseline.
