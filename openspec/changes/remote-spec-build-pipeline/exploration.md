# Exploration: Remote Spec Build Pipeline for Maqui Linux

## Current State

The Maqui Linux build system is a bash-based toolkit layered into four tiers:

1. **User-facing CLI** (`mql`) -- dispatches to lib/ functions
2. **Library layer** (`lib/*.sh`) -- shared functions: chroot management, repo updates, build dispatch, audit, backup, ISO generation
3. **Script layer** (`scripts/*.sh`) -- heavy-lifting scripts: spec building, install, source fetching, chroot execution, build chaining, async builds
4. **CI layer** (`.github/workflows/*.yml`) -- GitHub Actions on a self-hosted runner at thinkcentre.local

The build process works and is self-hosting (April 2026 milestone). The goal is to make it remote-friendly and contributor-friendly without breaking what works.

---

## A. Current Build System Map

### A.1 Architecture Layers (bottom to top)

```
[Host] thinkcentre.local (NixOS)
  |
  |-- MQL_ROOTFS=/mnt/maquilinux
  |     |-- base/          (immutable rootfs, lower overlay layer)
  |     |-- layers/upper/  (writable changes)
  |     |-- layers/work/   (overlay work dir)
  |     |-- merged/        (active overlay mount)
  |
  |-- [Chroot] $MQL_ROOTFS/merged
  |     |-- /mnt/workspace  -> bind mount of project root
  |     |-- /mnt/repo       -> bind mount of RPMS/
  |     |-- /etc/yum.repos.d/maquilinux-local.repo (auto-generated)
  |     |-- proc, dev, sys, run (virtual FS bind mounts)
  |
  |-- [CI Runner] ~/actions-runner/
        |-- Runner.Listener (self-hosted, runs as user, restarts via systemd)
        |-- NixOS workarounds: DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1
```

### A.2 Complete Build Flow (Step by Step)

```
STEP 1: SOURCE FETCH
  scripts/fetch-spec-sources.sh <spec>
  INPUT:  SPECS/<spec>.spec
  PROCESS: Parse SourceN lines, expand %{name}/%{version} macros (via rpmspec -P or manual fallback)
           Download each URL to SOURCES/<tarball>
  OUTPUT: SOURCES/<name>-<version>.tar.*
  GOTCHAS: rpmspec must be available on host; manual macro expansion as fallback; two URL formats supported

STEP 2: CHROOT SETUP
  mql chroot        --or--  lib/chroot.sh (programmatic)
  PROCESS:
    a. Mount overlayfs: base (lower) + upper + work -> merged
    b. Mount virtual FS: proc, dev, dev/pts, dev/shm, sys, tmpfs (run)
    c. Bind-mount workspace: $TOPDIR -> merged/mnt/workspace
    d. Bind-mount RPMS: $TOPDIR/RPMS -> merged/mnt/repo
    e. Write /etc/yum.repos.d/maquilinux-local.repo (gpgcheck=0)
  CONFIG: MQL_ROOTFS (default /mnt/maquilinux, overridable via env or mql.local)

STEP 3: BUILD RPM
  scripts/build-spec.sh <spec> [--arch=x86_64|i686] [--both] [--skip-tests] [--nodeps]
  INPUT:  SPECS/<spec>.spec + SOURCES/<tarballs>
  PROCESS:
    a. Verify chroot environment (overlay mount, workspace bind mount, rpmbuild binary)
    b. Resolve spec file (appends .spec if needed, detects noarch via BuildArch line)
    c. Check sources exist in SOURCES/ (extracts Source0, expands macros, validates file)
    d. Execute rpmbuild -ba inside chroot via `chroot` command:
       - Clear environment (env -i), set minimal: HOME, TERM, PATH
       - Override all _topdir, _builddir, _sourcedir, _rpmdir, _srcrpmdir to /workspace/*
       - Runs as root via sudo (chroot requires root)
    e. Repeat for i686 if --both (currently same-chroot, same toolchain)
  OUTPUT: RPMS/<arch>/<package>-<version>-<release>.<arch>.rpm + SRPMS/
  DEPS:   BuildRequires must already be installed in chroot or in /mnt/repo
  GOTCHAS: --both doesn't fully work (builds x86_64 only, comments say "needs refactoring")

STEP 4: INSTALL RPM
  scripts/install-spec.sh <pkg> [--arch=...] [--both]
  INPUT:  RPMS/<arch>/<package>-*.rpm
  PROCESS:
    a. Find newest RPM in RPMS/ (x86_64, i686, or noarch directories)
    b. Primary: dnf5 install -y --nogpgcheck <rpm> inside chroot (via mql_chroot_exec)
    c. Fallback: rpm -Uvh --nodeps for bootstrap scenarios (dnf not yet available)
    d. Auto-installs -devel subpackage for x86_64
  OUTPUT: Package installed in chroot rootfs
  GOTCHAS: dnf5 must be available; uses mql_chroot_exec which sources lib/chroot.sh

STEP 5: REPO UPDATE
  scripts/build-chain.sh calls update_repo_for_spec() after each build
  OR: mql repo update [arch]
  PROCESS:
    a. createrepo_c --update RPMS/<arch>/
    b. Called per-spec in build chain for immediate dependency resolution
  OUTPUT: repodata/ in each arch directory
  GOTCHAS: createrepo_c must be available; skipped if not found (warns to run manually)

STEP 6: BUILD CHAIN (optional, orchestration layer)
  scripts/build-chain.sh <specs> [--all] [--resume] [--continue] [--skip-tests] [--heal]
  PROCESS:
    a. Collect spec list (--all = all *.spec in SPECS/; otherwise comma-separated)
    b. State file (.build-chain-state): PENDING/BUILDING/SUCCESS/FAILED/SKIPPED status per spec
    c. For each spec: fetch sources -> build-spec.sh -> install -> update repo -> next
    d. Auto-heal mode: detect common errors (%files mismatch, doc dir, C23 nullptr) and retry
    e. Async mode: launch in detached tmux session (for multi-hour builds like Rust)
    f. Logs: per-spec log files in logs/<spec>-<timestamp>.log
  OUTPUT: per-spec logs + state file + summary
  GOTCHAS: Build stops at first failure (manual resume needed); state file is a simple pipe-delimited text file
```

