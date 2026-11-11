---
name: maqui-chroot-debug
description: "Trigger: Maqui chroot failure, stale overlay, missing build dependency. Diagnose before proposing recovery."
license: Apache-2.0
metadata:
  author: "Maqui Linux contributors"
  version: "1.1"
---

## Activation Contract

Use for Maqui overlay, mount, source or dependency failures. Do not use as permission to repair an environment.

## Hard Rules

- Load the relevant local references before diagnosing.
- Preserve existing overlays and evidence. Reset, unmount, promotion and deletion require explicit authorization; never substitute manual commands for interactive confirmation.
- Identify the active rootfs and its owner before any mutation. Git worktrees do not isolate shared chroots.
- Serialize mutations when overlays, package databases or repository destinations are shared; a task dependency graph alone does not prove safe parallel execution.
- Never disable signature verification to make a failure disappear.

## Decision Gates

| Observation | Next action |
|---|---|
| Rootfs or ownership unknown | Inspect configuration; stop mutations |
| Missing source or dependency | Compare spec requirements with available inputs |
| Stale mount suspected | Collect mount evidence; propose bounded recovery |
| Signature failure | Investigate trust and artifact provenance separately |

## Execution Steps

1. Record the failing command, exit code and bounded error output without secrets.
2. Inspect `./mql config` and the matching troubleshooting section; do not enter a chroot merely to inspect host configuration.
3. Distinguish observed causes from hypotheses. Reuse prior evidence only when its rootfs, artifact and configuration still match; rerun missing or invalidated checks, not the entire investigation by default.
4. Propose the smallest recovery with affected resources and expected evidence. Execute only within actual authorization, then repeat the original check. Historical troubleshooting examples do not override current authorization or trust requirements.

## Output Contract

Return observed cause or uncertainty, evidence, proposed/executed recovery, remaining risks and verification result. Never label an unexecuted recovery successful.

## References

Read [local workflow references](references/docs.md).
