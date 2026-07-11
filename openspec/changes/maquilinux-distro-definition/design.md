# Design: Maqui Linux Distro Identity Definition

## Technical Approach

This is a **documentation-only change**: one new file (`docs/DISTRO-IDENTITY.md`) that does not exist yet. Technical design therefore means designing the *document's* architecture, not code architecture. The document is a single ~250-line markdown file with 13 sections, ~50 words per elevator pitch, table-driven where data is multi-dimensional, prose only for narrative/voice sections.

Source of truth for facts: the exploration derived every claim from the actual codebase (`maquilinux.spec`, `os-release`, `mql.conf`, `README.md`, spec changelogs). The design encodes user decisions from `proposal.md` (YY.MM versioning, point releases, fresh-start with no Distro.md references, both canonical domains, all 5 comparison targets, "coming soon" community, DEs as long-term ambition).

Voice contract: confident-but-humble (Chimera), technical-but-accessible (Void), honest-about-limitations (Alpine), not defensive, not aspirational. Future-state items MUST be marked as roadmap, never written as existing.

## Architecture Decisions

### Decision: Document location

**Choice**: `docs/DISTRO-IDENTITY.md` (create the `docs/` directory).
**Alternatives considered**: repository root (`DISTRO-IDENTITY.md`), `openspec/changes/.../` (artifact, not deliverable).
**Rationale**: Proposal scope says `docs/DISTRO-IDENTITY.md`. `docs/` is referenced across `README.md`/`AGENTS.md` but does not exist yet — this change creates it. Root placement would collide with `README.md`'s role. OpenSpec is for SDD artifacts, not shipped docs.

### Decision: 13-section ordering vs exploration's ordering

**Choice**: Keep the proposal's confirmed 13-section order (1 elevator → 13 acknowledgements). Sections 3 ("what makes it different", short table) and 9 ("detailed comparison", full table) are intentionally **split**: section 3 is the hook with a tight 5-row summary, section 9 is the full 5-distro matrix. Avoids duplicating one giant table twice.
**Alternatives considered**: merge sections 3 and 9; drop section 3.
**Rationale**: Chimera's pattern (landing-page differentiation then /about/ depth) reads better than a single comparison dump. Section 3 sells the *unique combination*; section 9 provides *honest multi-axis context*.

### Decision: Table-first content model