### A.3 Configuration Surface

| Variable | Source | Default | Used by |
|----------|--------|---------|---------|
| `MQL_ROOTFS` | mql.conf, env, mql.local | `/mnt/maquilinux` | All chroot operations |
| `MQL_RELEASEVER` | mql.conf | `26.4` | Repo paths, repo sync |
| `MQL_REPO_SYNC_HOST` | mql.conf | `rog.local` | CI sync, repo.sh |
| `MQL_REPO_SYNC_PATH` | mql.conf | `/srv/glats/nginx/repo/linux/maquilinux` | CI sync |
| `MQL_REPO_URL` | mql.conf | `https://repo.glats.org/linux/maquilinux` | Public repo URL |
| `MQL_JOBS` | mql.conf | `$(nproc)` | Parallel builds |
| `MQL_KERNEL_VERSION` | mql.conf | `6.17.9` | ISO generation |
| `MQL_BACKUP_DIR` | lib/backup.sh env | `$HOME/maqui-backups` | Backup system |
| `MQL_REPO_PROD` | lib/audit.sh env | `/srv/glats/.../26.4/x86_64/stable` | Production audit |

Overrides: `mql.local` (gitignored) > `mql.conf` (committed) > defaults.

### A.4 Script Dependency Map

```
mql (CLI entry point)
  |-- lib/common.sh      (colors, logging, tool discovery, rootfs path)
  |-- lib/chroot.sh       (mount/unmount/exec/reset/persist/promote/chroot-interactive)
  |     |-- sources lib/common.sh
  |-- lib/build.sh        (mql_build, mql_install -- thin wrappers)
  |     |-- calls scripts/build-spec.sh
  |     |-- calls scripts/install-spec.sh
  |-- lib/repo.sh         (createrepo_c, rsync to remote)
  |     |-- sources lib/common.sh
  |-- lib/backup.sh       (museum-style tar.xz backups, cold storage)
  |     |-- sources lib/common.sh
  |-- lib/audit.sh        (spec vs RPM version audit, JSON/brief/human output)
  |     |-- sources lib/common.sh
  |-- lib/iso.sh          (ISO generation: dracut initramfs, squashfs, grub-mkrescue)
  |     |-- sources lib/chroot.sh, lib/repo.sh, lib/common.sh

scripts/build-spec.sh     (rpmbuild inside chroot)
  |-- sources lib/common.sh

scripts/install-spec.sh   (dnf/rpm install in chroot)
  |-- sources lib/common.sh, lib/chroot.sh

scripts/fetch-spec-sources.sh  (download tarballs)
  |-- sources lib/common.sh

scripts/run-in-chroot.sh  (generic chroot command execution)
  |-- sources lib/common.sh, lib/chroot.sh

scripts/build-chain.sh    (orchestration: fetch + build + install + repo per spec)
  |-- sources lib/common.sh, lib/repo.sh
  |-- calls fetch-spec-sources.sh, build-spec.sh, install-spec.sh (via scripts/ dir)

scripts/check-build-status.sh  (async build monitoring)
  |-- sources lib/common.sh

scripts/start-runner.sh   (GitHub Actions runner lifecycle)
  |-- self-contained (NixOS-specific)
```

### A.5 Release Pipeline (separate from build)

```
mql release rootfs    -> dnf install all RPMs into chroot
mql release tarball   -> tar.xz of base/
mql release iso       -> kernel copy + dracut + squashfs + grub-mkrescue -> ISO
```

CI workflows for releases:
- `iso.yml` -- triggered by tag push (`v*`), builds ISO + uploads to GitHub Release
- `publish-rootfs.yml` -- promotes a named backup to `maquiroot.glats.org`

---

## B. Pain Points

### B.1 What's Artisanal / Fragile / Manual

| Pain Point | Severity | Details |
|------------|----------|---------|
| Chroot requires root/sudo | HIGH | Must run as root; blocks non-admin CI contributors. Every build step needs sudo. |
| Overlay must be pre-mounted by operator | HIGH | CI workflow manually checks and mounts overlay; not self-healing on runner restart |
| `--both` flag is broken | MEDIUM | Comments say "needs refactoring to not use exec" -- builds x86_64 only for --both |
| Manual `--resume` for build chains | MEDIUM | Build stops at first failure; operator must manually fix and re-run with `--resume` |
| State file is a plain pipe-delimited text file | LOW | `.build-chain-state` is fragile; no locking, no JSON/YAML, no structured recovery |
| `rpmspec -P` may not be available on host | MEDIUM | fetch-spec-sources.sh needs `rpmspec` for proper macro expansion; has manual fallback |
| No cross-check between spec version and built RPM version | MEDIUM | audit.sh checks this, but only as a reporting tool -- not enforced at build time |
| Interactive `--promote` confirmation | HIGH | `mql chroot --promote` requires interactive input; cannot be used in CI; CI has its own manual promote workflow (merge-overlay.yml) |
| RPMS cleanup is caveman-style | LOW | CI cleanup step `sudo rm -rf $GITHUB_WORKSPACE/{BUILD,BUILDROOT,RPMS,SRPMS}` -- no tracking of what was cleaned |
| No build artifact retention beyond local filesystem | MEDIUM | RPMS/ is git-ignored; only logs and state file persist; RPMs must be manually synced |
| async mode uses tmux | MEDIUM | `--async` spawns detached tmux sessions; fragile across runner restarts; no structured async job system |

### B.2 What Blocks Remote CI

