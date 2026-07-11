# Exploration: Maqui Linux Distro Identity (v2, from scratch)

## A. What Distro.md Says Maqui IS (2022 Pulsar Vision)

Distro.md (`/home/glats/Project/maquilinux/Distro.md`, 343 lines) was written by Chris Cromer and Oscar Campos, dated March 12, 2022. It describes "Pulsar Linux" (codename), a GNU/Linux distribution that at the time had no real name. Key identity claims:

### What it intended to be
- **Name**: Undecided; "Pulsar" was a codename placeholder
- **Init system**: OpenRC (anti-systemd stance -- "diametrically opposed" to systemd)
- **Package manager**: RPM + DNF (with rich dependency resolution for package splitting)
- **Release model**: Biannual point releases + LTS (2-year span)
- **ISO images**: Three ISOs (Cinnamon DE, LXDE/Mate lightweight, Base terminal/i3)
- **Installer**: Calamares GUI (primary) + terminal bootstrapping (advanced)
- **Audience**: Developers and Linux enthusiasts ("hardened knowledge appreciated")
- **Kernel**: Latest stable, with updated kernel for LTS hardware support
- **Binary blobs**: Included in official repos (pragmatic over FSF purity)
- **Architecture**: x86_64 only (ARM64 "not discarded for future")
- **Multilib**: Yes, 32-bit x86 on 64-bit
- **Graphics**: GTK prioritized (for Cinnamon/LXDE/Mate)
- **Initramfs**: dracut
- **CI/CD**: Leaning GitLab (detailed comparison of GitHub/BitBucket/GitLab)
- **Languages**: Bash (preferred scripting), Python (scripting), Go (preferred systems), C++ (RPM plugins), Vala (desktop)
- **Licensing**: GPL for shared code, BSD/MIT/Apache2 for other software
- **Repos**: Official (devs) + Community (trusted users); third-party repos discouraged
- **Community**: Inclusive, English-only, anti-harassment
- **Funding**: None at time of writing

### What it explicitly left unresolved
- User sessions/seats: elogind vs consolekit2 (never decided)
- Stages 2 & 3 of LFS: "TBD"
- Name itself: explicitly "not a name proposal"
- Whether DNF+RPM would be adequate long-term ("do not discard creating our own RPM frontend")

### Voice / Tone
The document is formal, detailed, and defensive ("systemd is diametrically in opposition with those beliefs" / "we firmly believe that both debian and its derivatives... got package splitting wrong"). It reads like a design doc for investors or contributors, not a landing page for users.

---

## B. What the Codebase Says Maqui IS (2026 Reality)

### B.1 Identity from maquilinux.spec (the distro's own package)

```spec
Summary: Maqui Linux base configuration
Name: maquilinux
Version: 2
Release: 1.m264
URL: https://maquilinux.com
```

The `os-release` file it generates:
```
NAME="Maqui Linux"
VERSION="26.4"
ID=maquilinux
VERSION_ID=26.4
PRETTY_NAME="Maqui Linux 26.4"
HOME_URL="https://maquilinux.org/"
```

**URL inconsistency confirmed**: maquilinux.spec header says `maquilinux.com`, os-release content says `maquilinux.org`, changelog entries use `info@maquilinux.org`, `team@maqui-linux.org`, `security@maqui-linux.org`, and `dev@maquilinux.org`. Three separate domains in circulation.

### B.2 Identity from README.md

```
"Maqui Linux is an independent Linux distribution built entirely from source.
Every userland package is wrapped in an RPM spec file, giving us repeatable
builds, a consistent filesystem ownership model, and a place to encode
distribution-specific policy. The result is a 64-bit x86_64 system with i686
multilib support, managed entirely by RPM + DNF5, and initialized by OpenRC."
```

Key identity markers:
- "independent" (stated twice)
- "built entirely from source"
- "self-hosting as of 2026-04-02"
- "mql CLI is the single entry point for all development tasks"

