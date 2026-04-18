# AGENTS.md -- Maqui Linux

## Project

Maqui Linux is an independent Linux distribution based on Linux From
Scratch. It uses RPM + DNF5 as the package manager and OpenRC as the
init system. The architecture is x86_64 with i686 multilib.

## Configuration

`mql` uses a two-file config system:

| File | Purpose | In git? |
| ---- | ------- | ------- |
| `mql.conf` | Project defaults (committed) | Yes |
| `mql.local` | User overrides (gitignored) | No |

Environment variables override both files. Key variable:

```bash
# If your disk is auto-mounted at a different path:
echo "MQL_LFS=/run/media/glats/maquilinux" >> mql.local
# Or per-session:
export MQL_LFS=/run/media/glats/maquilinux
```

Show active config: `mql config`

## Key Paths

| Path | What |
| ---- | ---- |
| `SPECS/` | 109+ RPM spec files |
| `SOURCES/` | Source tarballs and patches |
| `RPMS/` | Built RPMs (gitignored) |
| `scripts/` | Build scripts (`build-spec.sh`, `install-spec.sh`, `mlfs-runner.sh`) |
| `tools/` | Maintenance tools (`create-clean-rootfs.sh`, `verify-independence.sh`) |
| `lib/` | `mql` CLI library functions (bash) |
| `release/` | ISO configs, dracut, branding |
| `mql.conf` | Default configuration (MQL_LFS, MQL_DISK, MQL_RELEASEVER, etc.) |
| `mql.local` | User overrides (gitignored, create as needed) |
| `flake.nix` | Nix development shell (optional, provides all tools) |
| `$MQL_LFS/base/` | Immutable rootfs (overlay lower layer, default: `/mnt/maquilinux/base/`) |
| `$MQL_LFS/merged/` | Overlay chroot target |
| `$MQL_LFS/repo/` | Local RPM repo (bind-mounted in chroot as `/mnt/repo`) |
| `/srv/glats/nginx/repo/` | Production repo served at `repo.glats.org` |

## Working with the Rootfs

- The disk is mounted at `$MQL_LFS` (default: `/mnt/maquilinux`, configurable).
- Files in the rootfs are at `$MQL_LFS/merged/...` (overlay active)
  or `$MQL_LFS/base/...` (overlay not mounted).
- To run commands inside the chroot: `sudo mql chroot --exec "<cmd>"`
- Or manually: `sudo chroot $MQL_LFS/merged <cmd>`
- The chroot has its own GCC 15.2, Python 3.14, rpmbuild, dnf5.

## Spec Conventions

- Gen3 template: see `SPECS/SPEC_TEMPLATE.md`.
- Release tag: `1.m264` (m264 = maquilinux 26.4).
- Debug packages disabled in all specs.
- Multiarch: `%if "%{_target_cpu}" == "i686"` conditionals.
- Library dirs: `/usr/lib/x86_64-linux-gnu/` (64-bit),
  `/usr/lib/i386-linux-gnu/` (32-bit).

## `mql` CLI Quick Reference

**With Nix (recommended):**
```bash
nix develop                      # Enter Nix dev shell
# Inside nix shell:
mql chroot                       Enter overlay chroot
```

**Without Nix (standalone):**
See `docs/MANUAL-STANDALONE.md` for tool installation per distro.
All `mql` commands work the same after prerequisites are installed.

**Common commands (both):**
```
mql chroot                       Enter overlay chroot
mql chroot --exec "<cmd>"        Run command in chroot
mql chroot --reset               Discard overlay changes
mql chroot --persist <name>      Save snapshot
mql chroot --promote             Merge overlay into base
mql build <spec>                 Build RPM
mql build <spec> --both          Build 64+32 bit
mql install <spec>               Install RPM in chroot
mql backup create [tag]          Create rootfs backup (museum style)
mql backup list                  List all backups with metadata
mql backup restore <name>        Restore from backup
mql repo update                  Regenerate repo metadata
mql repo sync                    Publish to repo.glats.org
mql release rootfs               Generate rootfs from RPMs
mql release tarball              Package rootfs as .tar.xz
mql release iso                  Generate bootable live ISO
  mql test vm                    Boot in QEMU
  mql test smoke                 Run smoke tests
```

## Self-Hosting: Critical Packages

These 7 packages enable Maqui Linux to build itself and generate releases:

| Spec | Purpose | For |
| ---- | ------- | --- |
| `dracut.spec` | Initramfs generation (dracut-ng 110) | Live ISO boot |
| `busybox.spec` | Static binaries | Initramfs support |
| `dhcpcd.spec` | DHCP client | Live networking |
| `createrepo_c.spec` | Repo metadata | Publishing RPMs |
| `libisoburn.spec` | ISO creation (xorriso) | Generating ISOs |
| `squashfs-tools.spec` | Rootfs compression | Live ISO squashfs |
| `mtools.spec` | EFI image creation | UEFI boot support |

**Status:** ✅ All packages built and installed in base rootfs (2026-04-02)

## CI/CD and Operations