| Blocker | Why |
|---------|-----|
| Chroot requires sudo + physical disk | Runner must be on thinkcentre.local with `/mnt/maquilinux/` mounted |
| SSH to `rog.local` for repo sync | CI workflow needs SSH keys and network access to `rog.local` |
| GPG key exists only on `thinkcentre` | Signing requires local access to GPG secret key; `rpmsign` via `nix shell nixpkgs#rpm` |
| `mql chroot --promote` is interactive | Cannot promote overlay changes from CI without manual confirmation (CI uses workaround in merge-overlay.yml) |
| Workspace bind-mount is volume-specific | Build output goes to workspace RPMS/; works for local runner but not for external contributors |
| NixOS-specific runner environment | `start-runner.sh` uses NixOS paths (`/run/current-system/sw/bin/bash`, `/run/wrappers/bin`); CI workflow sets NixOS PATH |

### B.3 What Blocks External Contributors

| Blocker | Why |
|---------|-----|
| No access to thinkcentre.local | External contributors can't build; no remote build service |
| No access to rog.local | Cannot sync RPMs; cannot see production repo |
| GPG key is local to thinkcentre | Cannot sign RPMs externally |
| Chroot needs full rootfs disk | Cannot create overlay without a full Maqui Linux rootfs |
| DNF5 from local repo at /mnt/repo | External contributors don't have the RPM repo locally |
| build-chain.sh fetches real sources | Network access needed; fetches from real upstream URLs |
| No sandboxed build environment | Builds run as root, modify real disk; isolation risk for untrusted specs |

---

## C. Current CI Analysis

### C.1 How `build-rpms.yml` Works

**Triggers:**
- `workflow_dispatch` (manual) -- operator specifies specs list, tag, mode (build-only/publish)
- `push` to `main` with path filter: `SPECS/*.spec` or `SOURCES/*`
- `pull_request` with same path filter

