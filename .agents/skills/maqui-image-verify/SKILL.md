---
name: maqui-image-verify
description: "Trigger: Maqui rootfs or ISO verification, VM boot acceptance. Separate artifact integrity, guest behavior and release eligibility."
license: Apache-2.0
metadata:
  author: "Maqui Linux contributors"
  version: "1.0"
---

## Activation Contract

Use to plan or verify rootfs/ISO artifacts and VM behavior. Use [package acceptance](../maqui-acceptance-verify/SKILL.md) for package checks; image verification does not authorize image creation or publication.

## Hard Rules

- Establish intended architecture, firmware, artifact and persistence boundary from the selected delivery contract. Ask only for consequential unresolved choices; do not invent a support matrix.
- Record the exact image path and digest. Verify the launcher's selected image; a filename sorted as latest is not proof of artifact freshness.
- Require authorization and isolated disposable state for VM execution. Never attach host disks or overwrite an existing installation as an implicit verification step.
- Keep checksum integrity, authenticated provenance, bootability, networking and persistent installation as separate claims.
- Do not invoke rootfs/ISO assembly to answer a verification-only request. Do not publish or access signing credentials.

## Decision Gates

| Available evidence | Permitted conclusion |
|---|---|
| File exists or checksum matches | Artifact presence/integrity only, not trusted provenance or boot |
| QEMU starts or chroot smoke passes | Launcher/chroot evidence only, not guest acceptance |
| Guest reaches expected console | Boot evidence for that image and selected VM configuration |
| Network or persistence untested | Mark pending; do not infer from boot success |

## Execution Steps

1. Load the references and delivery criteria. Identify the artifact, source/build evidence and intended target without copying transient roadmap state into this skill.
2. Check available integrity and structure evidence. Report missing artifact or tooling; do not regenerate anything silently.
3. For authorized guest tests, define bounded timeouts and expected observations before launch. Capture guest console or equivalent evidence tied to the image and VM configuration.
4. Test requested guest networking, package installation or persistence separately, only within scope. A host HTTP response does not prove guest connectivity; a checksum alone does not prove signature trust.
5. Report missing harness capabilities rather than treating interactive launch as an automated passing test. Leave publication and wider hardware/container qualification pending unless separately verified.

## Output Contract

Return artifact identity, VM configuration, checks/results, bounded logs and unverified claims. Distinguish pass, fail, not applicable and not run; never generalize one VM result to bare metal or all supported targets.

## References

Read [local workflow references](references/docs.md).
