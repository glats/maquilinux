# Maqui Linux: Distro Identity and Definition

## What is Maqui Linux

Maqui Linux is an independent Linux distribution built from source, packaged
with RPM and DNF5, initialized by OpenRC, with x86_64 and i686 multiarch
support, and self-hosting as of April 2026.

The project was born from the conviction that an independent distribution
should own its entire stack -- from toolchain to package manager -- without
inheriting decisions made by other projects. Maqui originated on a Linux
From Scratch base and has since evolved into a fully independent distribution
with its own toolchain, package repository, and build infrastructure. It
rebuilds itself from its own repository using its own RPM specifications.

## Characteristics

| Characteristic | Detail |
|----------------|--------|
| Package manager | RPM + DNF5 |
| Init system | OpenRC |
| Architectures | x86_64 with i686 multiarch |
| Multiarch layout | `/usr/lib/x86_64-linux-gnu` and `/usr/lib/i386-linux-gnu` |
| C library | glibc |
| Compiler | GCC 15.2 |
| Kernel | Linux 6.17.9 |
| Release model | Point releases |

## Multiarch

Maqui supports both x86_64 and i686 from a single system using a unified
library layout under `/usr/lib`. Both architectures coexist in the same
filesystem: 64-bit libraries live at `/usr/lib/x86_64-linux-gnu` and 32-bit
libraries at `/usr/lib/i386-linux-gnu`. This layout keeps the filesystem
clean and predictable, avoiding separate `/usr/lib64` or `/usr/lib32`
directories. The result is seamless 32-bit compatibility on a 64-bit base,
reproduced across 100 packaging specifications.

## How Packages Work

Every piece of software in Maqui is defined by an RPM specification file.
These specs are the single source of truth: they encode build configuration,
dependencies, filesystem layout, and distribution policy in one
source-controlled document. No package enters the repository without one.

The repository is regenerated from these specs using `createrepo_c`,
ensuring that every binary RPM traces back to a specific build recipe. This
gives the distribution full provenance over its entire package set and the
ability to rebuild any component from source at any time.

## Purpose

Maqui Linux targets developers and Linux enthusiasts who want an
RPM-managed system initialized by OpenRC. The distribution provides broad
hardware support, including compatibility with proprietary firmware and
platforms such as Steam.

## Community

Maqui is built in the open. Development, issue tracking, and contribution
review happen on public infrastructure accessible to anyone. The project
welcomes contributions regardless of background and values direct,
respectful collaboration. Community communication channels are currently
being established and will be announced when available.

## Release and Versioning

Version numbers follow `YY.MM` format. The current release, 26.4,
corresponds to April 2026. Each RPM carries the release tag `1.m264`,
identifying it as part of the Maqui Linux 26.4 package set.

| Component | Detail |
|-----------|--------|
| Version format | YY.MM |
| Current release | 26.4 (April 2026) |
| RPM release tag | `1.m264` |
| Update mechanism | `dnf` from `repo.glats.org` |

## Branding

"Maqui" is the Chilean maqui berry (*Aristotelia chilensis*), a native
South American fruit. The name reflects the distribution's origin and its
independence from established distribution families.

| Element | Detail |
|---------|--------|
| Name | Maqui Linux |
| Domains | `maquilinux.org`, `maquilinux.com` |
