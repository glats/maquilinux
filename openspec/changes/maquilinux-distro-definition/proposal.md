# Proposal: Maqui Linux Distro Identity Definition

## Intent

Maqui Linux has no formal definition document. The Distro.md (2022 "Pulsar" codename) describes early aspirations; the 2026 codebase embodies decisions never written down. This gap makes it impossible to answer "what is Maqui Linux?" without reading 130 specs. One definitive identity document solves this.

## User Decisions (2026-07-09)

| # | Decision | Answer |
|---|----------|--------|
| 1 | Canonical domain | Both `maquilinux.org` and `maquilinux.com`. Drop `maqui-linux.org` |
| 2 | Version 26.4 meaning | YY.MM format: April 2026. Ubuntu LTS-style naming |
| 3 | Release model | Point releases, YY.MM versioning (like Ubuntu LTS) |
| 4 | Desktop ambitions | Long-term ambition; start simple with distributable base |
| 5 | Comparison targets | Void, Alpine, Chimera, Fedora, Gentoo (all five) |
| 6 | Pulsar/Distro.md legacy | Fresh start -- no Distro.md references |
| 7 | Community platforms | "Coming soon" placeholder |

## Scope

### In Scope
- `docs/DISTRO-IDENTITY.md` -- single definition paper (13 sections, ~250 lines)

### Out of Scope
- Missing docs (DECISIONS.md, GETTING-STARTED.md, manuals) -- separate changes
- Code, spec, or infrastructure changes
- Skills creation

## Document Structure (13 sections)

| # | Section | Pattern from |
|---|---------|-------------|
| 1 | Elevator pitch (50 words) | Chimera, Alpine SSS |
| 2 | Why Maqui Linux exists | Chimera, Gales |
| 3 | What makes it different (comparison table) | Adelie, Chimera |
| 4 | Design philosophy (core tenets) | Chimera, Gales |
| 5 | Technical pillars (6-7 items) | Void |
| 6 | What Maqui IS NOT | Void "not a fork", Alpine "not for desktop" |
| 7 | Target audience + anti-audience | Alpine |
| 8 | Release and versioning (YY.MM, Ubuntu LTS-like) | Void |
| 9 | Detailed comparison: Void, Alpine, Chimera, Fedora, Gentoo | Chimera, Adelie |
| 10 | Governance and community ("coming soon") | Chimera, Void |
| 11 | Branding (maqui berry, canonical domains) | Chimera |
| 12 | Roadmap (distributable first, then DEs) | All |
| 13 | Acknowledgements (LFS, Gentoo, Fedora/RHEL) | Gales |

### Voice
Confident but humble (Chimera-style), technical but accessible (Void-style), honest about limitations (Alpine-style). Not defensive, not aspirational.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `docs/DISTRO-IDENTITY.md` | New | Single definition paper (~250 lines) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Document becomes stale as distro evolves | Med | YY.MM version tag anchors to current release; update per-release |
| Non-existent sections referenced as fact | Low | Exploration verified every claim against codebase |

## Success Criteria

- [ ] `docs/DISTRO-IDENTITY.md` exists with all 13 sections
- [ ] Scannable: tables, bullet lists, clear section hierarchy
- [ ] Voice matches guidelines (confident, humble, honest)
- [ ] No Pulsar/Distro.md references (fresh start)
- [ ] No code or spec changes introduced
