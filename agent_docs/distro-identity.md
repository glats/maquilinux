# Distro Identity
<!-- stability: stable | last-reviewed: 2026-07-10 -->

Maqui Linux is an independent Linux distribution built from source, packaged
with RPM and DNF5, initialized by OpenRC, with x86_64 and i686 multiarch
support, and self-hosting as of April 2026.

The project originated on a Linux From Scratch base and evolved into a fully
independent distribution with its own toolchain, package repository, and
build infrastructure. It rebuilds itself from its own repository using its
own RPM specifications.

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
| Version format | YY.MM (26.4 = April 2026) |
| RPM release tag | `1.m264` on all packages |

## Branding

"Maqui" is the Chilean maqui berry (*Aristotelia chilensis*). Domains:
`maquilinux.org` and `maquilinux.com`.

## Related Docs

- [Build Workflow](build-workflow.md) -- the full build pipeline
- [Spec Conventions](spec-conventions.md) -- how specs are structured
- [Canonical Definition](../docs/DISTRO-IDENTITY.md) -- human reference