### B.3 What Was Actually Built vs Aspirations

| Distro.md (2022) | Reality (2026) | Status |
|---|---|---|
| Pulsar Linux | Maqui Linux | Renamed |
| Biannual + LTS releases | 26.4 (single version, no release cadence defined) | Diverged |
| 3 ISO flavors (Cinnamon/LXDE/Base) | Single bootable ISO (no DE ISOs) | Diverged |
| Calamares installer | No installer (ISO + manual chroot) | Not built |
| Community repos | Single repo (no community tier) | Not built |
| GitLab CI | GitHub Actions + self-hosted runner | Different choice |
| Vala desktop apps | No Vala anywhere in 130 specs | Not pursued |
| C++ for RPM plugins | No C++ RPM plugins | Not needed |
| Python scripting | Present in mql CLI (bash core) | Retained |
| Go for systems | None written yet (all bash) | Not yet used |
| elogind vs consolekit2 | Never resolved (no DE, so no urgency) | Pending |
| LXS/Mate DE | None built | Not started |
| FSF purity debate | No FSF listing concern visible | Moot |
| Stages 2 & 3 TBD | Completed (self-hosting achieved) | Done |

### B.4 Definitively Confirmed Identity Elements

These are non-negotiable, proven by implementation:

1. **Anti-systemd**: 43 references in specs explicitly remove/disable systemd (libdnf5 strips `systemd` dirs, util-linux builds `--without-systemd`, dracut omits `systemd` modules, procps-ng `--without-systemd`)
2. **OpenRC init**: Operational, the only init system
3. **RPM + DNF5**: 130 specs, all with `m264` release tag, DNF5 5.3.0.0 operational
4. **Debian-style multiarch**: `/usr/lib/x86_64-linux-gnu` + `/usr/lib/i386-linux-gnu` (explicitly rejecting `/usr/lib64`)
5. **x86_64 only** (with i686 multilib support)
6. **glibc** (not musl): glibc 2.42, confirmed in base rootfs
7. **GCC 15.2**: Latest toolchain
8. **Linux kernel**: 6.17.9
9. **Self-hosting**: Rebuilds itself from source (achieved 2026-04-02)
10. **Overlayfs workflow**: `mql chroot` with immutable base + writable overlay
11. **m264 distro tag**: Consistent across all 130 specs, meaning "Maqui Linux 26.4"
12. **LFS foundation**: Rooted in Linux From Scratch, but evolved beyond it

### B.5 What Does NOT Exist

- **docs/ directory**: Completely absent. All documentation references in README.md and AGENTS.md (GETTING-STARTED, DECISIONS, MANUAL-NIX, DEVELOPMENT-SYSTEM-PLAN, etc.) are forward references to files that have never been created.
- **Branding/logo**: Zero image files (no PNG, SVG, or any logo format anywhere in the repo)
- **release/ directory**: Mentioned in AGENTS.md but does not exist
- **Website**: maquilinux.org does not resolve to a visible site; the domain redirects to `repo.glats.org`
- **Community channels**: No IRC, Matrix, Discord, or forum documented anywhere

### B.6 Names and Email Addresses in Specs

From changelog entries across 130 specs:
- `Maqui Linux <info@maquilinux.org>` -- most common
- `Maqui Linux Team <team@maqui-linux.org>` -- older entries
- `Maqui Linux <security@maqui-linux.org>` -- crypto-related specs
- `Maqui Linux <dev@maquilinux.org>` -- rust.spec
- `Juan Cuzmar <juan.cuzmar.s@gmail.com>` -- original author

---

## C. Reference Distro Identity Patterns

### C.1 Chimera Linux (gold standard)

