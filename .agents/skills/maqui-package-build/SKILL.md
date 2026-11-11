---
name: maqui-package-build
description: "Trigger: build Maqui RPM, resolve BuildRequires, prepare multiarch build. Connect inputs, dependencies and isolated build evidence."
license: Apache-2.0
metadata:
  author: "Maqui Linux contributors"
  version: "1.0"
---

## Activation Contract

Use for a Maqui package build or build plan. Planning remains read-only; a request to inspect dependencies does not authorize installation or building.

## Hard Rules

- Read the local build, dependency and backup references. Keep specs authoritative and execute builds only in the overlay chroot.
- Identify the active rootfs, shared resources and permitted mutations. Separate worktrees do not isolate rootfs state.
- Verify source inputs and dependency providers for the selected architecture; never disable dependency or signature checks to force progress.
- Preserve backups and failure evidence. Restore, reset, promotion, credentials and publication require their own authorization.

## Decision Gates

| Prerequisite | Action |
|---|---|
| Sources missing | Resolve declared inputs; fetch only within authorized network/write scope |
| Dependency missing | Map installed providers, matching RPMs and existing specs before expanding work |
| New package or bootstrap cycle | Report the missing contract; do not silently invent a bootstrap sequence |
| Multiarch requested | Verify both dependency sets and spec support; x86_64 success is not i686 proof |
| Shared mutable rootfs | Serialize work or obtain an isolated target before building |

## Execution Steps

1. Record target spec, version/release, architectures and actual configuration. Load [spec gates](../maqui-spec-gates/SKILL.md) for static checks.
2. Resolve the dependency order and source availability. Distinguish repository availability from installation in the target rootfs.
3. Establish the documented pre-build backup before authorized mutations. Check which layer it captures; do not assume a base snapshot preserves overlay changes.
4. Run the selected `./mql build <spec>` form, using `--both` only when intended. Record exit code, logs and produced artifact identities.
5. On failure, stop dependent steps and use [chroot diagnosis](../maqui-chroot-debug/SKILL.md). On success, report artifacts; installation and [acceptance](../maqui-acceptance-verify/SKILL.md) remain distinct authorized steps.

## Output Contract

Return dependency order, missing inputs, target/backup identity, executed commands and results, artifact paths and pending acceptance. Never equate build completion with signed installation or release readiness.

## References

Read [local workflow references](references/docs.md).
