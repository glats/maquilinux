---
name: maqui-distro-build
description: "Trigger: Maqui full distro build, build chain, resume package batch. Validate dependency order, shared state and per-package evidence."
license: Apache-2.0
metadata:
  author: "Maqui Linux contributors"
  version: "1.0"
---

## Activation Contract

Use for planning, executing or resuming a multi-package Maqui build. Use [package build](../maqui-package-build/SKILL.md) for each package; do not duplicate its workflow.

## Hard Rules

- Planning is read-only. Inspect the chain implementation before executing; a dry-run flag is not proof of zero side effects.
- Establish explicit dependency order from specs and target providers. Do not assume `--all` computes a topological order.
- Identify ownership of rootfs, state file, logs and repository output. Serialize shared mutations; separate worktrees alone are insufficient isolation.
- Do not enable `--heal` without explicit approval for its spec edits. Do not treat an installation fallback using `--nodeps` as validated dependency resolution.
- Keep signing, promotion, publication and destructive recovery outside this skill's authority.

## Decision Gates

| Condition | Action |
|---|---|
| Dependency cycle or missing provider | Stop affected builds; resolve the bootstrap contract |
| Resume or skip-built requested | Match saved state to specs, sources, architecture, rootfs and artifacts before reuse |
| Continue-on-failure or skipped tests | Report incomplete proof; do not promote aggregate success |
| Detached execution | Track terminal results; process/session creation is not completion |

## Execution Steps

1. Load the references. Define the selected package set, build order and expected artifacts; do not silently expand to every spec.
2. Inspect current option behavior, install fallbacks and state writes. Before launch, resolve any side effects outside authorization; a warning after execution cannot make them safe.
3. Confirm backup coverage and resource ownership through package-build. For authorized execution, retain per-package commands, logs, exit codes and artifact identities.
4. Reconcile chain state with observed results. Treat pending, building, failed, skipped or unverifiable entries as distinct from accepted packages; check dependent prerequisites before continuing.
5. Hand matching artifacts to package acceptance. Keep repository-candidate and image qualification separate from chain completion.

## Output Contract

Return selected order, target/state identity, per-package outcomes, blocked dependents and exact next safe step. State what evidence permits resumption; do not delete or reset saved state to hide failures.

## References

Read [local workflow references](references/docs.md).
