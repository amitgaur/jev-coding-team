# Coding-router comparison and adopted changes — 2026-10-04

Inspected the public skill documentation and advisor/policy implementation of
[capitalparser/codex-model-router](https://github.com/capitalparser/codex-model-router/tree/3b7859a17cc5ea640f9967221600db9e3a578433),
and the skill/documentation of
[orange-the-weak/codex-auto-model-router](https://github.com/orange-the-weak/codex-auto-model-router/tree/694402bb81355cb2c3d663b8bc5c7d6da4f31a2e).
These are reference implementations, not dependencies. No upstream code was copied
or installed. The model families and execution APIs in those projects differ from
this skill's current runtime.

The first separates recommendations from execution, supplies bounded worker
contracts and records verified outcomes for escalation. The second explicitly
weighs delegation overhead and distinguishes direct coordinator execution from
model-specific workers. These are useful design patterns, not independent proof
of better coding outcomes.

Adopted in our independently implemented `scripts/dispatch.py`:

- Explicit runtime model/effort binding and observed execution identity.
- Current workspace and exact writable paths carried into worker plans.
- A verification method for every acceptance criterion, with complete receipts.
- Host handling when no slot, supported binding or delegation benefit exists.
- Capability-failure escalation suggestions within the existing two-attempt cap.

Retained our host-reviewed source projection, minimum roles, one-task Jev calls,
stale-recommendation checks, TypeSafe provider and pinned Jev source. Phase controls
worker scope rather than determining difficulty. Jev requests/rubric and frozen
benchmark results are unchanged.

We did not adopt automatic history-based downgrades or a shell-based alternate
executor. There is no outcome evidence yet to justify learned tier selection in
our model pool. Local receipts support future measurement without implying that
they authenticate their own contents.

Luna's independent forward tests found an initially permissive review flag and
missing acceptance-to-check coverage. Both were repaired before final validation.
See dispatch.md for trust assumptions: the host must establish semantic adequacy,
actual model use, resolved file scope and test results. This package remains
experimental; offline invariants are not a coding benchmark.