**Choice**: Tables for sections 3, 5, 9, 12. Bullet lists for 6, 7, 13. Prose only for 1, 2, 4 (narrative/voice). Mixed for 8, 10, 11.
**Alternatives considered**: all-prose (exploration's 200-300 line target scannability argues against), all-tables (loses voice).
**Rationale**: Estimated per-section lines need to stay under the 30-line scannability budget; tables compress multi-dimensional data best; prose is reserved where tone carries the meaning (elevator pitch, philosophy).

### Decision: Comparison axes (section 9)

**Choice**: 9 columns — Distro | Package manager | Init system | C library | Built from | Multiarch | Release model | Self-hosting | Arch support. Rows: Maqui, Void, Alpine, Chimera, Fedora, Gentoo (6 rows incl. Maqui).
**Alternatives considered**: drop "Self-hosting" (sparse data), drop Gentoo (source-built overlap), add "systemd-free" as its own column.
**Rationale**: systemd-free is constant across all 5 peers except Fedora and is single-column noise — better as a one-line note under the table. Self-hosting differentiates Maqui from Void/Alpine/Chimera (which cannot rebuild themselves purely from their own repo without external bootstrap). Multiarch axis is Maqui's unique column (Debian-style on RPM). Maqui row first (the subject), peers alphabetical after.

### Decision: Technical pillars table (section 5)

**Choice**: 4-column table — Pillar | What it is | Why it matters | Status. 7 pillars from exploration D.1/B.4: RPM+DNF5, OpenRC, x86_64+i686 Debian-multilib, source-built (LFS), self-hosted toolchain, overlayfs dev workflow, m264 versioning.
**Alternatives considered**: 3-column (drop "Status"); 5-column (add "alternatives rejected").
**Rationale**: Status (Operational/In Development) carries Alpine-style honesty and prevents aspirational claims. 7 rows stays under the 30-line budget (header + 7 + 2 framing).

### Decision: Versioning narrative (section 8)

**Choice**: State "26.4 = April 2026, YY.MM format, Ubuntu LTS-style naming" per user Decision 2/3. Release model = point releases (not rolling). Note `m264` release tag = "M[aqui] 26.4" derived from `MQL_RELEASEVER`.
**Alternatives considered**: defer versioning rationale to a separate DECISIONS.md doc.
**Rationale**: Section 8 must answer the single most common new-user question. Proposal confirmed the format; design encodes it verbatim. The `m264` tag derivation is documented only here among shipped docs.

### Decision: Anti-canon (what the doc must NOT contain)

**Choice**: No "we/us/our" not backed by shipped evidence; no Pulsar/Distro.md name or link (user Decision 6, fresh start); no `maqui-linux.org` domain (dropped per Decision 1); no unresolvable URLs; no claims about things that do not exist (DEs, installer, branding, community platforms are explicitly "roadmap" or "coming soon").
**Alternatives considered**: acknowledge Distro.md as history (exploration §F recommended this; user overrode).
**Rationale**: User Decision 6 took priority over exploration §F. Fresh start means divergent aspirations (Calamares, 3 ISO flavors, GitLab) stay out — they were never built.

## Content Flow (Data Flow for a document)

The 13 sections form a reading funnel — high-signal hook → justification → proof → boundaries → roadmap:

```
  [1 Elevator: WHAT] 50-word pitch
        │ (reader decides: keep reading?)
        ▼
  [2 Why exists: WHY] origin narrative sans Pulsar
  [3 Different: short proof] 5-row unique-combo table
  [4 Philosophy: PRINCIPLES] 3-5 tenets + tradeoffs
  [5 Pillars: HOW] 7-row technical-Status table
        │ (reader decides: is this for me?)
        ▼
  [6 IS NOT] boundary-setting (Alpine-pattern)
  [7 Audience + anti-audience] fit statement
  [8 Release/versioning] YY.MM point releases
  [9 Comparison] 6×9 honest matrix
  [10 Governance "coming soon"] minimal
  [11 Branding] name origin + canonical domains
  [12 Roadmap] distributable-first → DEs later
  [13 Acknowledgements] LFS, Gentoo, Fedora/RHEL
```

Transitions: 1→2 ("Why does this exist?"), 2→3 ("What is actually different?"), 5→6 ("Given those pillars, what isn't this?"), 7→8 ("If this is for you, how do releases work?"), 9→10 ("How is it run?"), 12→13 ("Whose shoulders?").

## Section-by-Section Content Architecture

| # | Section title (final) | Format | Target lines | Opening hook | Closing thought |
|---|------------------------|--------|--------------|---------------|-----------------|
| 1 | Elevator Pitch | Prose (1 paragraph) | 8 | "Maqui Linux is an independent x86_64 distribution built from source on Linux From Scratch, packaged with RPM and DNF5, initialized by OpenRC, and self-hosting as of 2026-04-02." | (none — pitch stands alone) |
| 2 | Why Maqui Linux Exists | Prose (2 paragraphs) | 18 | "Most non-systemd distributions picked their own package manager to escape systemd. Maqui took the opposite path: keep the RPM ecosystem, remove systemd." | "The result is the only actively-maintained distribution combining RPM, DNF5, and OpenRC." |
| 3 | What Makes Maqui Different | Table (5 rows: Unique combination) | 12 | "Five attributes together — not any one alone — define Maqui's place in the Linux ecosystem." | one-line note: "Maqui is the only active distro running DNF5 without systemd." |
| 4 | Design Philosophy | Bullet list (3-5 tenets + tradeoffs) | 18 | "Guiding principles, not rules." | (none) |
| 5 | Technical Pillars | Table (Pillar / What / Why / Status) | 14 | "The seven load-bearing technical decisions." | (none) |
| 6 | What Maqui Is Not | Bullet list | 12 | "Naming what something isn't clarifies what it is." | (none) |
| 7 | Target Audience | Two bullet lists (For / Not for) | 10 | "Maqui is not for everyone — and does not try to be." | (none) |
| 8 | Release and Versioning | Mixed (prose + small table) | 16 | "'26.4' is not arbitrary. It is April 2026." | (none) |
| 9 | Comparison with Other Distros | Table (6×9) + 1-line note | 22 | "Honest side-by-side, no spin." | note under table: "All but Fedora are systemd-free." |
| 10 | Governance and Community | Prose + "coming soon" callout | 10 | "A small team, run in the open on GitHub." | "Community channels are planned, not yet launched." |
| 11 | Branding | Prose + small table | 10 | "'Maqui' is the Chilean maqui berry (*Aristotelia chilensis*)." | canonical domains row |
| 12 | Roadmap | Bullet list (marked: in-progress vs planned) | 16 | "Built first, aspirational second." | (none) |
| 13 | Acknowledgements | Bullet list | 10 | "Built on the shoulders of." | (none) |

**Total**: ~202 lines content + ~48 lines for headers/TOC/blank = ~250 lines target.

## Comparison Table Design (Section 9)

Columns (left to right): **Distro | Package manager | Init system | C library | Built from | Multiarch | Release model | Self-hosting | Arch support**

Rows (top to bottom — subject first, peers alphabetical):

| Distro | Package manager | Init | libc | Built from | Multiarch | Release | Self-host | Arch |
|--------|-----------------|------|------|-----------|-----------|---------|-----------|------|
| **Maqui** | RPM + DNF5 | OpenRC | glibc | LFS | Debian-style on RPM | Point (YY.MM) | Yes | x86_64 + i686 |
| Alpine | APK | OpenRC | musl | scratch | none | Rolling | No | multi |
| Chimera | APK | dinit | musl | FreeBSD-rooted | none | Rolling | No | multi |
| Fedora | RPM + DNF5 | systemd | glibc | RPM-native | `/usr/lib64` | Point (6-mo) | Yes | multi |
| Gentoo | Portage | OpenRC (opt) | glibc/musl | source | none | Rolling | Yes | multi |
| Void | XBPS | runit | glibc/musl | scratch | none | Rolling | No | multi |

**Closing note** (single line under table): "Of these, only Maqui pairs RPM+DNF5 with OpenRC and Debian-style multiarch. All peers except Fedora are systemd-free."

## Technical Pillars Table Design (Section 5)

| Pillar | What it is | Why it matters | Status |
|--------|-----------|----------------|--------|
| RPM + DNF5 | Package format and resolver | Reusable, dependency-rich packaging; only active DNF5 distro without systemd | Operational |
| OpenRC | Init system | Service supervision without systemd's coupling | Operational |
| x86_64 + i686 multilib | Debian-style `/usr/lib/{x86_64,i386}-linux-gnu` | Unique on RPM; allows 32-bit compat | Operational |
| Source-built (LFS foundation) | Bootstrapped from Linux From Scratch | Not a fork — full toolchain ownership | Operational |
| Self-hosted toolchain | GCC 15.2, glibc 2.42, kernel 6.17.9 | Distro rebuilds itself from its own repo | Operational |
| overlayfs dev workflow | `mql chroot` immutable base + writable overlay | Reproducible builds, safe experimentation | Operational |
| m264 versioning | Release tag `1.m264` on every spec | Traceability to Maqui 26.4 across 130+ specs | Operational |

All 7 are Operational — none In Development. Honesty check: any pillar not yet shipped MUST show In Development or be moved to section 12.

## Visual Hierarchy (GitHub markdown rendering)

- **H2 (`##`)** for the 13 section titles — anchors auto-generated by GitHub slugify, forms the implicit TOC.
- **No explicit TOC** at top: GitHub's rendered outline serves the purpose; a manual TOC adds 15 lines for marginal benefit at 250 lines.
- **No H3** within the 13 sections — keep flat to honor the 30-line/section budget.
- **Bold** for first-occurrence key terms and pillar names in prose.
- **Code formatting** for paths (`/usr/lib/x86_64-linux-gnu`), commands (`mql chroot`), version tags (`1.m264`), config keys (`MQL_RELEASEVER`).
- **Emphasis** reserved for the elevator pitch's load-bearing adjectives (max 3 instances) and section 9's closing one-liner.
- **Tables** in sections 3, 5, 9, 12 (roadmap table). **Bullet lists** in 4, 6, 7, 13. **Prose** in 1, 2.
- **Single callout** in section 10 (`> **Community channels are planned, not yet launched.**`) — one GitHub blockquote, used sparingly so it carries weight.
- **No admonition syntax** (no `> [!NOTE]` etc.) — plain blockquote keeps the document portable beyond GitHub.

## Anti-Patterns to Avoid

| Anti-pattern | Where it threatens | Mitigation in design |
|--------------|--------------------|--------------------|
| "We/us/our" without evidence | Sections 2, 4, 10 | Use "Maqui" as subject. Replace "we built" with "Maqui was built". Allow "we" only in acknowledgements (verbatim contributor names back it). |
| Pulsar / Distro.md references | Sections 2, 11, 13 | User Decision 6: fresh start. Origin narrative (section 2) frames the "RPM-without-systemd" tension, not the codename. |
| `maqui-linux.org` domain | Section 11 | Decision 1: canonical = `maquilinux.org` + `maquilinux.com`. Spec/email migration is out of scope — doc states intent. |
| URLs that don't resolve | Sections 10, 11 | Link only to `repo.glats.org` (verified resolving) and GitHub repo. `maquilinux.org` named but not hyperlinked. |
| Version numbers not current | Sections 5, 8 | Pin to 26.4 / m264 / April 2026 / kernel 6.17.9 / GCC 15.2 / glibc 2.42 per exploration B.4. |
| Claims about unbuilt things | Sections 6, 12 | DE, installer, branding, community = section 12 roadmap or "coming soon". Never stated as existing. |
| Defensive tone | Sections 2, 4, 9 | State tradeoffs as choices, not attacks. ("Maqui keeps glibc; Alpine keeps musl. Different priorities.") |

## Writing Constraints

- **Hard max 250 lines** (content + headers + blank lines). Section budget above sums to ~250.
- **Elevator pitch max 50 words** (section 1).
- **No section > 30 lines** including its blank-line separators. Largest planned section (9, comparison) is 22 lines.
- **Tables over prose** wherever data has ≥2 dimensions (sections 3, 5, 9, 12).
- **English only** (project convention).
- **No emoji** (project `No Emojis Policy`).
- **Single doc, single file** — no includes, no cross-links to unbuilt docs.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `docs/DISTRO-IDENTITY.md` | Create | The 13-section identity document (~250 lines). Creates the `docs/` directory. |
| `docs/` | Create (dir) | Does not exist today; this change bootstraps it. |

No code, spec, or infrastructure files are modified. `maquilinux.spec`'s divergent domains remain (domain migration is out of scope per proposal).

## Verification Strategy

This change produces a markdown document, not executable code. Verification is structural and stylistic:

| Layer | What to verify | Approach |
|-------|---------------|----------|
| Structure | All 13 H2 sections present, ordered per design | `grep -c '^## ' docs/DISTRO-IDENTITY.md` returns 13 |
| Length | ≤ 250 lines | `wc -l docs/DISTRO-IDENTITY.md` |
| Scannability | No section > 30 lines | Manual scan / per-section line count |
| Elevator pitch | ≤ 50 words | Word-count section 1 prose |
| Voice | No unsupported "we", no Distro.md refs, no `maqui-linux.org` | `grep -i 'pulsar\|distro\.md\|maqui-linux\.org'` returns empty; manual review of "we" usage |
| Anti-patterns | No URLs to unresolvable hosts, no unbuilt features stated as existing | Manual review of sections 6, 9, 10, 11, 12 |
| Facts | Technical claims match codebase (kernel 6.17.9, GCC 15.2, glibc 2.42, DNF5, OpenRC, x86_64+i686) | Cross-check against exploration §B.4 and `maquilinux.spec` |
| Markdown renders | GitHub renders cleanly, tables intact | Manual GitHub preview or `glow`/`mdcat` |

## Migration / Rollout

No migration required. `docs/DISTRO-IDENTITY.md` is a new file. The `docs/` directory is created by this change; later changes (DECISIONS.md, GETTING-STARTED.md, etc.) extend it independently.

Version-anchor policy (from proposal risk): the document pins to release 26.4. When release 27.x ships, section 8's "26.4" references and section 5's toolchain versions update in the same PR as the release tag bump. This is policy, not code, and is recorded here for the apply phase.

## Open Questions

- [ ] None blocking design. All 7 user decisions resolved in proposal.md (2026-07-09).
- [ ] Minor (defer to apply): exact 3-5 tenets wording in section 4 — designer's call during drafting, constrained by "not defensive, not aspirational".
- [ ] Minor (defer to apply): whether section 11 mentions both `maquilinux.org` and `maquilinux.com` as canonical or picks one primary — Decision 1 said "both"; design assumes both listed with `.org` listed first per os-release precedence.