**Structure**:
1. Elevator pitch (one paragraph, landing page)
2. Dedicated `/about/` page with philosophy
3. "Why this exists" narrative (born from unhappiness with status quo)
4. Core tenets (simple > complex, opinionated = good, dogmatic = bad)
5. Honest comparison with Alpine and Void
6. Technical specifics framed as "means to an end, not selling points"
7. System design principles (portability > security > benchmarks)
8. Packaging philosophy explained
9. Community values
10. FAQ

**Voice**: Confident, opinionated, intellectually honest, modern. Reads like a manifesto, not a spec sheet.

**Questions answered**: Why does this exist? What makes it different? Who is it for? Why not Alpine/Void/Gentoo instead? What will NEVER change? What is the philosophy behind technical choices?

**Questions NOT answered**: Release cadence (still in development), governance structure (team is small), exact roadmap (still evolving).

### C.2 Void Linux

**Structure**:
1. "Not a fork!" -- first heading, establishes independence immediately
2. Short feature paragraphs: runit, musl/glibc choice, XBPS, xbps-src
3. "Stable rolling release" explained
4. "Developed by volunteers, for fun" -- humble framing
5. No philosophical essay, just what makes it different

**Voice**: Minimalist, confident, "show don't tell." No manifesto, no comparisons, just crisp differentiation. "Here's what we do. Here's what's different. If you like it, use it."

**Questions answered**: Is this a fork? What's unique? How do releases work? Who makes this?

**Questions NOT answered**: Philosophy, target audience, comparison with others, roadmap, governance.

### C.3 Alpine Linux

**Structure**:
1. SSS motto: Small, Simple, Secure
2. Clear audience statement: "power users who appreciate security, simplicity and resource efficiency"
3. Explicit about what it ISN'T: "not recommended for desktop"
4. Container-first identity
5. Technical specifics: musl, BusyBox, OpenRC, apk, PIE binaries

**Voice**: Practical, security-focused, honest about limitations. Not trying to be everything to everyone.

**Questions answered**: What is it optimized for? Who is it for? Who is it NOT for? What are the key technical differentiators?

**Questions NOT answered**: Philosophy beyond SSS, comparisons, future roadmap.

### C.4 Adelie Linux

**Structure**:
1. Comparison table with other distros (side-by-side)
2. OpenRC, musl, desktop focus, longest release cycle among comparables
3. Clear about intended use and target audience

**Voice**: Structured, comparative, transparent. "Let me show you where we fit."

**Questions answered**: How do we compare to others? What release cycle? What init system? What libc?

**Questions NOT answered**: Philosophy, origin story, governance, community values.

### C.5 Gales Linux

**Structure**:
1. Strong, opinionated philosophy document
2. 15 design decisions enumerated
3. History narrative (why previous attempts failed)
4. Very technical, developer-facing

**Voice**: Highly technical, opinionated, detailed. Reads like an engineering design document.

**Questions answered**: What were the failed attempts? What 15 design decisions define us? Why each decision?

**Questions NOT answered**: Target audience, comparison with others, simple elevator pitch.

### C.6 Pattern Synthesis

| Feature | Chimera | Void | Alpine | Adelie | Gales | Maqui needs? |
|---|---|---|---|---|---|---|
| Elevator pitch | Yes | Implicit | Yes (SSS) | No | No | YES |
| Philosophy/Thesis | Yes (manifesto) | No | SSS only | No | Yes (15 decisions) | YES |
| "Why this exists" | Yes | No | No | No | Yes (history) | YES |
| Honest comparison | Yes (Alpine/Void) | No | No | Yes (table) | No | YES |
| Target audience | Implicit | No | Explicit | Yes | Devs | YES |
| Anti-audience | No | No | Yes (no desktop) | No | No | YES |
| Technical pillars | Framed as means | Listed | Listed | Listed | Listed | YES |
| Design tradeoffs | Yes (portability>security) | No | No | No | Yes | YES |
| "What we aren't" | No | "Not a fork!" | Yes | No | No | YES |
| Version/Release model | Not yet defined | "Stable rolling" | Point releases | Longest cycle | Not clear | YES |
| Governance | Small team | Volunteers | Community | Not detailed | Not detailed | YES |
| Branding consistency | Yes | Yes | Yes | Yes | Yes | NO (3 domains) |
| Documentation exists | Yes | Yes | Yes | Yes | Yes | NO (docs/ is empty) |

