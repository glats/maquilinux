---
name: maqui-acceptance-verify
description: "Trigger: Maqui post-build checks, RPM acceptance, package runtime verification. Separate package proof from VM and release proof."
license: Apache-2.0
metadata:
  author: "Maqui Linux contributors"
  version: "1.1"
---

## Activation Contract

Use to verify a selected Maqui package after building or installation. Do not install packages merely because verification was requested.

## Hard Rules

- Read acceptance criteria and identify package, version, architecture and target rootfs before checking.
- Execute target checks inside the authorized chroot, never against the host RPM database or host library paths.
- Obtain authorization before installation or other state changes; do not bypass signature checks.
- Treat chroot acceptance, signed-install E2E, VM boot and release qualification as distinct evidence.
- Do not infer boot or networking from launching QEMU, or serving the intended repository from HTTP 200 alone. Require guest observations and expected endpoint content for those claims.

## Decision Gates

| Condition | Action |
|---|---|
| Package not installed | Report missing prerequisite; do not claim runtime acceptance |
| No executable or shared library | Mark that check not applicable with payload evidence |
| Both architectures requested | Check both target library layouts |
| Unknown or untrusted executable | Stop execution and request a safe verification environment |
| Signed-install proof requested | Identify key bootstrap and consumer verification; local bypass paths do not prove authenticated installation |

## Execution Steps

1. Load the acceptance reference and inspect the selected artifact's expected payload.
2. Run applicable package registration, integrity, executable and linkage checks in the intended environment. Use concrete paths, not blindly copied placeholders.
3. Check architecture-specific files inside that same target; record version and architecture for every result.
4. Report failures and missing prerequisites without promoting, publishing or changing the accepted scope. Do not remove bootstrap/local bypasses indiscriminately; map their consumers and authorization boundaries before proposing a separate correction.

## Output Contract

Return package/target identity and per-check command, exit code, result and evidence. Distinguish pass, fail, not applicable and not run. Tie reused evidence to its artifact and environment. State explicitly which VM, trust or publication claims remain unverified.

## References

Read [local workflow references](references/docs.md).
