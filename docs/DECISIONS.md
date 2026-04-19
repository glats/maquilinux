# Decision Log

Record of all tool and architecture choices made during Maqui Linux
development. Follow the process defined in `docs/DECISION-FRAMEWORK.md`
before adding entries here.

---

## 2026-04-19: Remove LFS branding references

**Component:** Project identity and branding - eliminating "Linux From Scratch"
and "LFS" terminology from codebase and documentation.

**Decision:** Remove all explicit LFS branding while maintaining backward
compatibility during transition. See full ADR: `docs/ADR-003-remove-lfs-branding.md`

**Alternatives considered:**

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Keep all LFS references | Acknowledges origins | Weakens independent brand | ❌ Rejected |
| Remove everything including history | Cleanest branding | Loses provenance | ❌ Rejected |
| Remove branding, keep history | Best of both | More work | ✅ Accepted |

**Scope:**
- Configuration: `MQL_LFS` → `MQL_ROOT` (104+ occurrences, backward compat)
- Scripts: `mlfs-runner.sh` → `maqui-runner.sh`, `cleanup-lfs-remnants.sh` → `cleanup-bootstrap-remnants.sh`
- Language: "LFS bootstrap"/"vestiges" → "bootstrap"
- Documentation: Remove "Linux From Scratch" from descriptions
- Preserved: RPM spec changelogs (history), generic "from scratch" phrases

**Sources:** Exploration of 268+ references across 22 files; Maqui Linux
independent distribution positioning requirements.

**Revisit when:** Never. One-time branding separation.

---

## 2026-03-25: cpio implementation

**Component:** cpio archive tool (required by dracut for initramfs creation
and by RPM for `rpm2cpio`)

**Decision:** GNU cpio 2.15 with two patches from BLFS 13.0

**Alternatives considered:**

| Option | Description | Rejected because |
|--------|-------------|-----------------|
| GNU cpio 2.13 / 2.14 | Older versions | Same build failures with glibc 2.36+; no advantage |
| bsdcpio (libarchive) | Already installed, symlink only | Not canonical for RPM; subtle flag differences possible; `rpm2cpio` assumes GNU cpio behaviour |
| 3cpio | Rust-based, fastest option | Requires Rust toolchain bootstrap; hours of compilation; deferred |

**Patches applied:**
```bash
# Fix 1: GCC 15 rejects unprototyped function pointers (BLFS 13.0)
sed -e "/^extern int (\*xstat)/s/()/(const char * restrict,  struct stat * restrict)/" \
    -i src/extern.h
sed -e "/^int (\*xstat)/s/()/(const char * restrict,  struct stat * restrict)/" \
    -i src/global.c

# Fix 2: glibc 2.36+ moved major()/minor() to <sys/sysmacros.h>
ac_cv_rettype_major=int ./configure --prefix=/usr --enable-mt \
    --with-rmt=/usr/libexec/rmt
```

**Sources:** BLFS 13.0 cpio page; OpenWRT issue #15203; GNU cpio 2.15 tarball

**Revisit when:** Never for the patches. Revisit 3cpio once Maqui Linux
bootstraps its own Rust toolchain.

---

## 2026-03-25: initramfs generator

**Component:** Tool that generates the initramfs for live ISO boot and
installed systems.

**Decision:** dracut-ng 110 (without Rust / dracut-cpio)

**Alternatives considered:**

| Option | Maintained | Hidden deps | OpenRC | Endgame fit |
|--------|-----------|-------------|--------|-------------|
| dracut 059 | No (dead Dec 2022) | asciidoc, systemd pkg-config | Yes (omit modules) | No — dead project |
| dracut-ng 110 | Yes (360 contributors, Feb 2026) | libkmod, C compiler | Yes — tested by Void, Alpine, Gentoo | Yes — 3cpio later |
| mkinitcpio | Yes (Arch-focused) | bash, kmod, mkcpio | Partial | No — not RPM-native |
| booster | Yes (Go-based) | Go toolchain | Limited | No — Go bootstrap cost |

