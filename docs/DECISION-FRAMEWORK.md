# Decision Framework

When a task requires choosing a tool, library, package format, or architecture
component, the decision must not be made unilaterally by an agent. This document
defines the mandatory research and presentation process.

## When This Applies

Any choice that has two or more viable options and affects:

- A package that will be distributed as part of Maqui Linux
- A build tool used in the development pipeline
- A runtime dependency of the ISO, initramfs, or installer
- A format or protocol that other components depend on

Simple version bumps within the same tool do not require this process.

## The Research Checklist

Before presenting options to the developer, an agent must answer all of the
following questions for each candidate:

**Maintenance:**
- Is the project actively maintained? What was the last release?
- Is there a fork that has superseded the original (e.g. dracut → dracut-ng)?
- How many distributions ship it today?

**Dependencies:**
- What are the build-time dependencies?
- Are there hidden toolchain requirements (Rust, Go, Python, systemd)?
- What does it pull in at runtime?

**Compatibility with Maqui Linux:**
- Does it work without systemd (OpenRC)?
- Does it build cleanly against glibc 2.4x and GCC 15?
- Are there known patches required? Where are they documented (LFS, BLFS,
  Fedora spec, Gentoo ebuild)?

**Self-hosting impact:**
- Does it need to be inside the chroot/initramfs, or only on the build host?
- What is its role in the bootstrap path?
- Does adopting it now block or enable anything later (e.g. Rust toolchain)?

**Long-term fit:**
- Where is the ecosystem heading?
- Is there a "next version" already visible (e.g. 3cpio requires Rust but
  dracut-ng already works without it)?

## Presentation Format

Present findings as a comparison table followed by a recommendation:

```
## Options: <component name>

| Criterion          | Option A         | Option B         | Option C         |
|--------------------|------------------|------------------|------------------|
| Maintained         |                  |                  |                  |
| Last release       |                  |                  |                  |
| Build deps         |                  |                  |                  |
| Hidden deps        |                  |                  |                  |
| OpenRC compatible  |                  |                  |                  |
| glibc 2.4x / GCC15 |                 |                  |                  |
| Known patches      |                  |                  |                  |
| Self-hosting role  |                  |                  |                  |
| Endgame fit        |                  |                  |                  |

**Recommendation:** Option X — <one sentence reason>.
**Decision:** [developer fills in]
```

The agent must wait for the developer's explicit decision before proceeding.
Never assume a default and proceed silently.

## Recording the Decision

Once the developer decides, record the outcome in `docs/DECISIONS.md` using
the format defined there. Include:

- The date
- What was decided
- What the alternatives were
- The stated reason
- Any conditions under which the decision should be revisited

## Source Requirements

Research must draw from primary sources where possible:

- The project's own repository, configure script, and NEWS/CHANGELOG
- Distribution packaging: Fedora `.spec`, Gentoo ebuild, Alpine APKBUILD,
  Arch PKGBUILD, Void Linux template
- LFS / BLFS book (current stable version)
- The project's own documentation site

Secondary sources (blog posts, Stack Overflow) may supplement but must not
be the sole basis for a recommendation.
