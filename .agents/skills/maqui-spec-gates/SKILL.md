---
name: maqui-spec-gates
description: "Trigger: Maqui RPM spec changes, package lint, multiarch packaging. Select gates and report observed evidence."
license: Apache-2.0
metadata:
  author: "Maqui Linux contributors"
  version: "1.1"
---

## Activation Contract

Use when editing or checking Maqui RPM specs. Keep the existing orchestration route; this skill does not require delegation.

## Hard Rules

- Treat specs as package-definition authority; load conventions and relevant multiarch/dependency references.
- Build only inside the overlay chroot when building is authorized. Lint success does not prove build or runtime acceptance.
- Keep promotion, publication, credential access and Git delivery outside this skill's authority.
- Preserve command output and exit codes; unavailable tools are missing proof, not passes.
- Separate validated signed-candidate production from stable-promotion eligibility. A successful build or signing step alone does not authorize promotion.

## Decision Gates

| Changed surface | Required evidence |
|---|---|
| Spec | Scoped spec lint |
| Source or repository URL | Scoped endpoint lint; report network limitations |
| Built RPM payload | FHS lint on the selected artifacts |
| Architecture conditionals | Verify intended architecture outputs; do not infer i686 from x86_64 |
| Pipeline success claimed | Inspect failure propagation; warnings and unconditional publication steps are not acceptance gates |

## Execution Steps

1. Identify changed specs, intended architectures and affected dependency edges.
2. Run `./mql lint spec <spec>` and applicable `./mql lint endpoints <files>` checks using actual paths.
3. Match built RPMs to the intended spec version, release and architecture before running `./mql lint fhs <rpm>`; otherwise mark payload verification pending. Do not substitute a stale artifact's result.
4. Report failures before proposing changes. For authorized corrections, rerun affected checks and preserve surrounding behavior.

## Output Contract

Return each command, exit code, observed result and artifact identity where relevant. Separate static lint, build evidence and runtime acceptance; name skipped gates and their reason.

## References

Read [local workflow references](references/docs.md).
