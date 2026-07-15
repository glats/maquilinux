# release-engineering-docs Specification

## Purpose

Agent-accessible documentation describing Maqui Linux release engineering workflows: ISO generation, rootfs publishing, and the installable ISO design approach (implementation deferred).

## Requirements

### Requirement: Release Engineering Reference Documentation

The project MUST include `agent_docs/release-engineering.md` documenting the ISO and rootfs release workflow. The document SHALL describe the full pipeline: build, acceptance, ISO generation, checksum creation, and publishing. It MUST include the publishing URLs for all artifacts: `https://repo.glats.org` (RPM repo), `https://maquiroot.glats.org/latest/` (rootfs), and `https://maquiroot.glats.org/iso/latest/` (ISO). It SHALL reference the associated CI workflow files (`build-rpms-v2.yml`, `iso.yml`, `publish-iso.yml`, `publish-rootfs.yml`) for implementers.

#### Scenario: Agent reads release engineering docs

- GIVEN an agent is tasked with understanding the release pipeline
- WHEN the agent reads `agent_docs/release-engineering.md`
- THEN it understands the sequence: build packages, generate ISO, publish artifacts
- AND it knows the three publishing URLs (repo, rootfs, iso)

#### Scenario: Agent understands ISO publishing flow

- GIVEN an agent reads `agent_docs/release-engineering.md`
- WHEN it follows the documented ISO publishing flow
- THEN it understands that latest ISOs go to `maquiroot.glats.org/iso/latest/`
- AND history ISOs go to `maquiroot.glats.org/iso/history/`
- AND checksums (.iso.sha256, .iso.sha512) accompany each ISO

### Requirement: Installable ISO Design Document

The project SHALL include `agent_docs/installer-design.md` documenting the approach for building an installable ISO. This document is design-only; implementation is deferred. It MUST evaluate at least two installer approaches (e.g., custom script vs. calamares vs. anaconda-lite) with tradeoffs. It SHALL define the minimal feature set for a viable installer and identify dependencies that would need new RPM specs.

#### Scenario: Agent reads installer design

- GIVEN an agent is tasked with implementing an installable ISO
- WHEN the agent reads `agent_docs/installer-design.md`
- THEN it finds evaluated installer approaches with tradeoffs
- AND it sees the deferred implementation notice
- AND it understands the RPM spec dependencies required
