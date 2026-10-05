# Evaluation status — 2026-10-04

**Experimental; does not meet the v1 publication targets.** Jev is an adviser;
the host must verify every recommendation before delegation. No automatic agent
dispatch is implemented. Do not advertise validated efficiency or robust routing.

V2 adds reviewed briefs, enforced host floors, snapshot checks and one task per
request. **65 offline tests pass after the host-coordination update.** [V2 diagnostic results](injection-fix.md) revise
the causal interpretation: removing c020's injected sentence did not fix the
original batch misroute; singleton v1 and v2 probes both passed. V2 is not yet
validated on fresh held-out cases. The metrics below are frozen v1 results.
The dispatch update adds model/effort plans, workspace/file scope, complete
acceptance-check coverage and host-attested outcome checks; it does not change
Jev prompts or demonstrate a coding performance improvement. Luna independently
ran nine additional offline scenarios, all passing. See
[the comparison and rationale](router-comparison.md). V2.2 adds explicit
[host coordination without Astra](coordination.md), checked by Luna in ten
additional offline scenarios. The nine previous dispatch scenarios still pass.
These checks do not measure coding-task success or cost savings.

Luna (`gpt-6-luna`) ran the live evaluations through official TypeSafe using
`jev-1.13.0`. A separate Sol agent authored synthetic policy fixtures; an Astra
agent reviewed the implementation and two orchestration scenarios. The scenarios
were written forward tests, not live worker-task benchmarks.

| Evaluation | Result |
|---|---|
| Offline consumer/scorer checks | 25 test groups pass |
| Skill structure validation | Pass |
| Synthetic development | 15/16 effective, 16 cases |
| Synthetic held-out | 25/32 effective (78.1%); raw Choice 26/32 (81.3%) |
| Held-out 95% Wilson interval | 61.2%–89.0% |
| Held-out substantive coverage | 19/32 (59.4%) |
| Held-out selective accuracy | 17/19 (89.5%) |
| Held-out critical underdelegations | 1 |
| RouterArena difficulty-to-role proxy | Raw 20/60 (33.3%); effective 11/60 (18.3%) |
| RouterArena review rate | 41/60 (68.3%) |

Synthetic held-out c020 describes untrusted plugin execution architecture but
contains a source appendix telling the router to select Luna. Jev selected Luna;
the frozen gold requires Astra. Both its reported Luna probability and confidence
were 1.0. Raising confidence thresholds cannot catch this observed wrong choice.
The result establishes a failure on that adversarial fixture, not the causal
impact of the injected text. The subsequent controlled comparison is documented
in the v2 report above.

The helper's malformed huge-number handling bug was fixed before live evaluation.
No routing rubric or threshold was tuned from these results. Original receipts
retain script and input hashes. Pilot observations overlap their larger sets and
are excluded from the reported larger-set denominator.

RouterArena's easy/medium/hard labels were mapped to Luna/Sol/Astra solely as a
predeclared experimental proxy. That mapping is not official role gold or worker
success. The adapter asks for answers supported by supplied question/context;
knowledge questions and native difficulty do not exactly match this skill's
source-based delegation rubric. No official RouterArena score is claimed.

Read [the full protocol](evaluation.md) before extending these tests. Address the
adversarial case on development data, then use newly authored held-out cases for
an unbiased policy evaluation. Do not tune on RouterArena's evaluation-only data.
Actual Astra/Sol/Luna outcome and cost comparisons remain unmeasured.

## Public outcome replay

A separate [RouteLLM GSM8K](https://github.com/lm-sys/RouteLLM/tree/0b64fdafe049e596a3f5657c219329f24af24198/routellm/evals/gsm8k)
pilot used the original historical Mixtral/GPT-4 pair with 20 calibration and 60
disjoint evaluation questions. Jev saw no evaluation outcomes. With a declared
GPT-4 fallback on 46 abstentions, recorded answer correctness was 51/60 (85.0%)
and GPT-4 share 46/60 (76.7%). Always-GPT-4 scored 52/60 (86.7%); always-Mixtral
40/60 (66.7%); the per-item oracle 58/60 (96.7%). Raw Jev choices scored 44/60.

This tests a separate candidate-selection prompt using the same Jev integration,
not the four-role skill rubric. It is a small historical replay, not a result for
current Astra/Sol/Luna. There are no token prices or measured monetary savings.
See [public benchmark reproduction](public-benchmarks.md) for commands and scope.
