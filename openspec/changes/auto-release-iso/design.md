# Design: Auto Release ISO Pipeline

## Technical Approach

Refactor `iso.yml` into a reusable ISO builder that delegates to `mql release iso` (single canonical builder, `lib/iso.sh:72-125`) and chains into the main CI pipeline via `workflow_call`. Add `publish-iso.yml` to mirror the `publish-rootfs.yml` pattern (validate -> sync to `rog.local` -> archive -> index). On push to `main`, `build-rpms-v2.yml` invokes the ISO workflow after a clean build (gated on `build-chain.sh` exit code); on tag `v*`, the ISO is additionally attached to a GitHub Release. Phase 2 installable-ISO work is captured as design only in `agent_docs/installer-design.md`.

## Architecture Decisions

### Decision: `iso.yml` refactor -- canonical builder + `workflow_call`

**Choice**: Refactor `iso.yml` to delegate to `mql release iso`; remove the inline dracut/squashfs/grub-mkrescue reimplementation (current lines 31-77); add `workflow_call`; keep `workflow_dispatch` + `push: tags v*`.

`workflow_call` inputs:

| Input | Type | Required | Default | Purpose |
|---|---|---|---|---|
| `version` | string | no | `26.4-YYYYMMDD` | ISO filename + Release title |
| `publish` | boolean | no | `false` | Call `publish-iso.yml` after build |
| `dry_run` | boolean | no | `false` | Build only, skip publish + Release |

Step sequence:

1. Environment gate -- same `MQL_ROOTFS` overlay + `rpmbuild` checks as `build-rpms-v2.yml` lines 58-130.
2. Verify ISO deps in base rootfs (`dracut`, `grub`, `libisoburn`, `squashfs-tools`, `mtools`, `busybox`, `dhcpcd`); fail fast listing missing set.
3. Run `mql release rootfs` (installs all `RPMS/x86_64/*.rpm` via `dnf install`, `lib/iso.sh:21-40`) then `mql release iso` (`lib/iso.sh:72-125`). Rootfs step guarantees base contains every spec built in this pipeline run before squashfs compression.
4. Rename `maquilinux-YYYYMMDD.iso` -> `maquilinux-${version}.iso`; generate `.sha256` + `.sha512`.
5. `actions/upload-artifact@v4` (90-day retention, same artifact name `iso`).
6. If `publish=true`: call `publish-iso.yml` via `uses:` with `iso_path`, `sha256_path`, `version`.
7. If trigger is `push: tags v*`: `softprops/action-gh-release@v1` attach ISO + checksums (existing wiring, lines 97-106).

**Alternatives**: New `iso-build.yml` from scratch (rejected: loses tag-trigger history and existing Release wiring). Keep inline iso.yml (rejected: divergent from `mql release iso`, two sources of truth).

**Rationale**: One canonical ISO builder. `workflow_call` keeps `build-rpms-v2.yml` lean; ISO is testable independently via `workflow_dispatch`.

### Decision: `publish-iso.yml` -- validate-then-publish

**Choice**: New workflow, callable via `workflow_call` from `iso.yml` publish mode or standalone `workflow_dispatch` with `iso_artifact_name`. Mirrors `publish-rootfs.yml` ordering.

Validation:

| Check | Threshold | Action on fail |
|---|---|---|
| File exists, non-empty | `stat` succeeds | Exit 1, list artifacts |
| Size sanity | > 500 MB (compressed rootfs floor) | Exit 1 |
| Internal structure | Loop-mount ISO; verify `/boot/vmlinuz`, `/boot/initramfs.img` (or `boot/`), `/LiveOS/rootfs.img` | Exit 1 listing contents |
| Checksum verify | Recompute sha256, compare to uploaded `.sha256` | Exit 1 on mismatch |

Sync steps (follow `publish-rootfs.yml` lines 158-219):

1. `ssh rog.local "mkdir -p .../maquiroot/iso/latest .../maquiroot/iso/history"`
2. `rsync -avz maquilinux-${version}.iso rog.local:.../iso/latest/maquilinux-latest.iso`
3. `rsync -avz` the `.sha256` to `iso/latest/maquilinux-latest.iso.sha256`
4. Archive: `ssh rog.local "cp .../iso/latest/maquilinux-latest.iso .../iso/history/maquilinux-${version}.iso"` (+ `.sha256`)
5. Verify remote size: `stat -c%s .../iso/latest/maquilinux-latest.iso` >= 500 MB
6. Update `index.json` via jq listing `iso/latest/*.iso`, `iso/history/*.iso`, `latest/*.tar.xz`