**Configure used:**
```bash
./configure \
    --prefix=/usr \
    --sysconfdir=/etc \
    --libdir=/usr/lib \
    --disable-dracut-cpio \
    --disable-documentation
```

**OpenRC dracut.conf:**
```
hostonly="no"
add_dracutmodules+=" dmsquash-live livenet rootfs-block "
omit_dracutmodules+=" systemd systemd-initrd "
compress="zstd"
```

**Sources:** dracut-ng GitHub (360 contributors, v110 Feb 2026); Gentoo Wiki
dracut page; dracut-ng configure script (auto-disables dracut-cpio if no cargo);
dracut-ng NEWS.md (`configure: allow dracut-cpio to be disabled`, v104)

**Revisit when:** Maqui Linux bootstraps Rust toolchain. At that point enable
`--enable-dracut-cpio` and add `3cpio` as an optional dependency.

---

## 2026-03-25: squashfs implementation

**Component:** Tool to compress the rootfs into a squashfs image for the
live ISO.

**Decision:** squashfs-tools 4.6.1 (compiled from source, installed manually)

**Alternatives considered:**

| Option | Description | Notes |
|--------|-------------|-------|
| squashfs-tools 4.6.1 | Reference implementation | Standard, ships in all distros |
| squashfs-tools-ng | New rewrite by the same author | Better API but overkill for now |

**Build notes:** Required `zlib-devel` and `xz-devel` headers. Both were
already present in the chroot. Built with `make -j$(nproc)` and installed
with `install -m 755`.

**Revisit when:** Never for the tool choice. Revisit version at next major
kernel squashfs feature bump.

---

## 2026-03-25: ISO creation tool

**Component:** Tool that assembles the final bootable ISO image.

**Decision:** xorriso / libisoburn 1.5.6

**Alternatives considered:**

| Option | Description | Notes |
|--------|-------------|-------|
| xorriso (libisoburn) | Combines libburn + libisofs | Standard for modern distros; handles Rock Ridge, Joliet, El Torito |
| mkisofs / genisoimage | Legacy tool | Still works but less actively maintained |
| grub-mkrescue | GRUB wrapper around xorriso | Higher abstraction; fine for simple cases |

**Decision rationale:** xorriso is the standard choice. It is already in the
Nix devShell (`libisoburn`) and compiled in the chroot. No reason to deviate.

**Revisit when:** Never.

---

## 2026-04-02: init system

**Component:** Init system for Maqui Linux (PID 1, service management, runlevels)

**Decision:** OpenRC 0.63

**Alternatives considered:**

| Option | Description | Rejected because |
|--------|-------------|-----------------|
| systemd | Most widely used Linux init | Circular dependencies on itself; monolithic; does not fit LFS philosophy; requires many dbus/udev dependencies not yet in the tree |
| s6 / s6-rc | Lightweight, Skarnet's suite | Steep learning curve; less familiar tooling; less RPM-native documentation |
| runit | Very simple, supervisor-based | Limited service management features; less widely used for desktop-adjacent systems |

**Decision rationale:** OpenRC is simpler than systemd (no circular
dependencies, no external bus requirements), works without systemd-specific
kernel features, and is actively tested with LFS/MLFS-style builds. Void Linux,
Alpine, Gentoo, and similar source-based distros all use OpenRC, providing a
good reference base for our configurations.

**Sources:** LFS/MLFS mailing lists; Gentoo and Void Linux documentation; OpenRC
GitHub (active, regular releases).

**Revisit when:** Never — init system choice is foundational and affects many
spec files.

---

## 2026-04-02: package manager

**Component:** Binary package manager and dependency resolver for Maqui Linux

**Decision:** RPM + DNF5

**Alternatives considered:**