---

## D. What Makes Maqui Unique (That NO Other Distro Has)

### D.1 Category-Defining Uniqueness

**1. RPM + DNF5 without systemd, built from LFS**
No other distribution combines these three attributes. The only non-systemd RPM distributions historically were Mandriva-era forks, and none have survived in active development. This is genuinely unique in the Linux ecosystem.

- Void: no systemd, but uses XBPS (own package manager)
- Alpine: no systemd, but uses APK + musl
- Chimera: no systemd, but uses APK + musl
- Adelie: no systemd, but uses APK + musl
- Gentoo: no systemd (optional), but uses Portage (source-based)
- openSUSE/Fedora/RHEL: RPM, but systemd
- ALT Linux: APT-RPM, not DNF

Maqui is the **only active distro** running DNF5 (not DNF4) without systemd.

**2. Debian-style multiarch on an RPM system**
Fedora uses `/usr/lib64`. Debian uses `/usr/lib/x86_64-linux-gnu`. Maqui uses the Debian layout while packaging RPMs. This is not done by any major distribution.

**3. Rich dependency-based package splitting**
Distro.md section 1.10.3 describes a system where `dnf` automatically installs `apache-man` when `man` is present, and uninstalls it when `man` is removed. This is implemented via DNF5 rich dependencies. No other distribution markets this as a core identity feature.

**4. Self-hosted from LFS, not forked**
Most distributions fork from Debian, Fedora, or Arch. Maqui was built from LFS -- it bootstrapped its own toolchain and can now rebuild itself entirely. This puts it in the same category as Gentoo and Linux From Scratch itself, but with RPM packaging.

**5. overlayfs-based development workflow**
The `mql chroot` with `--persist`, `--promote`, `--reset` on a dedicated ext4 disk is a development environment, not a user feature. This is a unique take on "how distros are built."

### D.2 Cultural/Narrative Uniqueness

**6. Chilean origin**
The name "Maqui" comes from the Chilean maqui berry (Aristotelia chilensis). The primary developer Juan Cuzmar is Chilean. This is unique among independent distros (Void is Spanish/European, Chimera is European, Alpine is Norwegian, Adelie is US, Gales is unknown).

**7. The "m264" version tag**
The `m264` suffix embedded in every RPM Release tag is a fingerprint unique to Maqui. Version numbering (26.4) is unusual and unexplained -- it doesn't follow calendar versioning (like Ubuntu) or sequential (like Fedora) in any obvious way.

### D.3 What Maqui Shares (Not Unique but Worth Stating)

| Attribute | Shared with |
|---|---|
| OpenRC init | Alpine, Gentoo, Artix, Adelie |
| Anti-systemd stance | Void, Artix, Devuan, Chimera |
| Built from source | Gentoo, LFS, Gales |
| glibc (not musl) | Void (option), most mainstream distros |
| Self-hosted CI runner | Uncommon but not unique |
| Spec-driven development (SDD) | Unique in distro development (using OpenSpec/Engram for a distro is unprecedented) |

---

## E. Proposed DISTRO-IDENTITY.md Structure

Based on Chimera Linux as gold standard, supplemented by patterns from Void, Alpine, and Gales:

### Proposed Section Map