Additive rsync (no `--delete`) keeps history immutable -- same convention as rootfs publish line 331.

**Alternatives**: Inline publish step inside `iso.yml` (rejected: mixes concerns, harder to retry publish independently). Publish on tag only (rejected: `iso/latest/` should track main builds, not only releases).

**Rationale**: Validates ISO before exposing the public URL; isolated publish workflow can be retried without rebuilding the ISO.

### Decision: `build-rpms-v2.yml` ISO integration

**Choice**: Add a new job `iso-build` (not a step) to `build-rpms-v2.yml` using `needs: build` and `if:` gating, calling `iso.yml` via `uses:`.

```yaml
iso-build:
  needs: build
  if: github.event_name == 'push' && needs.build.outputs.chain_exit_code == '0'
  uses: ./.github/workflows/iso.yml
  with:
    version: ${{ needs.build.outputs.tag }}
    publish: true
```

`build` job already captures `chain_exit_code` at line 201 (`steps.build.outputs.chain_exit_code`); expose it as a job-level `outputs:`. Partial failure (any spec FAILED under `--continue-on-failure`) -> `chain_exit_code != 0` -> ISO skipped, reason in job summary. PRs never trigger ISO. `workflow_dispatch publish` mode also triggers it; `build-only` mode does not.

**Alternatives**: Inline ISO step (rejected: 360min timeout already, exploration C.1 con). Nightly cron (rejected: drifts from latest packages, exploration C.3 con). Auto-generate on every spec push regardless of failures (rejected: exploration E.5 option A is safest).

**Rationale**: ISO is a downstream artifact of a clean build; `chain_exit_code` is the single source of truth already tracked by build-chain.sh. Separate job keeps ISO timeout isolated from the build timeout.

### Decision: Installable ISO -- custom script for Phase 1

**Choice**: Document installer approach A (custom shell-script installer) for Phase 1; Phase 2 roadmap documented in `agent_docs/installer-design.md` only -- no implementation in this change.

Decision matrix:

| Option | GUI deps | Effort | Maintenance | Phase fit |
|---|---|---|---|---|
| A. Custom shell installer | None | Low | Low (Maqui-specific) | Phase 1 -- recommended |
| B. Calamares | Qt6 + X/Wayland | High | High (upstream deltas) | Phase 2+ |
| C. Anaconda-lite | Python + rpm-native | High | High (Fedora coupling) | Phase 3+ |

**Rationale**: Phase 1 ships a live ISO only (current `mql release iso` capability, exploration A). Option A is the smallest viable next step and avoids pulling Qt/X into the squashfs image -- keeps ISO inside the 600MB-1.2GB estimate. Phase 2 roadmap: design an `mql install` subcommand that partitions target disk, copies rootfs from squashfs via `tar`, installs GRUB, regenerates initramfs.

### Decision: Agent docs + pointer index

| File | Action | Content |
|---|---|---|
| `agent_docs/release-engineering.md` | Create | ISO + rootfs publish flow, URLs, trigger conditions, push-vs-read boundary (extends `agent_docs/backup-flow.md`) |
| `agent_docs/installer-design.md` | Create | Installer decision matrix, Phase 2 roadmap |
| `AGENTS.md` | Modify | Add 2 entries to pointer index; bump `agent-context-version` to "3"; add `iso/` paths + URLs to Key Paths / Key URLs |

### Decision: Public URL layout

```
maquiroot.glats.org/
  latest/
    maquilinux-rootfs-latest.tar.xz          (existing, publish-rootfs.yml)
  iso/
    latest/
      maquilinux-latest.iso
      maquilinux-latest.iso.sha256
    history/
      maquilinux-<version>.iso
      maquilinux-<version>.iso.sha256
```

Remote root: `/srv/glats/nginx/maquiroot/iso/` on rog.local (sibling of existing `latest/` and `history/` rootfs dirs). Only `.sha256` in public layout (matches rootfs convention); `.sha512` retained in GitHub artifact/Release only. Filename omits `-x86_64` per design decision; Phase 2 multiarch ISOs would switch to `maquilinux-latest-x86_64.iso` naming.

## Data Flow

```
push: SPECS/*.spec -> build-rpms-v2.yml
  -> build-chain.sh --json --continue-on-failure -> .ci-build-state.json
  -> acceptance-test.sh --json
  -> [chain_exit_code == 0?] -> iso.yml (workflow_call, publish=true)
       -> mql release rootfs  (dnf install all RPMs into chroot)
       -> mql release iso     (kernel + dracut + squashfs + grub-mkrescue)
       -> sha256/sha512
       -> upload-artifact
       -> publish-iso.yml (workflow_call)
            -> validate -> rsync rog.local:.../iso/latest -> archive history -> index.json
       -> [push: tag v*] -> GitHub Release attach
```

