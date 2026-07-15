# iso-ci-automation Specification

## Purpose

Automated live ISO generation triggered by CI pipeline, delegating to `mql release iso`, with publishing to GitHub artifacts/releases and maquiroot.glats.org.

## Requirements

### Requirement: ISO Triggered by Clean CI Build

The system MUST generate a live ISO on every successful push to the default branch where ALL built spec packages pass acceptance tests. The system MUST skip ISO generation when any spec build fails (partial failure).

#### Scenario: Clean build generates ISO

- GIVEN a push to main triggers `build-rpms-v2.yml`
- WHEN all spec builds and acceptance tests pass
- THEN the ISO workflow is invoked and produces a bootable ISO
- AND the ISO is uploaded as a GitHub artifact

#### Scenario: Partial failure skips ISO

- GIVEN a push triggers the build pipeline
- WHEN any spec build or acceptance test fails
- THEN ISO generation SHALL NOT be invoked
- AND the pipeline reports that ISO was skipped due to build failure

### Requirement: ISO Delegates to mql CLI

The ISO workflow MUST use `mql release iso` instead of inline dracut, squashfs, or grub-mkrescue steps. The workflow MUST run `mql release rootfs` before `mql release iso` to ensure all RPMs are installed in the base rootfs. ISO tool dependencies (dracut, grub, libisoburn, squashfs-tools, mtools) MUST be verified present before generation.

#### Scenario: ISO build uses mql release iso

- GIVEN the ISO workflow is invoked
- WHEN `mql release rootfs` completes successfully
- AND ISO tool dependencies are confirmed installed
- THEN `mql release iso` generates a bootable ISO
- AND no inline dracut, squashfs, or grub-mkrescue commands exist in iso.yml

### Requirement: Workflow Call Invocation

The ISO workflow MUST expose a `workflow_call` trigger so `build-rpms-v2.yml` can invoke it programmatically. The callable interface SHALL accept version and mode inputs.

#### Scenario: build-rpms-v2 invokes ISO via workflow_call

- GIVEN `build-rpms-v2.yml` completes with all specs passing
- AND the run mode is publish or the event is push to main
- WHEN the workflow invokes iso.yml via `workflow_call`
- THEN iso.yml receives version and mode parameters
- AND proceeds with ISO generation

### Requirement: ISO Publishing Targets

Every generated ISO MUST be uploaded as a GitHub artifact (retention 90 days). On a tag push, the ISO MUST also be attached to the corresponding GitHub Release. In publish mode, the ISO MUST be synced to `maquiroot.glats.org/iso/latest/` with SHA-256 and SHA-512 checksums alongside. History ISOs SHALL be archived under `maquiroot.glats.org/iso/history/`.

#### Scenario: Tag push publishes to GitHub Release

- GIVEN a tag push (e.g., `v26.4`) triggers the ISO workflow
- WHEN the ISO is generated
- THEN it is uploaded as a GitHub artifact
- AND attached to the GitHub Release for that tag

#### Scenario: Publish mode syncs to maquiroot

- GIVEN the ISO workflow runs in publish mode
- WHEN the ISO passes size and structure verification
- THEN it is rsynced to `maquiroot.glats.org/iso/latest/maquilinux-latest-x86_64.iso`
- AND SHA-256 and SHA-512 checksum files are published alongside

### Requirement: ISO Integrity Verification

Before publishing, the system MUST verify the ISO file size is greater than zero. The system MUST generate SHA-256 and SHA-512 checksums for every ISO artifact.

#### Scenario: Zero-size ISO not published

- GIVEN `mql release iso` produces an output file
- WHEN the file size is zero bytes
- THEN publishing MUST be skipped
- AND the workflow SHALL fail with a descriptive error

#### Scenario: Valid ISO passes verification

- GIVEN `mql release iso` produces a valid ISO
- WHEN the file size is above zero
- THEN checksums are generated
- AND publishing proceeds
