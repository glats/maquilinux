# Distro Quality Stack

Objective: an agentic quality stack that keeps Maqui Linux on a Debian filesystem hierarchy with Maqui-style RPM specs, and drives it to a desktop live ISO "al nivel de fedora, guardando proporciones".
Branch: `feat/distro-quality-stack` | Delivery: `ask-on-risk` | Test runner: `bats` (host: `nix shell nixpkgs#bats nixpkgs#rpm -c bats tests/`)

## Specs

- **S1** -- "quiero crear un stack agentico que se preocpue de ella con varias cosas de calidad". Project-scoped agents backed by deterministic, runnable quality gates (agents call gates; gates decide pass/fail).
- **S2** -- "el layout de carpetas tiene que ser debian". Clarified (L2): the INSTALLED SYSTEM filesystem follows the Debian hierarchy (Debian Policy 9.1.1 on top of FHS 3.0); the repository layout (`SPECS/`, `SOURCES/`) stays as-is. Verified rules (https://www.debian.org/doc/debian-policy/ch-opersys.html):
  - packages for 64-bit architectures must not install files in `/usr/lib64` or below;
  - only the dynamic linker and libc may install files in `/lib64`;
  - a package must not install files into a triplet path other than its own architecture's (`x86_64-linux-gnu`, `i386-linux-gnu`);
  - `/usr/libexec` is permitted (FHS 3.0).
- **S3** -- "pero estilo mquilinux (no literal) los specs". Specs remain RPM and follow `agent_docs/spec-conventions.md`, adapted where needed (not a literal copy of another distro's packaging).
- **S4** -- "un stack con herd quizás". Assumption: Herd (https://github.com/Herd-OS/herd) is evaluated as an optional orchestration layer, not a hard dependency, until a tool-adoption evaluation decides.
- **S5** -- "ship distro iso con desktop y todo". A bootable live ISO with a desktop environment and an installer, built and smoke-tested by the pipeline.
- **S6** -- "una distro al nivel de fedora. guardando proporcopnes". Proportional equivalents of Fedora's dist-git, Koji, Bodhi, Pungi/Lorax, openQA, and Anaconda.
- **S7** -- "usado ODD por supuesto para lgorar eos". Tracked in this document and its Engram mirror `odd/distro-quality-stack/tasks`.

## Tasks

| ID | Specs | Route | Status | Evidence |
|----|-------|-------|--------|----------|
| T1 | S1, S2 | inline | done | `mql lint fhs`: Debian path policy over built RPM file lists; RED 9/9 fail, GREEN 9/9 pass (`tests/lint-fhs.bats`), shellcheck clean; commit: see Log L6 |
| T2 | S2, S3 | inline | pending | `mql lint spec`: spec policy (Release tag, debug_package, multiarch block, no hardcoded lib64); wire into PR CI |
| T3 | S2, S3 | TBD, high risk | pending | macros package setting `%_libdir`/`%_libexecdir` to Debian multiarch paths; gated on T1/T2 reports |
| T4 | S1 | inline | pending | doc drift: spec-conventions, multiarch-guide counts, AGENTS.md dead links, acceptance multiarch check accepting `/usr/lib64` |
| T5 | S1 | inline | pending | project agents in `.opencode/` (spec steward, FHS auditor, release engineer, boot QA) calling T1/T2/T6 gates |
| T6 | S5, S6 | TBD, high risk | pending | ISO pipeline defects (grub.cfg/label, rootfs.img vs squashfs.img, base vs overlay) + CI QEMU boot smoke |
| T7 | S5 | TBD | pending | desktop foundation specs: dbus, eudev/elogind decision, PAM, polkit, sudo, openssh, network |
| T8 | S5 | TBD | pending | graphics stack: libdrm, Mesa, Wayland/X, fonts, cairo, pango, GTK |
| T9 | S5 | TBD | blocked on decision | desktop environment: MATE (Engram #2682) vs Cinnamon (Distro.md:128) |
| T10 | S5 | TBD | pending | installer: parted, dosfstools, efibootmgr, then Calamares |
| T11 | S4 | inline | pending | Herd tool-adoption evaluation |
| T12 | S6 | TBD | pending | release gate (Bodhi-lite): testing to stable promotion |

## Log

- **L1** (2026-10-15, user, verbatim): "aca hay una distro from scratch en la que estoy trabajando y quiero crear un stack agentico que se preocpue de ella con varias cosas de calidad: el layout de carpetas tiene que ser debian, pero estilo mquilinux (no literal) los specs. lo que quiero es un stack con herd quizás y ship distro iso con desktop y todo. una distro al nivel de fedora. guardando proporcopnes. usado ODD por supuesto para lgorar eos. será una tarea titanica."
- **L2** (2026-10-15, user answer): "Filesystem del sistema" -- the installed system follows the Debian hierarchy; specs stay RPM with Maqui conventions; repo layout unchanged.
- **L3** (2026-10-15, exploration): `/usr` merge done (SPECS/filesystem.spec:67-69); multiarch dirs exist (:43-44); `/usr/lib64` and `/lib64` are compatibility symlinks (:71,:73); no macros package sets `%_libdir`; only 49/131 specs carry the i686 block, 14 declare ExclusiveArch; no spec linter (CI runs only `rpmspec --parse`); `.opencode/` has no project agents; ISO is live shell only, no desktop or installer; the desktop stack (dbus through DE) has no specs.
- **L4** (2026-10-15, research): Herd-OS/herd is Go, Apache-2.0, created 2026-03, 4 stars, 153 open issues, "in active development"; it runs agents on self-hosted GitHub runners. The Maqui runner also builds RPMs in the overlay chroot, so concurrent agent jobs there need isolation before adoption.
- **L5** (2026-10-15): Next step T1.
- **L6** (2026-10-15, T1 evidence): `bats tests/lint-fhs.bats` RED 9 failing before `lib/lint.sh`, GREEN 9/9 after; `shellcheck -x lib/lint.sh` clean. Baseline over the 40 local RPMs: 1 violation, `lvm2-2.03.38-1.m264.x86_64.rpm: FHS-USR-LIB64: /usr/lib64/libdevmapper.so.1.02` (input for T3). The full package set lives on the build host; rerun there for a complete baseline. Next step: T2.