## File Changes

| File | Action | Description |
|---|---|---|
| `.github/workflows/iso.yml` | Modify | Delegate to `mql release iso`; add `workflow_call` inputs; remove inline dracut/squashfs/grub; add publish-mode call to `publish-iso.yml`; keep tag-trigger Release |
| `.github/workflows/build-rpms-v2.yml` | Modify | Add `iso-build` job gated on `chain_exit_code == '0'`; expose `chain_exit_code` + `tag` as job outputs |
| `.github/workflows/publish-iso.yml` | Create | Validate + rsync to rog.local `iso/latest` + archive `iso/history` + `index.json` |
| `agent_docs/release-engineering.md` | Create | ISO + rootfs publishing reference for agents |
| `agent_docs/installer-design.md` | Create | Installable ISO design, decision matrix, Phase 2 roadmap |
| `AGENTS.md` | Modify | Add 2 entries to pointer index; bump `agent-context-version` |
| `lib/iso.sh` | Verify | Confirm `mql release iso` runs end-to-end against fresh rootfs; fix issues found during integration |

## Interfaces / Contracts

### `iso.yml` `workflow_call` inputs

```yaml
inputs:
  version: { type: string,  required: false, default: '' }   # falls back to 26.4-YYYYMMDD
  publish: { type: boolean, required: false, default: false }
  dry_run: { type: boolean, required: false, default: false }
```

### `publish-iso.yml` `workflow_call` inputs

```yaml
inputs:
  iso_path:        { type: string,  required: true  }   # .iso path in caller workspace
  sha256_path:     { type: string,  required: true  }
  version:         { type: string,  required: true  }
  dry_run:         { type: boolean, required: false, default: false }
  skip_validation: { type: boolean, required: false, default: false }
```

### `build-rpms-v2.yml` `build` job outputs (new)

```yaml
outputs:
  chain_exit_code:
    description: "build-chain.sh exit code (0 = all specs passed)"
    value: ${{ steps.build.outputs.chain_exit_code }}
  tag:
    value: ${{ steps.list.outputs.tag }}
```

## Testing Strategy

| Layer | What | How |
|---|---|---|
| Unit | `mql release iso` reproduces ISO after `mql release rootfs` | Manual run on self-hosted runner; verify ISO boots in QEMU (`qemu-system-x86_64 -cdrom iso -m 2048 -boot d`) |
| Unit | `check_iso_deps` fails with explicit missing list (`lib/common.sh:126`) | Temporarily uninstall `squashfs-tools`; expect exit 1 with `Missing ISO dependencies: squashfs-tools` |
| Integration | `iso.yml` `workflow_call` from `build-rpms-v2.yml` on clean push | Push trivial spec change to main; verify ISO artifact + `rog.local` `iso/latest` updated |
| Integration | Partial failure skips ISO | Force build-chain.sh failure (broken spec); verify `iso-build` job skipped, summary cites `chain_exit_code != 0` |
| E2E | Tag push publishes to GitHub Release + maquiroot | `git tag v26.5 && git push --tags`; verify Release attached artifact, `iso/latest/maquilinux-latest.iso` served, sha256 matches |
| E2E | History archive immutable | Two consecutive publishes; verify `iso/latest/` overwritten but `iso/history/` retains both versions |

## Migration / Rollout

No data migration required. Rollback path:

1. Revert `iso.yml` / `build-rpms-v2.yml` / `publish-iso.yml` to prior commit -- ISO step is additive (gated job), `build-rpms-v2.yml` main build unaffected.
2. If `maquiroot.glats.org/iso/` publishing fails, GitHub artifact (90-day retention) and GitHub Release remain as fallback.
3. nginx `/iso/` location block on rog.local is additive (no rewrite needed); can be added before first publish without risk.

## Open Questions

- [ ] Should `publish-iso.yml` also PGP-sign the ISO on tag push? (Defer to separate change per proposal out-of-scope; needs key management.)
- [ ] Run `mql release rootfs` on every ISO build, or only when `build-rpms-v2.yml` already promoted via `mql chroot --promote`? (Recommendation: always run -- reproducibility over speed; install is ~10-30min, well within iso.yml timeout.)
- [ ] `index.json` schema: reuse rootfs index structure or new ISO-specific schema? (Recommendation: extend existing jq to include `iso/latest` and `iso/history` paths in same index file.)