**Spec change detection for push/PR:**
```bash
# Detects changed specs by diffing HEAD~1 against HEAD
git diff --name-only HEAD~1 HEAD -- 'SPECS/*.spec' | sed 's|SPECS/||; s|\.spec$||' | tr '\n' ','
```
- `fetch-depth: 2` limits diff to last commit only
- Path filter guarantees at least one spec changed
- If no spec changed (shouldn't happen due to path filter): exits with success

**Runner:**
- `runs-on: [self-hosted, maquilinux]` -- targets thinkcentre.local
- `timeout-minutes: 360` -- 6 hour build timeout
- PATH includes NixOS wrappers: `/run/wrappers/bin:/run/current-system/sw/bin:/usr/bin:/bin`

**Build flow in CI:**
```
1. Verify runner env (sudo, chroot available)
2. Cleanup previous artifacts (sudo rm BUILD/BUILDROOT/RPMS/SRPMS/SOURCES)
3. Checkout (depth=2)
4. Load config (source mql.conf + mql.local)
5. Setup chroot (verify overlay mounted, bind-mount workspace, mount virtual FS)
6. Determine build list (git diff for push/PR, manual input for workflow_dispatch)
7. Backup before build (skip for PR)
8. Check disk space (min 10GB)
9. PR MODE: Validate spec syntax only (rpmspec --parse) -- does NOT build
10. PUSH/DISPATCH MODE: Full build loop:
    a. fetch-spec-sources.sh <spec>
    b. build-spec.sh <spec> --arch x86_64
    c. build-spec.sh <spec> --arch i686 (skip if ExclusiveArch: x86_64)
    d. dnf install RPMs into chroot
    e. ldconfig
11. Collect RPMs (cp from workspace/ to local RPMS/)
12. Sign RPMs (rpmsign via nix shell, only publish mode)
13. Update local repo (staging directory + createrepo_c)
14. Setup SSH for sync (known_hosts + key check)
15. Sync to rog.local (rsync with --ignore-existing, additive only)
16. Success backup post-build
```

**Key observations about current CI:**

**What works well:**
- Spec change detection on push to main is simple and correct
- PR validation (rpmspec --parse only) is the right security model
- Backup before/after build protects against bad builds
- Additive sync (--ignore-existing, no --delete) prevents overwriting signed RPMs
- Disk space check prevents filling the disk mid-build
- Auto-install after build ensures BuildRequires chain works

**What's partially working:**
- `--both` flag not used; i686 built separately with its own build-spec.sh call (works but verbose)
- Signing uses `nix shell nixpkgs#rpm` which creates ephemeral shells (slow, non-deterministic)
- SSH to rog.local is best-effort; warnings emitted but build continues
- Artifact collection step copies from `/workspace/RPMS/` -- fragile path

**What's missing:**
- Build logs not preserved as artifacts (lost after runner cleanup)
- No structured build status (success/failure per spec) surfaced to PR
- No per-spec build isolation; all specs share the same workspace
- No retry on transient failures (network for fetch, build flakes)
- No notification system beyond CI logs
- No build status badge or dashboard
- Spec syntax validation uses `rpmspec --parse` but doesn't check BuildRequires availability
- No cache for unchanged specs (always rebuilds everything in the chain)

### C.2 Runner Capabilities on thinkcentre.local

**What the runner has:**
- Full access to `/mnt/maquilinux/` (rootfs disk)
- `sudo` with passwordless access (required for chroot)
- Nix/NixOS environment (for `nix shell` ephemeral tools: rpm, createrepo_c, xorriso, grub2)
- Internet access (for source fetching, GitHub API)
- SSH keys to `rog.local` (for repo sync)
- GPG key `397EEB9B...` (for RPM signing)
- `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1` (required for .NET runner on NixOS)

**What the runner sees:**
- The GitHub Actions workspace (checked-out repo)
- `/mnt/maquilinux/base/` (immutable rootfs)
- `/mnt/maquilinux/merged/` (active overlay with bind-mounted workspace)
- Not: the overlay layers directly (handled by mount operations in CI)

**Runner can do:**
- `mql build <spec>` -- builds RPM inside chroot
- `mql chroot --exec "<cmd>"` -- arbitrary commands in chroot
- `scripts/build-chain.sh` -- full orchestration (though CI uses its own loop)
- SSH + rsync to rog.local
- `nix shell` for on-demand tools

**Runner limitations:**
- Single machine (can't scale horizontally)
- No sandbox per job (same chroot, same workspace)
- No container isolation (bare NixOS host)
- Requires interactive setup for initial registration (token from GitHub)
- Auto-start via systemd user service (configured but fragile on NixOS)

### C.3 What's Automated vs Manual

| Operation | Automated? | How |
|-----------|-----------|-----|
| Spec change detection | YES | git diff on push to main |
| Source fetching | YES | fetch-spec-sources.sh in CI loop |
| rpmbuild | YES | build-spec.sh in CI loop |
| Install in chroot | YES | dnf/rpm in CI loop |
| Repo metadata update | YES | createrepo_c after build (publish mode) |
| RPM signing | YES | rpmsign via nix shell (publish mode) |
| Repo sync to rog.local | YES | rsync in CI (publish mode) |
| Chroot promote to base | MANUAL | merge-overlay.yml workflow_dispatch with PROMOTE confirmation |
| Rootfs publish to maquiroot | MANUAL | publish-rootfs.yml workflow_dispatch with backup tag |
| ISO build | SEMI | iso.yml triggers on tag push, requires manual tag |
| Backup creation | YES | Auto pre/post build; manual for other scenarios |
| Build chain orchestration | YES | CI implements its own loop, not build-chain.sh |
| PR validation | YES | rpmspec --parse only; no actual build on PR |

---

## D. Industry Pattern Analysis

### D.1 Packit Architecture (Fedora)

**Core model:**
```
GitHub PR/commit -> packit-service (event listener) -> SRPM build -> Koji build -> Bodhi update
```

**Key components:**
1. **packit.yaml** -- declarative config in repo root. Defines:
   - `specfile_path` -- path to spec file
   - `upstream_project_url` -- GitHub repo
   - `jobs` -- what to do on what trigger:
     - `copr_build` on `pull_request` -- test build in COPR
     - `koji_build` on `commit` to dist-git -- production build
     - `bodhi_update` on successful Koji build -- push to Fedora repos
   - `targets` -- chroot targets (fedora-all, epel-9, etc.)
   - `allowed_pr_authors` / `allowed_committers` -- security gate

2. **Spec change detection:** Packit-service receives webhooks from dist-git. Only commits with spec-file changes trigger builds. No spec change = skip.

3. **Build isolation:** Each build in fresh Mock chroot. SRPM built first, then binary RPM. Build logs available via Koji web UI.

4. **External contributor model:** PR from fork triggers COPR build. COPR is a public build service (no access to production infra needed). Build results visible in PR.

5. **Provenance:** All builds logged in Koji. Build ID links to git commit, spec, logs, RPM artifacts.

### D.2 What Maqui Can Adopt

| Packit/Koji Pattern | Maqui Equivalent | Feasibility |
|---------------------|-----------------|-------------|
| `packit.yaml` config | `maqui-build.yaml` in repo root | HIGH -- simple YAML, minimal schema needed |
| Spec change detection | Already working in CI (`git diff HEAD~1 HEAD`) | ALREADY EXISTS |
| PR build in COPR (sandboxed) | PR build on thinkcentre runner (Phase 2) or remote build service (Phase 3) | MEDIUM -- need isolation |
| Koji build on merge | Full build + sign + sync on push to main | ALREADY EXISTS (publish mode) |
| Bodhi update | Repo sync to rog.local + maquiroot publish | ALREADY EXISTS (partial) |
| Webhook-based triggers | GitHub Actions events (push, PR, workflow_dispatch) | ALREADY EXISTS |
| Mock chroot isolation | Current overlay chroot -- shared across builds | NEEDS ISOLATION for Phase 3 |
| Allowed authors/committers | GitHub branch protection rules + PR review | ALREADY EXISTS (GitHub) |

### D.3 What's Overkill for Maqui

- **Koji**: Full Koji is a multi-service system (hub, builder, web, DB) -- too heavy for one distro developer. The overlay chroot is simpler and already works.
- **Bodhi**: Maqui doesn't need Fedora's update-testing-stable pipeline. Additive repo sync is sufficient.
- **fedora-messaging bus**: Over-engineering for a single-builder setup.
- **Sidetag groups**: Maqui builds are sequential (build chain), not parallel with cross-dependencies.

### D.4 COPR Pattern for External Contributors

COPR is worth studying because it solves exactly the Phase 3 problem:
- External user pushes spec to their fork
- COPR fetches sources, builds SRPM, builds binary RPM
- Results visible in COPR web UI and PR status
- No access to production infra needed

Maqui's equivalent could be:
- A lightweight "COPR-like" service on thinkcentre (Phase 3)
- OR a GitHub Actions-based remote build that doesn't need LAN access
- OR a container-based approach (Podman/Docker with chroot inside)

---

## E. Three-Phase Target Architecture

### E.1 Phase 1: Ordered Build Process

**Goal:** Make the artisanal process documented, predictable, and clean. Zero behavioral changes. Zero breakage.

**What changes:**
1. **Create `agent_docs/build-pipeline.md`** -- the definitive ordered documentation of the entire pipeline, superseding the scattered documentation in `build-workflow.md`, `dependency-resolution.md`, and `chroot-lifecycle.md` (these remain as reference, but the pipeline doc is canonical).
2. **Standardize `maqui-build.yaml` schema** -- a declarative config (even if only documentation at first) that describes: spec file location, arch targets, build order dependencies, skip conditions.
3. **Clean up script naming and organization:**
   - `scripts/build-spec.sh` stays (core)
   - `scripts/install-spec.sh` stays (core)
   - `scripts/fetch-spec-sources.sh` stays (core)
   - `scripts/build-chain.sh` stays (orchestration)
   - `scripts/run-in-chroot.sh` stays (utility)
   - `scripts/check-build-status.sh` stays (monitoring)
   - Rename/normalize: no renames needed -- names are clear
4. **Add `--json` output to build scripts** -- machine-readable build status for CI consumption
5. **Fix `--both` flag** in `build-spec.sh` -- make it actually build both arches (the comment says "needs refactoring")
6. **Add `scripts/detect-changed-specs.sh`** -- extract the CI's change detection logic into a reusable script
7. **Document the exact ordering of `build-chain.sh`'s dependency resolution**

**What does NOT change:**
- File paths (SPECS/, SOURCES/, RPMS/, SRPMS/, BUILD/, BUILDROOT/)
- Build behavior (same `rpmbuild` invocation, same chroot path, same env clearing)
- Config file format (mql.conf + mql.local)
- Chroot lifecycle (overlay model stays the same)
- Overlay path (`/mnt/maquilinux/merged`)
- Workspace bind mount (`/mnt/workspace`)

### E.2 Phase 2: CI Remote

**Goal:** Spec-file changes in GitHub PRs on the main repo trigger automated builds on thinkcentre.local. No behavioral change to the build process itself -- only the trigger and artifact pipeline change.

**Trigger mechanism:**
```
PR opened/updated (SPECS/*.spec changed) 
  -> GitHub Actions workflow on [self-hosted, maquilinux]
  -> detect-changed-specs.sh (reusable script from Phase 1)
  -> For each changed spec: build, install, set status
  -> Report results back to PR (status checks + comment)
```

**Build flow (no change from current):**
```
Same as current build-rpms.yml build loop:
  fetch-spec-sources.sh -> build-spec.sh -> install (dnf) -> (publish if on main)
```

**Key differences from current CI:**
1. **Reuse `build-chain.sh` instead of CI's own loop** -- reduces duplication
2. **Per-spec GitHub commit status** -- each spec gets its own status check (not one monolithic check)
3. **Build artifacts as GitHub Actions artifacts** -- RPMs uploaded with retention
4. **Build logs as artifacts** -- `logs/` directory uploaded
5. **PR comment with build summary** -- which specs built, which failed, links to logs
6. **maqui-build.yaml** -- declarative config for which specs to build on what triggers
7. **Phase 2 does NOT introduce:** external contributor support, container isolation, remote build service

**Security model (Phase 2):**
- PR builds are VALIDATION ONLY (rpmspec --parse) -- no actual rpmbuild on PR from fork
- Push to main = full build + install + sign + sync (current publish mode)
- Manual `workflow_dispatch` = operator-specified build list (current behavior)
- GPG key stays on thinkcentre (no export needed)

### E.3 Phase 3: External Contributors

**Goal:** Any developer can fork, modify a spec, open a PR to maquilinux/maquilinux, and see CI build results. No LAN access needed. No thinkcentre.local access needed.

**What's different from Phase 2:**
1. **PR from fork triggers ACTUAL build** (not just validation) -- needs build isolation
2. **Sandboxed build environment** -- cannot use the shared overlay chroot directly
3. **No sign/sync** -- external builds don't touch production repo
4. **Public build logs** -- accessible without thinkcentre access
5. **No chroot promote** -- external builds don't modify the rootfs

**Architecture options for Phase 3:**

**Option A: Container-based build per PR**
```
PR from fork -> GitHub Actions (self-hosted runner)
  -> Fresh overlay chroot (copy of base, new upper layer) per PR
  -> Run build inside isolated chroot
  -> Upload RPMs + logs as artifacts
  -> Discard overlay after build
```
Pros: Reuses existing chroot model, no new tools. Cons: Per-build overlay overhead, disk-intensive.

**Option B: Podman/Docker with maqui-build container**
```
PR from fork -> GitHub Actions (self-hosted runner)
  -> podman run maqui-builder:latest (contains rootfs + rpmbuild + dnf5)
  -> Mount workspace, run build inside container
  -> No chroot needed (container IS the chroot)
  -> Upload RPMs + logs as artifacts
```
Pros: True isolation, reproducible, portable (container could run on any runner). Cons: Need to build and maintain a container image, adds tooling dependency.

**Option C: Remote build API on thinkcentre**
```
PR from fork -> GitHub Actions (github-hosted runner)
  -> POST /api/build to thinkcentre (behind VPN or public endpoint)
  -> thinkcentre builds in sandboxed chroot
  -> Results streamed back via API or webhook
  -> Build logs visible on public status page
```
Pros: Full Maqui build environment, no container work. Cons: thinkcentre needs a public endpoint or VPN service for external contributors.

**Recommendation: Option A for Phase 3 MVP, with Option B as the long-term target.**

Option A is the smallest change from Phase 2:
- Phase 2 already builds on the runner
- Adding per-PR overlay isolation is incremental
- No new infrastructure needed (no container registry, no API server)

Option B is better long-term because:
- A container image makes the build environment reproducible and shareable
- External contributors could run the container locally for pre-PR testing
- Could eventually run on ANY GitHub runner (not just thinkcentre)

**Security considerations for Phase 3:**
- Builds run as root (chroot requires it) -- risk of malicious specs
- Mitigation: Build in a throwaway overlay layer that's discarded after build
- Mitigation: Rate-limit external PR builds (max N concurrent)
- Mitigation: Maintain `allowed_pr_authors` list in maqui-build.yaml (Packit pattern)
- PR builds are "build-only" -- never sign, never sync, never promote

---

## F. Phase 1: Concrete Ordering Plan

### F.1 Files to Reorganize

**No file moves needed.** The current layout is clean:

```
scripts/     -> executable build scripts (good)
lib/         -> sourced library functions (good)
agent_docs/  -> agent reference docs (good)
docs/        -> human-readable docs (good)
openspec/    -> SDD artifacts (good)
```

### F.2 Scripts to Clean Up

1. **`scripts/build-spec.sh`:**
   - Fix the `--both` flag (currently broken -- builds only x86_64, comments say "needs refactoring")
   - Add `--json` flag for machine-readable output (exit code + RPM list + duration)
   - Add `--log-file` flag for explicit log destination

2. **`scripts/build-chain.sh`:**
   - Add `--json` output for state file and summary
   - Add `--stop-on-failure` (default, current behavior) and `--continue-on-failure` options
   - Document the state file format more clearly

3. **`scripts/install-spec.sh`:**
   - Add `--json` output

4. **NEW: `scripts/detect-changed-specs.sh`:**
   - Extract the git diff logic from build-rpms.yml into a reusable script
   - Usage: `detect-changed-specs.sh [base-ref] [head-ref]`
   - Output: comma-separated list or JSON array of changed spec names

### F.3 Docs to Create/Update

1. **NEW: `agent_docs/build-pipeline.md`** -- comprehensive pipeline documentation:
   - Architecture diagram (layers: Source -> Fetch -> Chroot -> Build -> Install -> Repo -> Sign -> Sync)
   - Each step with exact command, inputs, outputs, verification
   - Configuration reference (all MQL_* variables and their effects)
   - Failure modes and recovery per step
   - Relationship to CI workflows

2. **NEW: `maqui-build.yaml` schema** (Phase 2/3 prep, Phase 1 just documents it):
   ```yaml
   # maqui-build.yaml - declarative build config
   specs:
     - path: SPECS/bash.spec
       arches: [x86_64, i686]
       skip_tests: false
     - path: SPECS/linux.spec
       arches: [x86_64]
       skip_tests: true
   jobs:
     - trigger: push
       branch: main
       mode: publish
     - trigger: pull_request
       mode: validate  # or "build" in Phase 3
   ```

3. **Update: `agent_docs/build-workflow.md`** -- note that it's now the quickstart, with pointer to `build-pipeline.md` for the full pipeline

### F.4 What NOT to Change

- **DO NOT change** the overlay chroot model (`base/`, `layers/upper/`, `merged/`)
- **DO NOT change** the `mql` CLI interface (backward compatible)
- **DO NOT change** the `mql.conf` format
- **DO NOT change** spec file conventions (release tags, lib dirs, multiarch macros)
- **DO NOT change** the `rpmbuild` invocation inside the chroot
- **DO NOT change** the workspace bind-mount path (`/mnt/workspace`)
- **DO NOT change** the DNF5 local repo config
- **DO NOT change** any existing workflow YAML files (add new, don't break old)

---

## G. Key Decisions for Proposal Phase

### Questions the user must answer before design starts:

| # | Question | Context | Default recommendation |
|---|----------|---------|----------------------|
| 1 | **Should Phase 2 build on PR from fork (trusted), or only on push to main?** | Current: PR only validates spec syntax. Phase 2 could extend to build for trusted contributors. | Keep validation-only for Phase 2. Actual build on PR is Phase 3. |
| 2 | **What's the `allowed_pr_authors` policy for Phase 3?** | Packit pattern: list of GitHub usernames allowed to trigger builds. Empty = no one. | Start with empty list (no automatic PR builds). Add known contributors manually. |
| 3 | **Should the CI use `build-chain.sh` or maintain its own build loop?** | Current CI has its own loop (duplicated logic). build-chain.sh has more features (state, heal, async, resume). | CI should call build-chain.sh to eliminate duplication. |
| 4 | **What's the artifact retention policy for CI builds?** | RPMs, SRPMs, and logs need retention. GitHub Actions has 90-day default for artifacts. | 90 days for PR builds, permanent for main-line builds (synced to rog.local). |
| 5 | **Should Phase 3 use overlay isolation (Option A) or containers (Option B)?** | Option A is simpler but less portable. Option B is more work upfront but enables local dev testing. | Phase 3 MVP: Option A (per-PR overlay). Long-term: Option B (container image). |
| 6 | **Should `maqui-build.yaml` be mandatory or optional?** | If mandatory, all specs must be listed. If optional, CI falls back to "build all changed specs." | Optional in Phase 1/2, recommended in Phase 3 (for security filtering). |
| 7 | **Does the repo sync to rog.local need to change for Phase 2?** | Current: additive rsync with --ignore-existing. Works for now. | No change needed for Phase 2. Phase 3 needs no sync at all. |
| 8 | **Should CI log verbosity be configurable per spec?** | Some specs (Rust, LLVM) generate massive logs. Others are small. | Yes -- `maqui-build.yaml` per-spec `verbose: true/false`. |
| 9 | **What's the error notification path for CI failures?** | Current: CI log + build summary. No email, Slack, or webhook. | GitHub commit status + PR comment is sufficient. Optional webhook for Phase 3. |
| 10 | **Does the `--both` fix belong in Phase 1 or Phase 2?** | `--both` is broken in build-spec.sh (builds only x86_64). Fixing is low-risk. | Phase 1. It's a bug fix, not a feature. |

---

## Summary: Readiness for Proposal

**Phase 1 (Order)** is ready. The current build system is well-understood, cleanly organized, and functional. The main work is documentation, a few bug fixes, and standardizing CI-facing interfaces (JSON output, reusable scripts).

**Phase 2 (CI Remote)** is mostly already implemented. The current `build-rpms.yml` does 80% of what Phase 2 targets. The remaining work is: reusing build-chain.sh, per-spec status checks, artifact upload, and PR comment integration -- all well within GitHub Actions capabilities.

**Phase 3 (External Contributors)** is the big lift. It requires build isolation (per-PR chroot layers or containers), a security model for untrusted specs, public log visibility, and potentially a remote build API. This is where Packit/Koji/COPR patterns become most relevant, but also where Maqui's single-machine architecture creates the most tension.

---

## H. Acceptance Tests & Verification

### H.1 What Exists Today

| Test | Where | What it verifies | Status |
|------|-------|-----------------|--------|
| Spec syntax validation | `build-rpms.yml` (PR mode) | `rpmspec --parse` returns clean. Catches syntax errors, invalid macros, missing sections. | Operational in CI |
| Version match check | `lib/audit.sh` | RPM version vs spec version vs upstream version. Reports drift, does not block. | Reporting only (not enforced) |
| DNF repo integrity | `lib/audit.sh` | Checks repodata freshness, missing RPMs vs installed deps | Reporting only |
| Backup verify (size) | `publish-rootfs.yml` | Checks backup tarball is >100MB before promoting to maquiroot | Operational in CI |
| Validation tests | `publish-rootfs.yml` | Three-part test suite: (1) file structure sanity, (2) RPM count audit, (3) restore + DNF test | Operational |
| Smoke tests | `mql test smoke` | Runs smoke tests in chroot | Manual trigger only |
| ISO boot | `mql test vm` | Boots ISO in QEMU | Manual trigger only |

### H.2 What's Missing (Acceptance Criteria)

For agents to verify a package build was successful, these checks are needed:

| Test | What to verify | Priority |
|------|---------------|----------|
| **RPM install verification** | `rpm -q <package>` returns installed; `rpm -V <package>` returns clean (no file tampering) | HIGH |
| **Binary execution** | Run `--version` or `--help` on the installed binary; exit code 0 | HIGH |
| **Library linkage** | `ldd` on installed .so files shows no missing libraries | HIGH |
| **DNF dependency check** | `dnf repoquery --requires <package>` shows all deps satisfied | MEDIUM |
| **Multiarch verification** | For `--both` builds: 64-bit libs in `/usr/lib/x86_64-linux-gnu/` and 32-bit in `/usr/lib/i386-linux-gnu/` | MEDIUM |
| **File ownership** | All files owned by the RPM (`rpm -ql <package>` matches installed paths) | MEDIUM |
| **No stray files** | No build artifacts left in workspace after build (BUILD/, BUILDROOT/ cleaned) | LOW |

### H.3 Acceptance Test Flow for CI

```
Build completes -> Install RPM -> Verify package installed (rpm -q) ->
Verify files intact (rpm -V) -> Verify binary runs (--version) ->
Collect RPMs -> Success
```

This should be a reusable verification step in CI. Not just for humans -- agents reading the CI output should be able to determine success/failure from structured status.

---

## I. Backup & Rootfs Publishing Flow

### I.1 Backup System (lib/backup.sh)

**Philosophy:** Museum-style. Never delete. Hot storage (recent) + cold storage (archive).
**Location:** `$HOME/maqui-backups/` (hot), `$HOME/maqui-archive/` (cold).
**Format:** `maquilinux-YYYYMMDD-HHMMSS-<tag>.tar.xz` + `.meta` sidecar.

**Backup lifecycle in CI:**
```
Pre-build backup  ->  Build packages  ->  Post-build (success) backup
                                 |
                                 +-> Restore pre-build if failure
```

**Commands agents must know:**
```bash
mql backup create <tag>       # Create backup of current base rootfs
mql backup list               # List all backups
mql backup restore <name>     # Restore from backup
mql backup museum             # View hot + cold storage
```

### I.2 Rootfs Publishing (publish-rootfs.yml)

**Flow:**
```
1. Trigger: workflow_dispatch with backup_tag
2. Verify backup exists on thinkcentre.local (>100MB)
3. Validation tests (file structure, RPM audit, restore+DNF test)
4. Promote to rog.local -> /srv/glats/nginx/maquiroot/latest/
5. Archive copy to history/ with timestamp
6. Verify promoted backup size
```

**URLs agents must know:**
```
https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz   -- Latest rootfs
https://maquiroot.glats.org/history/<name>.tar.xz                     -- Historical versions
```

### I.3 Backup Enhancements Needed for Phase 2/3

| Enhancement | Why |
|-------------|-----|
| Per-build backup tagging | `pre-build-<spec>-<timestamp>` to isolate which build broke things |
| Backup size reporting in CI summary | Agents need to know if backup grew unexpectedly (sign of a bad build) |
| Automated pre-build backup | Already done in build-rpms.yml. Extend to all build triggers. |
| Post-build backup on failure | Restore to pre-build state automatically. Currently only done for success case. |

---

## J. Agent Knowledge Requirements

### J.1 Paths Agents Must Know

| Path | Type | Purpose |
|------|------|---------|
| `$MQL_ROOTFS/base/` | Local disk | Immutable rootfs (default: `/mnt/maquilinux/base/`) |
| `$MQL_ROOTFS/merged/` | Local disk | Active overlay chroot |
| `$MQL_ROOTFS/repo/` | Local disk | Local RPM repo |
| `$MQL_ROOTFS/layers/upper/` | Local disk | Writable overlay changes |
| `/mnt/workspace` | Inside chroot | Bind-mounted project root |
| `/mnt/repo` | Inside chroot | Bind-mounted RPMS directory |
| `/usr/lib/x86_64-linux-gnu/` | Inside chroot | 64-bit libraries |
| `/usr/lib/i386-linux-gnu/` | Inside chroot | 32-bit libraries |
| `$HOME/maqui-backups/` | Host (thinkcentre) | Hot backup storage |
| `SPECS/` | Project root | RPM spec files |
| `SOURCES/` | Project root | Source tarballs |
| `RPMS/` | Project root | Built RPMs (gitignored) |

### J.2 URLs Agents Must Know

| URL | Type | Purpose |
|-----|------|---------|
| `https://repo.glats.org` | Public | Production RPM repository (DNF5 target) |
| `https://maquiroot.glats.org/latest/` | Public | Latest rootfs tarball for developer download |
| `https://maquiroot.glats.org/history/` | Public | Rootfs archive |
| `https://github.com/glats/maquilinux` | Public | Source repository |
| `thinkcentre.local` | Internal | Build server (SSH, runner host) |
| `rog.local` | Internal | Repo + rootfs server (SSH sync target) |

### J.3 What an Agent Needs to Know to Build a Package (Complete Map)

```
IDENTITY:    Maqui is RPM+DNF5+OpenRC, x86_64+i686, YY.MM versioning
CONFIG:      MQL_ROOTFS (default /mnt/maquilinux), mql.conf + mql.local
CHROOT:      Overlay model (base/upper/work -> merged), bind mounts, virtual FS
BUILD:       fetch-spec-sources.sh -> mql build -> mql install -> mql repo update
SPECS:       m264 tag, multiarch macros, debug_package disabled, ExclusiveArch
DEPS:        BuildRequires chain, dnf from /mnt/repo, build order resolution
VERIFY:      rpm -q, rpm -V, binary --version test, file ownership check
BACKUP:      mql backup create pre/post build, restore on failure
PUBLISH:     repo sync -> repo.glats.org, rootfs promote -> maquiroot.glats.org
PATHS:       12 critical paths (section J.1)
URLS:        6 endpoints (section J.2)
```

---

## K. Developer Workflow & Offline Resilience

### K.1 Full Developer Lifecycle

```
1. DEVELOPER DOWNLOADS LATEST ROOTFS
   curl -O https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz
   
2. MOUNTS LOCALLY
   Developer has their own disk/local setup (not thinkcentre.local).
   Extracts rootfs, mounts overlay, enters chroot.

3. WRITES/MODIFIES SPEC
   Creates or edits SPECS/<package>.spec on their local machine.

4. BUILDS LOCALLY (optional pre-check)
   mql build <spec>  -- tests the build in their local chroot.
   
5. PUSHES TO GITHUB
   git push -> PR or direct push to main.
   
6. CI RUNS ON thinkcentre.local
   GitHub Actions triggers build-rpms.yml.
   Build happens on thinkcentre.local's chroot.
   RPMs built, installed, signed, synced to repo.glats.org.
   Rootfs promoted to maquiroot.glats.org.
   
7. NEXT DEVELOPER DOWNLOADS UPDATED ROOTFS
   Cycle repeats from step 1.
```

### K.2 The Split: Local Dev vs Canonical Build

| Concern | Developer's Machine | thinkcentre.local |
|---------|-------------------|-------------------|
| Rootfs source | Downloaded from maquiroot.glats.org | Self-maintained base/ overlay |
| Build authority | Local only (pre-check, not authoritative) | Canonical (RPMs synced to repo) |
| Signing | None | GPG key on thinkcentre |
| Publishing | None | RSync to rog.local |
| State | Disposable (re-download if broken) | Persistent (backup before/after build) |

### K.3 Offline Resilience

thinkcentre.local may not always be online. When offline:

| Failure Mode | Mitigation |
|-------------|------------|
| CI scheduled run while thinkcentre offline | GitHub runner shows offline. Job queued, runs when runner comes back. |
| PR needs build but runner offline | Author notified: "runner offline, retrying." Manual trigger via `workflow_dispatch` when runner is back. |
| Sync to rog.local fails (network) | Best-effort sync. Warnings logged. Manual sync via `mql repo sync` when network restores. |
| Signing fails (GPG issue) | Build succeeds unsigned. Signing retry via `workflow_dispatch` with `mode: publish`. |

**Manual fallback commands:**
```bash
# If CI couldn't sync, do it manually from thinkcentre:
ssh thinkcentre.local "cd ~/Work/maquilinux && mql repo sync"

# If CI couldn't promote rootfs:
ssh thinkcentre.local "cd ~/Work/maquilinux && mql backup create manual-$(date +%Y%m%d)"
# Then trigger publish-rootfs.yml with the backup tag
```

### K.4 Unified Artifact Flow

```
SPEC change (GitHub)
    |
    v
CI on thinkcentre.local  <-- may be offline, queued
    |
    +-> build RPMs -> install -> sign -> sync -> repo.glats.org
    |
    +-> backup rootfs -> promote -> maquiroot.glats.org
                                          |
                                          v
                              Developer downloads latest rootfs
                              (entry point for new contributors)
```

The public surface is:
- `repo.glats.org` -- DNF5 repository (all built RPMs)
- `maquiroot.glats.org` -- rootfs tarballs (entry point for developers)
- `github.com/glats/maquilinux` -- source + CI

### K.5 Push vs Read Boundary

Files are pushed internally via SSH/rsync. Files are exposed publicly via HTTPS.

| Direction | Mechanism | From | To | Who |
|-----------|-----------|------|----|-----|
| **Push (internal)** | SSH + rsync | thinkcentre.local | rog.local | CI runner |
| **Push (internal)** | SSH + rsync | thinkcentre.local | rog.local (maquiroot) | CI runner |
| **Push (internal)** | bind-mount | Host workspace | Chroot /mnt/repo | CI runner |
| **Read (public)** | HTTPS (nginx) | rog.local | Internet | Developers, users |
| **Read (public)** | HTTPS (nginx) | rog.local | Internet | DNF5 clients |
| **Read (public)** | HTTPS (GitHub) | github.com | Internet | Source, CI logs |

The boundary is `rog.local`'s nginx. Everything behind it is internal push. Everything in front is public HTTPS read. This boundary MUST be explicit in all documentation and agent context.

### K.6 Developer Environment Setup

Two paths to set up a build environment:

**Path A: Nix shell (NixOS / Nix users)**
```bash
git clone https://github.com/glats/maquilinux
cd maquilinux
nix develop  # Provides: rpm, rpmbuild, createrepo_c, dnf5, xorriso, grub2
```
All build tools available inside the nix shell. No host package installation needed.

**Path B: Standalone (any Linux distro)**
```bash
# Install build tools via host package manager:
# Ubuntu/Debian: apt install rpm rpm2cpio createrepo_c dnf5 xorriso grub2
# Fedora:       dnf install rpm-build createrepo_c dnf5 xorriso grub2
# Arch:         pacman -S rpm-tools createrepo_c dnf5 xorriso grub
git clone https://github.com/glats/maquilinux
cd maquilinux
# All mql commands work after tools are installed
```

**After setup (both paths):**
```bash
curl -O https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz
sudo mkdir -p /mnt/maquilinux
sudo tar -xJf maquilinux-rootfs-latest.tar.xz -C /mnt/maquilinux
# Set MQL_ROOTFS if not default:
echo "MQL_ROOTFS=/mnt/maquilinux" > mql.local
mql chroot  # Enter chroot, ready to build
```

This setup guide MUST be part of the Phase 1 documentation output.
```
