# Coding worker plans and verification

Use `scripts/dispatch.py` after routing a bounded coding task. It creates an
advisory spawn contract and validates host-observed outcome receipts. It neither
spawns agents nor runs checks, authenticates observations, or changes permissions.

## Prepare the contract before routing

Add `host.dispatch` before setting the review digest. Changing scope or checks
later invalidates the route, as any host-control change does:

```json
{
  "phase": "implement",
  "owned_paths": ["src/parser.py", "tests/test_parser.py"],
  "deliverable": "Parser correction and regression test",
  "checks": [
    {"id": "empty-input", "acceptance_index": 0, "method": "Run parser regression tests"}
  ],
  "independent_review": false
}
```

Phases: explore, plan, implement, test, review. Phase describes execution shape;
it does not select a model. A difficult test investigation can require Astra;
a mechanical inventory can use Luna. Every `task.acceptance` entry needs at least
one check referring to its zero-based index. The planner derives criterion text
from the original acceptance list. The host must verify that each method actually
establishes its criterion; coverage alone cannot establish semantic adequacy.

Paths are exact files relative to the existing workspace, without globs or parent
traversal. An empty list means read-only; explore, plan and review require it.
Before delegation, inspect resolved paths for symlink escapes and compare them
with current ownership and pending writes. The helper validates strings, not the
filesystem. Include created, deleted, renamed and untracked paths in later diff
verification; do not rely on the worker's claimed changed-file list.

## Observe runtime and plan

Provide a separate trusted runtime object based on actual tool/model inventory:

```json
{
  "workspace_root": "/absolute/path/to/current/workspace",
  "coordinator_model": "gpt-6-astra",
  "bindings": {"sol": {"model": "gpt-6.1-sol", "effort": "medium"}},
  "catalog": {"gpt-6.1-sol": ["low", "medium", "high"]},
  "native_delegation": true,
  "free_slots": 1,
  "benefit_justified": true
}
```

These model names and effort levels are examples; use the current runtime and
explicit user choices. Supply bindings for roles needed by this task. The host
chooses the lowest effort it can justify from reasoning depth and verification;
do not interpret effort as measured cost. `benefit_justified` means a bounded
independent reasoning task warrants context-transfer and integration overhead.
For small work, use the host and parallelize independent tool reads where useful.

```
python3 <skill>/scripts/dispatch.py plan --task task.json --recommendation recommendation.json --runtime runtime.json
```

The recommendation file is one route entry from routes.json. The task file is
one task object. A `host` result keeps work with the coordinator; it never claims
that the coordinator changed model or that a blocked task is ready to execute.
Resolve the stated blocker first where necessary. In host coordination mode, an Astra complexity signal stays with the host for
review and never produces an Astra worker. In Astra mode, an Astra route stays
local when the coordinator is Astra; otherwise it can produce an Astra adviser plan.
`independent_review: true` permits a separate reviewer using the same model as
the coordinator when actual independent review is warranted.

A `worker` plan pins model, effort, fresh context, workspace, scope and checks.
Refresh runtime and regenerate immediately before calling `collaboration.spawn_agent`;
choose a short task_name and pass the returned spawn fields. This is an instruction
to the host, not an automatic executor. No alternate shell executor is installed.
Raw evidence in the worker brief is labeled untrusted; worker prompt injection
remains a risk the host must contain through authority limits and verification.

## Verify actual execution

Save plans and receipts in a repository-local ignored run directory. Never place
private runtime history in the distributable skill. After inspecting the actual
agent identity, full diff and check outputs, author a receipt:

```json
{
  "plan_sha256": "copy-from-plan",
  "host_verified": true,
  "workspace_root": "/absolute/path/to/current/workspace",
  "start_snapshot": "snapshot-from-plan",
  "end_snapshot": "observed-revision-and-working-tree-digest-after-verification",
  "agent_id": "actual-runtime-agent-id",
  "actual_model": "gpt-6.1-sol",
  "actual_effort": "medium",
  "changed_paths": ["src/parser.py", "tests/test_parser.py"],
  "checks": [
    {"id": "empty-input", "passed": true, "exit_code": 0, "evidence": "Reference to saved command output and regression result"}
  ],
  "unresolved_risks": []
}
```

```
python3 <skill>/scripts/dispatch.py assess --plan plan.json --receipt receipt.json
```

Every planned check needs exactly one receipt. Exit codes are optional for manual
checks; include them for commands. A zero exit code alone is not proof a test
covered the requirement. Missing evidence, scope violations, model/effort mismatch
or unresolved risks require review. Unknown actual model/effort cannot be recorded
as a verified routed success. The helper trusts host observations; a forged receipt
can lie. Neither the plan hash nor `host_verified` authenticates its author.

On failed checks, set failure_type to capability only when host inspection shows
the worker could not solve a sufficiently specified, runnable task. Infrastructure,
permissions and requirements failures stay with the host for resolution. A first
capability failure may suggest Luna → available Sol. Sol failures return to the
host in host mode; Astra mode may suggest an available Astra tier; it does not dispatch or
promote a saved recommendation. Update attempt_count, attach failure evidence,
revise the brief/floor and review again. A second failed attempt stops escalation.
Historical success never overrides a role floor or automatically downgrades work.

See [router-comparison.md](router-comparison.md) for pinned upstream references
and the rationale for this update.
