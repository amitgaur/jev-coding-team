# Jev Coding Team

A Codex skill for routing bounded coding and research tasks to Sol or Luna,
with **optional Astra advice**. The current host coordinates the work and verifies
results. Jev recommends a role; it does not grant permissions or execute agents.

**Experimental release v2.2.** Offline checks pass, but coding-quality improvements
and cost savings have not been demonstrated. The original routing evaluation did
not meet its publication targets. This repository publishes the experiment and
its limitations, not a benchmark-winning router.

## Install

Ask Codex:

> Install the skill from https://github.com/amitgaur/jev-coding-team/tree/main/skills/astra-jev-team

Or clone and run the local installer (Python 3.9+ for this installer and offline helpers):

```sh
git clone https://github.com/amitgaur/jev-coding-team.git
cd jev-coding-team
python3 tools/install.py
```

The installer copies only the skill into `$CODEX_HOME/skills` (default
`~/.codex/skills`). It does not modify your global configuration, install Jev,
store credentials, or call an API. Existing installations are left intact unless
you explicitly use `--upgrade`, which first creates a backup. The skill is
available on your next Codex turn. Its stable invocation is `$astra-jev-team`;
the display name is **Jev Coding Team**.

## Use it

**Without Astra:**

> Use $astra-jev-team without Astra. Fix this parser bug, delegate bounded work
> to available Sol/Luna workers, and verify every acceptance criterion.

**With Astra:**

> Use $astra-jev-team with Astra advice for the architecture, Sol for scoped
> implementation, and Luna for mechanical analysis. Verify the integrated result.

Model names are resolved from your runtime. You need access to the requested
models and native subagent tools; installing the skill does not provide model
access or change your current conversation's model. A Sol host can coordinate
without any Astra worker. Difficult work stays with the host for review rather
than being silently downgraded.

## Jev setup and credentials

Live classification uses **official TypeSafe**, model `jev-1.13.0`, via the
`jev-decide` CLI at `~/.local/bin/jev-decide`. Install the companion Jev skill/CLI
using [the pinned upstream setup instructions](https://github.com/wuyoscar/jev-skill/blob/01bd9403bcaac92e037869843ec83ad8a75c3ec2/skills/jev/references/setup.md).
The separate Jev CLI requires Python 3.10+; its own installed environment may
provide that independently of your system Python. The tested CLI package version is 0.2.1. Preserve that source pin unless you
explicitly choose and validate an update.

Supply `TYPESAFE_API_KEY` through the environment that launches Codex or the
classifier. Obtain it privately from [TypeSafe](https://console.typesafe.ai).
Do not paste it into chat, source files, task JSON, screenshots, or Git commits.
This project never needs your key committed or copied into its configuration.

```sh
python3 skills/astra-jev-team/scripts/doctor.py
```

The doctor checks local dependency/key **presence only**; it never prints a key
or makes a network request. Offline tests need no credentials. Live routing sends
reviewed task summaries to TypeSafe and incurs charges, so authorize that use
and sharing before running it. No simulation or alternate provider is used on
failure. Runtime request/response files may contain private task content; keep
them outside the repository or in its ignored `runs/` directory.

## How routing works

1. The host reviews the task and chooses explicit host or Astra coordination.
2. Permissions, evidence, model availability and minimum-role gates run locally.
3. Jev receives one reviewed brief per request, after CLI dry-run validation.
4. The host rechecks the recommendation and prepares an explicit worker contract.
5. Worker results are accepted only after host inspection of scope and checks.

Worker plans pin model, effort, workspace, writable files and verification
coverage. The helper does not spawn agents itself. Host-attested receipts and
hashes are consistency checks, not authentication or proof that tests ran.

For low-level use, see [routing](skills/astra-jev-team/references/routing.md),
[dispatch](skills/astra-jev-team/references/dispatch.md), and
[coordination modes](skills/astra-jev-team/references/coordination.md).

## Evaluation

```sh
python3 -m unittest discover -s skills/astra-jev-team/scripts -p 'test_*.py'
python3 -m unittest discover -s skills/astra-jev-team/evals -p 'test_*_forward.py'
```

At v2.2: 65 automated routing/dispatch tests and 19 independent Luna-authored
forward scenarios pass. These test workflow invariants; they are not live coding
outcome benchmarks. Public benchmark adapters and synthetic gold fixtures are
included. Third-party benchmark datasets, credentials, and private run logs are not.

Historical synthetic held-out effective routing accuracy was 25/32 (78.1%), with
one critical underdelegation. Removing an injected sentence did not fix the
original batched error; singleton probes passed. Host controls and isolated
requests mitigate integration risks without proving prompt-injection immunity.

Read [all results and limitations](skills/astra-jev-team/references/results.md)
and [public benchmark protocol](skills/astra-jev-team/references/public-benchmarks.md).
The next step is a fresh matched coding-outcome comparison, including delegation
overhead and actual usage. Do not tune a router on RouterArena evaluation data.

## Contributing

Keep gold labels out of classifier inputs, preserve old failures, and add behavior
checks for changes. Never submit real task logs or secrets. Model and provider
changes require explicit documentation and new validation. See
[the design comparison](skills/astra-jev-team/references/router-comparison.md)
for upstream inspiration and pins. Our implementation is independent; Jev is an
external dependency with its own license and service terms.

## License

MIT for this repository's code, documentation and original synthetic fixtures.
Third-party datasets are not redistributed and retain their own terms.
