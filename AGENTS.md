# AGENTS.md -- Maqui Linux
<!-- agent-context-version: "2" -->

## Project

Maqui Linux is an independent Linux distribution built from source, packaged
with RPM and DNF5, initialized by OpenRC, with x86_64 and i686 multiarch
support, and self-hosting as of April 2026. See `docs/DISTRO-IDENTITY.md`.

## Critical Constraints

- All code, comments, commit messages, and documentation in English.
- No emojis in code or output.
- RPM spec files are the single source of truth for package definitions.
- Builds happen inside the overlay chroot, not on the host.

## Quick Commands

```
mql chroot                       Enter overlay chroot
mql chroot --exec "<cmd>"        Run command in chroot
mql build <spec>                 Build RPM (x86_64)
mql build <spec> --both          Build 64+32 bit
mql install <spec>               Install RPM in chroot
mql repo update                  Regenerate repo metadata
mql chroot --reset               Discard overlay changes
```

For the full CLI reference, see `agent_docs/mql-cli-reference.md`.

## Critical Gotchas

1. **`dnf install` for package installs.** Use DNF5 inside the chroot:
   `mql chroot --exec "dnf install /mnt/repo/<pkg>-*.rpm"`

2. **`mql chroot --promote` requires interactive confirmation.** Cannot be
   scripted silently. Manual alternative:
   `sudo rsync -a $MQL_LFS/layers/upper/ $MQL_LFS/base/ && sudo rm -rf $MQL_LFS/layers/upper/*`

3. **Stale overlay mounts after crash.** Lazy unmount:
   `sudo umount -l $MQL_LFS/merged/{mnt/repo,dev/shm,dev/pts,dev,run,sys,proc}`
   then `sudo umount -l $MQL_LFS/merged`

4. **Sources must be in `SOURCES/` before building.** Use
   `scripts/fetch-spec-sources.sh <spec>` or place tarballs manually.

## Agent Documentation Index

| File | What it covers | Stability |
|------|---------------|-----------|
| `agent_docs/distro-identity.md` | What Maqui is, characteristics, versioning | stable |
| `agent_docs/build-workflow.md` | Spec to RPM pipeline step-by-step | mostly-stable |
| `agent_docs/spec-conventions.md` | Spec format, release tag, multiarch macros | stable |
| `agent_docs/chroot-lifecycle.md` | Overlay layers, bind mounts, state management | mostly-stable |
| `agent_docs/dependency-resolution.md` | BuildRequires chain, build order, dnf install | mostly-stable |
| `agent_docs/multiarch-guide.md` | i686 conditionals, library dirs, 32-bit patterns | stable |
| `agent_docs/mql-cli-reference.md` | Full CLI reference, regenerable from `mql --help` | evolvable |
| `agent_docs/troubleshooting.md` | Failure modes, diagnostics, recovery commands | evolvable |
| `agent_docs/acceptance-tests.md` | Post-build verification: rpm -q, rpm -V, binary exec, ldd, multiarch | stable |
| `agent_docs/backup-flow.md` | Backup lifecycle: pre-build, post-build, restore on failure, push-vs-read boundary | mostly-stable |
| `agent_docs/external-contributors.md` | External contributor design: per-PR overlay isolation, auhtor gating, Phase 3 vision | design-only |

Additional context:
| `docs/DISTRO-IDENTITY.md` | Canonical distro definition (human reference) |
| `docs/agents/runner-setup.md` | Self-hosted GitHub Actions runner |
| `docs/agents/backup-system.md` | Rootfs backup strategy |
| `docs/agents/standalone-developer.md` | Download rootfs, local development |

## Configuration

`mql` uses a two-file config system:

| File | Purpose | In git? |
|------|---------|---------|
| `mql.conf` | Project defaults | Yes |
| `mql.local` | User overrides | No |

Key variable: `MQL_ROOTFS` (default: `/mnt/maquilinux`). Override per-session:
`export MQL_ROOTFS=/mnt/maquilinux` or in `mql.local`.

Show active config: `mql config`

## Key Paths

| Path | What |
|------|------|
| `SPECS/` | RPM spec files |
| `SOURCES/` | Source tarballs and patches |
| `RPMS/` | Built RPMs (gitignored) |
| `scripts/` | Build scripts |
| `lib/` | `mql` CLI library (bash) |
| `$MQL_LFS/base/` | Immutable rootfs (overlay lower) |
| `$MQL_LFS/merged/` | Active overlay chroot |
| `$MQL_LFS/repo/` | Local RPM repo |

## Key URLs

| URL | What |
|-----|------|
| `https://repo.glats.org` | Production RPM repository (DNF5 target) |
| `https://maquiroot.glats.org/latest/` | Latest rootfs tarball for developer download |
| `https://maquiroot.glats.org/history/` | Rootfs archive |

## Language and Policy

All code, comments, and docs in English. Before choosing any tool, library,
or architecture component, follow the research process: verify via MCP tools
rather than guessing. Record decisions.

## Context Stack Structure

This file is **Layer 0**: always loaded by the agent (<200 lines, high-signal
content at the top). Files in `agent_docs/` are **Layer 1**: loaded on demand
when the agent's task matches that domain. Build tasks load `build-workflow.md`,
`spec-conventions.md`, and `dependency-resolution.md`. Debug tasks load
`troubleshooting.md`. `distro-identity.md` provides stable reference for any
domain.

## Rules for This File

Keep under 200 lines. When a topic needs detail beyond the pointer index, create
or update a file in `agent_docs/`. Bump `agent-context-version` when structure
changes (file renames, new required files, reorganization).
