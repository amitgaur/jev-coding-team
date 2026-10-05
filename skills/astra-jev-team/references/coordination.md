# Host coordination with optional Astra

The skill is displayed as Jev Coding Team. Its invocation remains
`$astra-jev-team` to preserve existing links and installed paths.

## Host mode: no Astra worker required

For new work, use host mode unless the user asks for Astra:

> Use $astra-jev-team without Astra. Keep coordination with the current host,
> delegate bounded work to available Sol/Luna workers, and verify the result.

Task control fields (merge into the host-authored record before review):

```json
{
  "coordination_mode": "host",
  "available": ["sol", "luna"],
  "minimum_role": "sol",
  "retain_for_host": false
}
```

Bind Sol and Luna to actual available model/effort pairs in the dispatch runtime.
No Astra runtime binding is required. If Sol is the coordinator, ordinary Sol
work stays local; Luna may handle bounded extraction or transformations. Another
host can dispatch a Sol worker. Explicit independent review can use a separate
Sol instance when warranted. There is no claim of independent model diversity
when two workers use the same model.

The existing `astra` classification label also represents complex architectural
work. It remains in Jev's frozen rubric to preserve historical comparability.
In host mode it is a complexity signal, not a request to run Astra. Such work
returns `review / complex_work_retained_by_host`, even if Astra appears in runtime
inventory. An `astra` minimum is retained before any classifier request. Do not
lower the floor merely because Astra is absent.

The current host may resolve the work itself, clarify the contract, or decompose
it into genuinely bounded pieces with new reviews. A host-review result is not
proof that the host has solved the task or is equivalent to Astra. Do not return
an unresolved task as complete. Sol failure returns to host review rather than
suggesting an unavailable or disabled Astra worker.

Host mode controls delegation. It cannot change the current conversation model;
if the host is already Astra, a fully Astra-free run must start with a different
host selected by the user. Do not claim to have switched the parent model.

## Astra mode

Set `coordination_mode: "astra"` when the user explicitly wants Astra advice.
Use the actual inventory; when Astra is absent, retain review rather than invent
availability or use a weaker tier under its name. The host still executes tools,
verifies evidence and owns final integration. Astra already hosting the task needs
no duplicate adviser unless independent review warrants one.

Omitting the field preserves old v2 Astra behavior for saved scripts and fixtures.
New tasks must state it explicitly. Invalid mode values fail closed. Changing mode
invalidates saved review/recommendation hashes; review the changed task afresh.

## Further improvements that need outcome evidence

The next useful experiment is a matched coding-task evaluation of host-only,
host+Sol/Luna, and optional-Astra workflows. Measure accepted task outcomes,
regressions, elapsed time, model usage, and available token/cost data on identical
fresh tasks. Keep infrastructure failures separate from capability failures.
Those results should determine effort defaults and when delegation pays off.
Until then, do not add automatic history-based downgrades or claim savings.