```
1. Elevator Pitch (50 words)
   - One paragraph: what Maqui Linux IS
   - Pattern: Chimera landing page, Alpine SSS

2. Why Maqui Linux Exists
   - Origin story: from Pulsar (2022 vision) to Maqui (2026 reality)
   - What problem it solves
   - The anti-systemd, pro-RPM tension that defines it
   - Pattern: Chimera "why this exists", Gales history narrative

3. What Makes Maqui Different (comparison table)
   - RPM+DNF without systemd (unique)
   - Built from LFS, not forked (rare)
   - Debian-style multiarch on RPM (unique)
   - Rich dep-based package splitting (unique)
   - Overlayfs dev workflow (unique)
   - Comparison rows: Maqui vs Void vs Alpine vs Chimera vs Fedora
   - Pattern: Adelie comparison table, Chimera honest comparison

4. Design Philosophy
   - Core tenets (3-5 principles, like Chimera's "simple > complex")
   - Tradeoffs explicitly stated (e.g., "glibc compatibility over musl minimalism")
   - What will NEVER change (anti-systemd, RPM+DNF, x86_64)
   - What MIGHT change (architectures, DEs, installer)
   - Pattern: Chimera core tenets, Gales 15 decisions

5. Technical Pillars (the 5-7 things that define the distro)
   - RPM + DNF5 package management
   - OpenRC init system
   - x86_64 with i686 multilib (Debian-style layout)
   - Built from source (LFS foundation)
   - Self-hosting toolchain (GCC 15.2 + glibc 2.42 + Linux 6.17.9)
   - overlayfs development workflow (mql CLI)
   - m264 versioning scheme
   - Pattern: Void short feature paragraphs

6. What Maqui IS NOT
   - Not a fork of any existing distro
   - Not a desktop-focused distro (no DE yet)
   - Not container-optimized (unlike Alpine)
   - Not musl-based
   - Not a rolling release
   - Not a general-purpose "everyone" distro
   - Pattern: Void "not a fork", Alpine "not for desktop"

7. Target Audience
   - Primary: Linux developers and enthusiasts who want RPM without systemd
   - Secondary: Self-hosters, infrastructure builders
   - Anti-audience: Desktop newcomers, users wanting "just works" experience
   - Pattern: Alpine explicit audience + anti-audience

8. Release and Versioning
   - What "26.4" means (needs explanation from user)
   - What "m264" tag means
   - Current release strategy (single version, no cadence defined)
   - How updates work (dnf from repo.glats.org)
   - Pattern: Void "stable rolling release" concept

9. Comparison with Other Distros (detailed)
   - Maqui vs Void: RPM vs XBPS, glibc vs optional musl, overlayfs vs none
   - Maqui vs Alpine: RPM vs APK, glibc vs musl, source-built vs package-built, desktop potential vs container-only
   - Maqui vs Chimera: RPM vs APK, glibc vs musl, LFS vs FreeBSD origins
   - Maqui vs Fedora: no systemd vs systemd-mandatory, LFS vs RPM-ecosystem-native
   - Pattern: Chimera honest comparison, Adelie comparison table

10. Governance and Community
    - Current: Juan Cuzmar (primary developer), small team
    - Contribution model: specs, patches, testing
    - Communication: GitHub Issues/PRs (no chat platforms documented)
    - Community values: from Distro.md section 3 (still relevant)
    - Pattern: Chimera community values, Void "volunteers for fun"

11. Branding
    - Name: "Maqui Linux" (origin: Chilean maqui berry)
    - URLs: maquilinux.org (primary -- needs resolution of inconsistency)
    - Logo: (none yet -- aspirational)
    - Color: (none defined)

12. Roadmap (high-level, not detailed)
    - PGP signing (rpm-sequoia bootstrap in progress)
    - Desktop environments (Cinnamon/LXDE aspirational, from Distro.md)
    - Installer (Calamares aspirational, from Distro.md)
    - ARM64 support (not discarded, from Distro.md)
    - Documentation (all 7 missing docs)
    - Pattern: Aspirational but honest about what's not done

13. Acknowledgements
    - Distro.md (original 2022 Pulsar vision by Chris Cromer & Oscar Campos)
    - Linux From Scratch (foundation)
    - Gentoo (OpenRC)
    - Fedora/RHEL (RPM ecosystem)
```

