# Tasks: Auto Release ISO Pipeline

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~385 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Medium

## Phase 1: ISO Automation

- [x] 1.1 **Refactor `.github/workflows/iso.yml` to use `mql release iso`** -- replace inline dracut/squashfs/grub-mkrescue steps (lines 31-77) with `mql release rootfs` + `mql release iso` calls; add ISO dep verification step (dracut, grub, libisoburn, squashfs-tools, mtools); generate sha256 + sha512 checksums; keep existing `upload-artifact` and `softprops/action-gh-release` steps.
- [x] 1.2 **Add `workflow_call` trigger to `.github/workflows/iso.yml`** -- add `on.workflow_call.inputs` block with `version` (string, optional, default `26.4-YYYYMMDD`), `publish` (boolean, optional, default false), `dry_run` (boolean, optional, default false); call `publish-iso.yml` via `uses:` when `publish=true`.
- [x] 1.3 **Create `.github/workflows/publish-iso.yml`** -- new workflow with `workflow_call` inputs: `version`, `dry_run`, `skip_validation`; validate ISO size (>500MB), checksum match; download ISO artifact; rsync to `rog.local:/srv/glats/nginx/maquiroot/iso/latest/`; archive to `iso/history/`; update `index.json`. Pattern from `publish-rootfs.yml`.
- [x] 1.4 **Add ISO trigger job to `.github/workflows/build-rpms-v2.yml`** -- expose `chain_exit_code` and `tag` as `build` job `outputs:`; add new `iso-build` job (`needs: build`, `if: chain_exit_code == '0'`) calling `.github/workflows/iso.yml` via `uses:` with `version`, `publish`, and `caller_run_id`.
- [x] 1.5 **Verify `lib/iso.sh` end-to-end on self-hosted runner** -- found blocking issue: `mql_release_rootfs` hardcoded `/mnt/workspace/` path incompatible with reusable workflow artifact restore. Fixed to `/mnt/repo/x86_64/` which is always available via bind mount.
- [x] 1.6 **Create `agent_docs/release-engineering.md`** -- document full release pipeline: build, acceptance, ISO generation, checksum, publish to maquiroot.glats.org (iso/latest/, iso/history/) and GitHub Release; reference CI workflow files; URL list (repo, rootfs, iso); push-vs-read boundary.
- [x] 1.7 **Create `agent_docs/installer-design.md`** -- evaluate installer approaches (custom script, Calamares, Anaconda-lite) with tradeoff matrix; define minimal viable installer feature set; list RPM spec dependencies for each approach; flag Phase 2 deferred implementation.

## Phase 2: Agent Documentation Index

- [x] 2.1 **Update `AGENTS.md`** -- add `agent_docs/release-engineering.md` and `agent_docs/installer-design.md` to Agent Documentation Index table; add ISO URLs to Key URLs; bump `agent-context-version` to `"3"`.