| Option | Description | Rejected because |
|--------|-------------|-----------------|
| dpkg + apt | Debian toolchain | Less familiar to the lead developer; .deb format requires different spec infrastructure |
| pacman (ALPM) | Arch Linux package manager | No existing spec ecosystem; PKGBUILD format is not RPM; harder to encode multiarch policy |
| apk (Alpine) | musl-centric, compact | Musl-focused; less suitable for glibc multilib system |

**Decision rationale:** RPM is the package format the lead developer knows well.
DNF5 is the modern, actively maintained dependency resolver (replaced DNF4/YUM).
The `rpmbuild` + `SPEC` format provides fine-grained control over file ownership,
`%pre`/`%post` scriptlets, and multiarch conditionals — all essential for an
LFS-based distribution.

**Sources:** Fedora/RHEL RPM documentation; DNF5 GitHub; MLFS book compatibility.

**Revisit when:** Never — package format is foundational.

---

## 2026-04-02: DHCP client

**Component:** DHCP client for live ISO networking and installed systems

**Decision:** dhcpcd 10.0.6

**Alternatives considered:**

| Option | Description | Rejected because |
|--------|-------------|-----------------|
| dhclient (ISC) | Traditional ISC DHCP client | Being retired upstream; heavy; requires ISC DHCP server libraries |
| NetworkManager | Full network stack | Depends on systemd/polkit; overkill for a minimal live environment |
| systemd-networkd | Integrated with systemd | Requires systemd — not applicable |

**Decision rationale:** dhcpcd is lightweight, has no systemd dependency, works
cleanly with OpenRC, and is actively maintained. It is also used by Alpine Linux
and Void Linux — both of which share our OpenRC + minimal philosophy.

**Sources:** dhcpcd GitHub (Roy Marples, active); Alpine Linux networking setup.

**Revisit when:** Never.

---

## 2026-04-02: busybox role in initramfs

**Component:** Static multi-call binary for the initramfs environment

**Decision:** BusyBox 1.36.1 (static single binary)

**Alternatives considered:**

| Option | Description | Rejected because |
|--------|-------------|-----------------|
| Individual static binaries | ship `sh`, `ls`, `mount`, etc. separately | More complex to build; harder to ensure all needed tools are present |
| toybox | BusyBox alternative | Smaller community; fewer dracut-ng compatibility guarantees |

**Decision rationale:** BusyBox provides all the utilities dracut-ng needs in
the initramfs as a single statically linked binary. No dynamic library
dependencies means no `.so` resolution inside the minimal initramfs environment.
This is the standard approach used by Fedora, Arch, Alpine, and Void.

**Sources:** dracut-ng documentation; BusyBox build system (static musl/glibc
build); Fedora dracut spec.

**Revisit when:** Never.

---

## 2026-04-02: repo metadata generator

**Component:** Tool to generate RPM repository metadata (repodata/)

**Decision:** createrepo_c 1.2.3

**Alternatives considered:**

| Option | Description | Rejected because |
|--------|-------------|-----------------|
| createrepo (Python) | Original Python implementation | Unmaintained since ~2020; slow; replaced by createrepo_c |
| reprepro | Debian-style repo management | .deb only; not applicable |

**Decision rationale:** createrepo_c is the actively maintained C rewrite of
the original Python `createrepo`. It is faster, produces identical output, and
is the standard tool used by Fedora, RHEL, and DNF5. There is no meaningful
alternative in the RPM ecosystem.

**Sources:** createrepo_c GitHub (rpm-software-management org, active); Fedora
packaging guidelines.

**Revisit when:** Never.

---

## Template for future decisions

Copy this block when recording a new decision:

```markdown
## YYYY-MM-DD: <component name>

**Component:** <what role does this fill>

**Decision:** <chosen option>

**Alternatives considered:**

| Option | <criterion> | <criterion> | Rejected because |
|--------|-------------|-------------|-----------------|
| ...    |             |             |                 |

**Sources:** <primary sources used>

**Revisit when:** <condition, or "Never">
```