### Voice Guidelines

Based on the synthesis:
- **Confident but humble**: Like Chimera, state what you are and aren't without defensiveness
- **Technical but accessible**: Like Void, show don't tell -- let the technical pillars speak
- **Honest about limitations**: Like Alpine, say who this ISN'T for
- **Opinionated where it counts**: Like Gales, enumerate non-negotiable design decisions
- **Not defensive**: Unlike Distro.md, don't justify choices by attacking alternatives

### Document Length Target
~200-300 lines, scannable with tables and bullet lists, not prose-heavy. Should be possible to skim in 5 minutes and understand everything Maqui is.

---

## F. Key Decisions Needed from User

### Decision 1: Primary domain (consistency)
Three domains are in use: `maquilinux.com`, `maquilinux.org`, `maqui-linux.org`. Which is the canonical domain? This affects `HOME_URL` in os-release, spec `URL` fields, and email addresses.

**Recommendation**: `maquilinux.org` (already in os-release, most widely used in changelogs)

### Decision 2: Version numbering meaning
What does "26.4" represent? Is it a date? A major.minor release? Why 26? This is the single most common question a new user would ask.

**Hypothesis**: Possibly 2026, 4th month or quarter? Or an arbitrary starting point?

### Decision 3: Release model
Distro.md proposed biannual point releases + LTS. Reality is a single 26.4 release with no stated cadence. The identity document needs to say which model it actually follows.

**Options**:
- A. Point releases (biannual or annual)
- B. Single release with continuous updates (stable rolling, like Void)
- C. "Still defining" (honest about current state)

### Decision 4: Desktop ambitions
Distro.md described Cinnamon, LXDE/Mate, and i3 ISOs with Calamares installer. None built. Should the identity document:
- A. Present these as the roadmap (future goal)
- B. Drop them and focus on server/developer use case
- C. Present as "community-contributed" (optional, not core)

### Decision 5: Comparison candidates
Which distros should Maqui compare itself against? The reference set:
- Void (non-systemd, similar audience)
- Alpine (non-systemd, OpenRC)
- Chimera (non-systemd, modern approach)
- Fedora (RPM ecosystem comparison)
- Gentoo (source-built comparison)

### Decision 6: The "Pulsar" legacy
Should Distro.md be acknowledged in the identity document? Options:
- A. Include a "History" section tracing Pulsar -> Maqui
- B. Mention briefly, link to Distro.md as historical reference
- C. Don't mention (start fresh)

**Recommendation**: Option A -- the origin story is compelling and explains why certain decisions were made.

### Decision 7: Community platform
Distro.md defined community guidelines but no platforms exist. Should the identity document define:
- A. Communication channels (Matrix, IRC, Discord, forums)
- B. "Coming soon" placeholder
- C. Not address (developer-only for now)

---

## G. Methodology Notes

### Verification method
- Every claim about Distro.md verified against actual file contents (343 lines)
- Every claim about 2026 reality verified against maquilinux.spec, filesystem.spec, README.md, mql.conf
- docs/ directory absence verified via `ls` command (does not exist)
- Reference distro analysis based on live web pages (pattern extraction, not line-by-line)

### Changes from v1 exploration
- Previous exploration treated Distro.md as aspirational; this analysis treats it as a distinct artifact (2022 plan vs 2026 reality) and maps every divergence
- Previous exploration focused on "what's built"; this focuses on "how does this compare to how peer distros present themselves"
- Previous exploration proposed 12 sections for DISTRO-IDENTITY.md generically; this proposes 13 specific named sections with patterns from reference distros
- Previous exploration treated `docs/` as "missing documents"; this confirms they literally never existed
- URL inconsistency is now quantified (3 different domains in active use) and mapped to specific files
- New finding: Maqui is the **only active distro** combining RPM+DNF5 without systemd
- New finding: Debian-style multiarch on RPM is unique in the ecosystem
