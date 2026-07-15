# Proposal: Auto Release ISO Pipeline

## Intent

Maqui Linux can build a live ISO (`mql release iso`) but it is completely decoupled from CI. The `iso.yml` workflow reimplements ISO creation inline and only triggers manually or on tags. No ISO is generated after successful builds, and no ISO is published to a public URL. This change automates ISO generation from CI and publishes artifacts to GitHub Releases and maquiroot.glats.org.

## Scope

### In Scope
- Refactor `iso.yml` to use `mql release iso` and add `workflow_call` trigger
- Add ISO step to `build-rpms-v2.yml`: on push to main, call iso-build workflow after clean build success
- New `publish-iso.yml` to sync ISO to maquiroot.glats.org/iso/ (validate-then-publish pattern from publish-rootfs.yml)
- GitHub artifact (every build) + GitHub Release attachment (on tag)
- Checksum generation (sha256 + sha512)
- ISO size and structure verification
- New `agent_docs/release-engineering.md` for agent reference
- Installable ISO design in `agent_docs/installer-design.md` (Phase 2 scope, implementation deferred)

### Out of Scope
- Calamares integration (separate change)
- QEMU boot test automation (separate change)
- PGP detached signatures (separate change)
- Installer implementation (design only in this change)

## Capabilities

### New Capabilities
- `iso-ci-automation`: Automated live ISO generation from CI pipeline, published to GitHub Releases and maquiroot.glats.org/iso/
- `release-engineering-docs`: Agent documentation for ISO and rootfs release workflows

### Modified Capabilities
None. No existing specs cover CI/ISO/release workflows.

## Approach

**Phase 1 (this change)**: Fix and automate live ISO.

1. Refactor `iso.yml` to delegate to `mql release iso` instead of inline reimplementing dracut, squashfs, and grub-mkrescue steps. Add `workflow_call` trigger accepting version and mode inputs.
2. Add conditional ISO step in `build-rpms-v2.yml`: after build+acceptance+sync, check `build-chain.sh` exit code. If zero (all specs passed), call `iso-build.yml` via `workflow_call`.
3. New `publish-iso.yml`: validate ISO size/structure, rsync to rog.local under `/srv/glats/nginx/maquiroot/iso/`, archive to history, update index. Pattern from `publish-rootfs.yml`.
4. GitHub artifact on every build (90-day retention); GitHub Release on tag pushes (softprops/action-gh-release).
5. Ensure `mql release rootfs` runs before `mql release iso` so base has all RPMs. Verify ISO deps (dracut, grub, libisoburn, squashfs-tools, mtools, busybox, dhcpcd) are installed in base rootfs.

**Phase 2 (design only)**: Document installable ISO approach in `agent_docs/installer-design.md`. Evaluate custom script vs calamares vs anaconda-lite. Implementation deferred.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `.github/workflows/iso.yml` | Refactor | Use `mql release iso`, add `workflow_call`, remove inline dracut/squashfs/grub steps |
| `.github/workflows/build-rpms-v2.yml` | Modified | Add ISO trigger job after clean build success |
| `.github/workflows/publish-iso.yml` | New | Validate + publish ISO to maquiroot.glats.org |
| `agent_docs/release-engineering.md` | New | ISO + rootfs release reference for agents |
| `agent_docs/installer-design.md` | New | Installable ISO design (Phase 2) |
| `lib/iso.sh` | Verify | May need fixes if `mql release iso` has issues |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| ISO deps missing from base rootfs (dracut, grub, etc.) | Medium | Check in CI before ISO build; fail early with clear message listing missing packages |
| `mql release iso` fails due to chroot state | Medium | Run `mql release rootfs` first to ensure all RPMs installed |
| ISO artifact exceeds GitHub size limits (2GB per artifact) | Low | Current estimate 600MB-1.2GB; under limit |
| build-rpms-v2.yml timeout (360min) insufficient with ISO added | Low | ISO build is separate workflow with own timeout; not in same job |

## Rollback Plan

1. Revert workflow files to previous commit if ISO step breaks main pipeline
2. ISO generation is additive (does not modify build pipeline), so build-rpms-v2.yml continues working without it
3. If maquiroot.glats.org publishing fails, GitHub artifact remains as fallback

## Dependencies

- ISO tools (dracut, grub, libisoburn, squashfs-tools, mtools) must be installed in base rootfs via their RPM specs
- SSH key + known_hosts for rog.local must exist on self-hosted runner (same as build-rpms-v2.yml sync step)
- Kernel config already has SQUASHFS, ISO9660, CDROM enabled (confirmed in exploration)

## Success Criteria

- [ ] ISO generated automatically on every successful push to main (no partial failures)
- [ ] `iso.yml` uses `mql release iso` -- no inline dracut/squashfs/grub reimplementation
- [ ] ISO published as GitHub artifact every build; GitHub Release on tag
- [ ] ISO published to maquiroot.glats.org/iso/ (latest + history + checksums)
- [ ] Partial build failure (any spec fails) skips ISO generation
- [ ] Installable ISO design documented in agent_docs/installer-design.md
- [ ] Release engineering docs created for agent reference