| Topic | Document | Key Points |
|--------|----------|------------|
| Self-hosted runner | `docs/agents/runner-setup.md` | NixOS or standalone Linux, any machine |
| Rootfs backups | `docs/agents/backup-system.md` | Museum style, never delete, archive to cold storage |
| Standalone developer | `docs/agents/standalone-developer.md` | Download rootfs, work locally, push optional |
| Key workflows | `bootstrap-rust.yml` (6hr timeout), `build.yml` (5-30 min) | Automatic backup before risky builds |

Quick reference (adapt `<your-runner-host>` to your setup):
```bash
# === NixOS Way (recommended) ===
# Start/restart runner
ssh <your-runner-host> "cd ~/Work/maquilinux && \
  tmux kill-session -t github-runner 2>/dev/null; sleep 1; \
  tmux new-session -d -s github-runner 'nix run .#runner'"

# Check runner environment
ssh <your-runner-host> "cd ~/Work/maquilinux && nix run .#runner-status"

# === Standalone Way (any Linux) ===
# See docs/agents/runner-setup.md for dependencies per distro
ssh <your-runner-host> "tmux kill-session -t github-runner 2>/dev/null; sleep 1; \
  tmux new-session -d -s github-runner '~/bin/Runner.Listener run'"

# === Common operations ===
# Create backup
ssh <your-runner-host> "cd ~/Work/maquilinux && ./mql backup create pre-<tag>"

# View runner logs
ssh <your-runner-host> "tmux capture-pane -t github-runner -p | tail -20"

# Check runner status from GitHub
gh api repos/glats/maquilinux/actions/runners | \
  jq -r '.runners[] | "\(.name): \(.status)"'
```

## Documentation Index

| Document | Covers |
| -------- | ------ |
| `docs/DEVELOPMENT-SYSTEM-PLAN.md` | Full architecture, overlay system, CLI design, build pipeline, dracut-ng/initramfs, ISO pipeline, repo structure, implementation phases, self-hosting roadmap, rootfs lifecycle |
| `docs/MANUAL-NIX.md` | Developer manual for NixOS/Nix users: `nix develop`, disk setup, daily workflow, building, repo management, testing, releases, NixOS host config, troubleshooting |
| `docs/MANUAL-STANDALONE.md` | Developer manual without Nix: tool installation per distro, manual chroot procedure, self-hosting setup, same workflow/build/release sections |
| `docs/agents/runner-setup.md` | Self-hosted GitHub Actions runner: NixOS or any Linux, configuration, troubleshooting |
| `docs/agents/backup-system.md` | Rootfs backup strategy: museum style, incremental backups, cold storage, restoration |
| `docs/agents/standalone-developer.md` | Download pre-built rootfs from maquiroot.glats.org, local development without runner, push optional |
| `docs/DEVELOPMENT.md` | Contribution workflow, CODEOWNERS, branch protection, CI/CD overview |
| `docs/PIPELINES.md` | GitHub Actions and GitLab CI pipeline details |
| `docs/DECISION-FRAMEWORK.md` | Mandatory research and presentation process before any tool/library decision |
| `docs/DECISIONS.md` | Log of all tool and architecture decisions with rationale and alternatives |
| `docs/GETTING-STARTED.md` | New developer onboarding: prerequisites, first build, daily workflow, troubleshooting |
| `SPECS/SPEC_TEMPLATE.md` | Gen3 spec template and authoring guide |
| `README.md` | Project overview, getting started, spec conventions, multiarch strategy |

## Critical Gotchas

1. **`--nodeps` required for bootstrap installs.** LFS-era libraries (librpm,
   libsqlite3, etc.) were installed directly onto the filesystem — not via RPM.
   The `.so` files exist but RPM has no record of them. Always use:
   `rpm -ivh --nosignature --nodeps /mnt/repo/<pkg>-*.rpm`

2. **`sudo env "PATH=$PATH"` inside `nix develop`.** Plain `sudo mql` resets
   PATH and loses Nix tools (`xorriso`, `mksquashfs`, `qemu-system-x86_64`).
   Use: `sudo env "PATH=$PATH" mql release iso`

3. **`mql chroot --promote` requires interactive confirmation.** It cannot be
   scripted silently. Manual alternative:
   `sudo rsync -a $MQL_LFS/layers/upper/ $MQL_LFS/base/ && sudo rm -rf $MQL_LFS/layers/upper/*`

4. **Stale overlay mounts after crash.** Use lazy unmount:
   `sudo umount -l $MQL_LFS/merged/{mnt/repo,dev/shm,dev/pts,dev,run,sys,proc}`
   then `sudo umount -l $MQL_LFS/merged`

## Language

All code, comments, commit messages, and documentation must be in
English.

## Rules for This File

This AGENTS.md must stay under 200 lines. When a new topic requires
detailed agent instructions that would exceed this limit, create a
dedicated document in `docs/agents/` instead and add a one-line
reference to the documentation index above. Keep this file as a brief
entry point, not a comprehensive manual.

## Decision Policy

Before choosing any tool, library, package format, or architecture
component with two or more viable options, follow the process in
`docs/DECISION-FRAMEWORK.md`. Never pick a default silently. Present
options to the developer and wait for an explicit decision. Record the
outcome in `docs/DECISIONS.md`.
