# Maqui Linux

Maqui Linux is an independent Linux distribution built from source following
the Linux From Scratch (MLFS multilib) book. Every userland package is wrapped
in an RPM spec file, giving us repeatable builds, a consistent filesystem
ownership model, and a place to encode distribution-specific policy. The result
is a 64-bit x86_64 system with i686 multilib support, managed entirely by
RPM + DNF5, and initialized by OpenRC.

The project is self-hosting as of 2026-04-02: Maqui Linux can rebuild itself
and produce a bootable live ISO without relying on any external distribution.
The `mql` CLI is the single entry point for all development tasks — building
packages, managing the overlay chroot, generating ISOs, and publishing to the
production RPM repository at `repo.glats.org`.

Development happens against a dedicated ext4 disk using an overlayfs-based
workflow. The base rootfs is immutable; all changes happen on an overlay layer
that can be reset, snapshotted, or promoted to the new base. The Nix devShell
(`nix develop`) provides all host tools; standalone development on any distro
is equally supported.

---

## Quick Start

New to the project? Start with:

```
docs/GETTING-STARTED.md
```

It covers prerequisites, disk setup, your first build, and the daily workflow
in under an hour.

---

## Dev Workflow (3-liner)

```bash
nix develop                            # Enter dev shell (or install tools manually)
mql build <spec>                       # Build an RPM
mql chroot --exec "dnf install /mnt/repo/<pkg>-*.rpm"  # Install in chroot
```

---

## `mql` CLI Reference

```
mql chroot                       Enter overlay chroot
mql chroot --exec "<cmd>"        Run command in chroot
mql chroot --reset               Discard overlay changes
mql chroot --persist <name>      Save snapshot
mql chroot --promote             Merge overlay into base (interactive confirm required)
mql build <spec>                 Build RPM
mql build <spec> --both          Build 64+32 bit
mql install <spec>               Install RPM in chroot
mql repo update                  Regenerate repo metadata
mql repo sync                    Publish to repo.glats.org
mql release rootfs               Generate rootfs from RPMs
mql release tarball              Package rootfs as .tar.xz
mql release iso                  Generate bootable live ISO
mql test vm                      Boot in QEMU
mql test smoke                   Run smoke tests
mql config                       Show active config
```

---

## RPM Versioning Scheme

Every spec in this repository uses a consistent scheme for `Version` and
`Release`.

Example filename: `maquilinux-1-1.m264.noarch.rpm`

| Field | Meaning |
| ----- | ------- |
| `Version: 1` | The upstream software version |
| `Release: 1.m264%{?dist}` | `1` = packaging revision; `m264` = Maqui Linux 26.4 distro tag |

- Bump `Version` when the upstream software version changes.
- Bump the numeric part of `Release` when only the spec or packaging changes.
- Keep the `m264` suffix consistent across all specs.

---

## Multiarch Strategy

Maqui Linux uses a **Debian-like multiarch layout** on an x86_64 system with
optional i686 (32-bit) libraries:

- 64-bit libraries: `/usr/lib/x86_64-linux-gnu`
- 32-bit libraries: `/usr/lib/i386-linux-gnu`
- Do **not** use `/usr/lib64`, `/usr/lib32`, or any x32 paths.

Specs enforce this via `--libdir=...` in `configure` / CMake calls, and via
`%if "%{_target_cpu}" == "i686"` conditionals for packages that carry 32-bit
variants.

Library-heavy packages that need 32-bit compatibility (`glibc`, `zlib`,
`openssl`) are built as a single x86_64 RPM that may contain both 64-bit and
32-bit libraries in the respective multiarch directories.

### Standard 32-bit build pattern

```spec
%prep
%setup -q -n %{name}-%{version}
cp -a . ../%{name}-%{version}-32

%build
# 64-bit
./configure --prefix=%{_prefix} --libdir=/usr/lib/x86_64-linux-gnu
make %{?_smp_mflags}

# 32-bit
pushd ../%{name}-%{version}-32
CC="gcc -m32" CXX="g++ -m32" \
./configure --prefix=%{_prefix} --host=i686-pc-linux-gnu \
            --libdir=/usr/lib/i386-linux-gnu
make %{?_smp_mflags}
popd
```

See `SPECS/SPEC_TEMPLATE.md` for the full Gen3 spec template.

---

## Documentation Index

| Document | Covers |
| -------- | ------ |
| `docs/GETTING-STARTED.md` | **Start here** — prerequisites, first build, daily workflow, troubleshooting |
| `docs/MANUAL-NIX.md` | NixOS/Nix users: disk setup, nix develop, NixOS host config, release flow |
| `docs/MANUAL-STANDALONE.md` | Without Nix: tool installation per distro, manual chroot, self-hosting |
| `docs/DEVELOPMENT-SYSTEM-PLAN.md` | Full architecture: overlay system, CLI design, ISO pipeline, self-hosting |
| `docs/DEVELOPMENT.md` | Contribution workflow, CODEOWNERS, branch protection |
| `docs/PIPELINES.md` | Target CI/CD architecture (planned — not yet implemented) |
| `docs/DECISION-FRAMEWORK.md` | Mandatory process before any tool/library decision |
| `docs/DECISIONS.md` | Log of all tool and architecture decisions with rationale |
| `SPECS/SPEC_TEMPLATE.md` | Gen3 spec template and authoring guide |
