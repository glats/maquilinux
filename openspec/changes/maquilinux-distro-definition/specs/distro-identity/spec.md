# Distro Identity Specification

## Purpose

Requirements for `docs/DISTRO-IDENTITY.md` defining what Maqui Linux IS. All claims MUST verify against codebase. No Pulsar/Distro.md references. 13 sections, ~250 lines.

## Requirements

| # | Section | Must Communicate | Source of Truth | Must Include | Must NOT Include | Format |
|---|---------|-----------------|-----------------|--------------|------------------|--------|
| R.1 | Elevator pitch | Independent distro, source-built, RPM+DNF5 + OpenRC | `README.md` L3-8 | "independent," "RPM+DNF5," "OpenRC," "x86_64 multilib" | Pulsar, systemd comparisons, aspirational | 1 paragraph, 50w max |
| R.2 | Why it exists | RPM without systemd; LFS-bootstrapped; self-hosting 2026-04-02 | `maquilinux.spec` L117-124, `README.md` L10-11 | Self-hosting date, anti-systemd, RPM+OpenRC uniqueness | Distro.md, Pulsar, attacks on others | 3-5 sentences |
| R.3 | Comparison table | Unique matrix vs Void/Alpine/Chimera/Fedora/Gentoo across 6 cols | `maquilinux.spec`, `filesystem.spec` L43-44, `README.md` L3-8 | Columns: init/pkg-mgr/libc/source/arch/multiarch | False claims, "better than" | Table 6r x 7c |
| R.4 | Philosophy | 3-5 tenets with tradeoff rationale | `filesystem.spec` L43-44+70-73, `README.md` L10-14 | Immutables: anti-systemd, RPM+DNF5, x86_64 | Systemd rants, superiority | Bullet list |
| R.5 | Technical pillars | 7 pillars as facts | `README.md` L3-8, `mql.conf` L30, 130 specs (m264) | RPM+DNF5, OpenRC, multilib, LFS, self-hosting, overlayfs, m264 | ARM64, abstractions | Bullet list |
| R.6 | What Maqui IS NOT | 6 boundary statements | `maquilinux.spec` (glibc, no DE) | Not fork/desktop/container/musl/rolling/general-purpose | Patronizing, attacking | Bullet list |
| R.7 | Audience | Devs needing RPM without systemd; anti-audience explicit | `README.md` L3-8, `AGENTS.md` | Primary AND anti-audience stated | "Everyone," general-purpose | 2 paragraphs |
| R.8 | Versioning | YY.MM (26.4=April 2026), LTS-style point releases | `mql.conf` L30, `maquilinux.spec` L119-121+130 | YY.MM explanation, "LTS-style," repo.glats.org | Rolling, LTS duration promises | Paragraph + table |
| R.9 | Deep comparison | Why RPM not XBPS, glibc not musl, LFS not fork | `maquilinux.spec`, `filesystem.spec`, exploration D.1 | Honest tradeoffs per distro | "Better than," inaccuracies | 1 paragraph each |
| R.10 | Governance | Small team (Juan Cuzmar), community "coming soon" | `maquilinux.spec` L165, `AGENTS.md` | "Coming soon," GitHub primary channel | Dead links, promised dates | 2 paragraphs |
| R.11 | Branding | Chilean maqui berry; .org + .com; no logo yet | `maquilinux.spec` L7, L123 | Both domains, berry origin, "no logo yet" | maqui-linux.org, fake logo | Prose + list |
| R.12 | Roadmap | Distributable base -> DEs -> installer -> ARM64; no dates | `AGENTS.md` release/, exploration E.12 | "Long-term ambition," priority order, "no dates" | Firm dates, "202X" | Bullet list |
| R.13 | Acknowledgements | LFS, Gentoo (OpenRC), Fedora/RHEL (RPM ecosystem) | `README.md`, `AGENTS.md` | LFS, Gentoo, Fedora/RHEL; SDD process | Distro.md, Pulsar, author names | 1 paragraph |

## Acceptance Criteria

### Scenario: Claim verifiability
- GIVEN `docs/DISTRO-IDENTITY.md` exists
- WHEN each claim is checked against its Source of Truth file
- THEN every claim resolves to a codebase file, spec, or config value
- AND zero Pulsar/Distro.md/maqui-linux.org references exist

### Scenario: Voice compliance
- GIVEN the document is reviewed for tone
- WHEN checking against Must NOT Include column
- THEN no defensive, attacking, or speculative language
- AND "coming soon"/"no logo yet" appear where reality is incomplete

### Scenario: URL consistency
- GIVEN the document references domains
- WHEN `grep -c "maqui-linux.org" docs/DISTRO-IDENTITY.md` runs
- THEN count is zero; only maquilinux.org and maquilinux.com appear

### Scenario: Structure
- GIVEN the document is complete
- THEN 13 sections with headings exist
- AND `wc -l` returns 200-300 lines
