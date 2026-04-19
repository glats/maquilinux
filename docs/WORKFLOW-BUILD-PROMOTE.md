# Build and Promotion Workflow

This document describes the two-phase workflow for building packages and promoting stable rootfs backups to `maquiroot.glats.org`.

## Overview

Maqui Linux uses a **two-phase workflow** to ensure only validated, working rootfs backups are published for other developers:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   build.yml │ ──► │   VALIDATE   │ ──► │  promote.yml    │
│   (compile) │     │   (manual)    │     │  (publish)      │
└─────────────┘     └──────────────┘     └─────────────────┘
       │                                           │
       ▼                                           ▼
post-build-OK                              maquiroot/latest/
(local backup)                           (public stable)
```

## Phase 1: Build (build.yml)

### Purpose
Compile packages, run basic tests, create local backup. **Does NOT publish to maquiroot.**

### Trigger
- `push` to `main` with spec changes
- `workflow_dispatch` with explicit spec list

### What it does
1. Determines build list (auto-detect or manual input)
2. Creates **pre-build backup** (rollback point)
3. Fetches sources (on host, chroot has no internet)
4. Builds each spec in order (x86_64 + i686)
5. Installs to chroot using `dnf` (proper deps)
6. Signs RPMs with GPG
7. Updates local repo + syncs to `repo.glats.org`
8. Creates **post-build-ok backup** (local only)

### Outputs
- RPMs in `RPMS/{x86_64,i686}/`
- Backups in `~/maqui-backups/`:
  - `pre-build-<tag>.tar.xz` — rollback point
  - `post-build-<tag>-ok.tar.xz` — candidate for promotion

### Example
```bash
# Manual build of rust toolchain
gh workflow run build.yml \
  -f specs="rust,rpm-sequoia,rpm" \
  -f tag="rust-bootstrap-attempt-2"
```

## Phase 2: Promotion (promote.yml)

### Purpose
**Explicitly** publish a validated backup to `maquiroot.glats.org` for other developers.

### Philosophy
The build can "succeed" but produce a broken system (e.g., missing critical libs, broken DNF). Promotion is **manual and explicit** to ensure only working states are published.

### Trigger
Only `workflow_dispatch` (manual):

```bash
# Promote a specific backup after testing
gh workflow run promote.yml \
  -f backup_tag="post-build-rust-bootstrap-attempt-2-ok" \
  -f skip_validation=false
```

### What it does
1. **Verify backup exists** — checks `~/maqui-backups/`
2. **Validation tests** (unless `skip_validation=true`):
   - Backup archive integrity (`tar -tz`)
   - Critical files present (dnf, rpm, rpm DB)
   - DNF functionality in chroot
   - RPM database sanity check
3. **Dry run option** — preview what would be synced
4. **Sync to maquiroot**:
   - `latest/maquilinux-rootfs-latest.tar.xz` — current stable
   - `history/maquilinux-<timestamp>-stable.tar.xz` — archived
   - `index.json` — API for scripts

### Validation Tests

| Test | Purpose |
|------|---------|
| Archive integrity | Backup not corrupted |
| Critical files | DNF, RPM, configs present |
| DNF in chroot | Package manager works |
| RPM database | Can query packages (>100 expected) |

### Skip Validation (Emergency)

For emergencies when you know the backup is good but tests are flaky:

```bash
gh workflow run promote.yml \
  -f backup_tag="post-build-urgent-fix-ok" \
  -f skip_validation=true \
  -f dry_run=false
```

⚠️ **Use with caution** — can break `maquiroot/latest/` for all developers.

## Workflow Examples

### Example 1: Rust Bootstrap (Multi-Attempt)

```bash
# Attempt 1: Build rust
gh workflow run build.yml -f specs="rust,rpm-sequoia,rpm" -f tag="rust-attempt-1"
# ... build fails ...
# Rollback manually if needed

# Attempt 2: Fix spec, rebuild
gh workflow run build.yml -f specs="rust,rpm-sequoia,rpm" -f tag="rust-attempt-2"
# ... build succeeds ...
# Test locally: enter chroot, verify rustc --version, etc.

# Promote after validation
gh workflow run promote.yml -f backup_tag="post-build-rust-attempt-2-ok"

# Now build next package using stable rust
gh workflow run build.yml -f specs="ripgrep" -f tag="ripgrep-with-rust"
```

### Example 2: XFCE4 Desktop (Cascading Builds)

```bash
# Build base libraries
gh workflow run build.yml -f specs="libxcb,xorg-server" -f tag="x11-base"
gh workflow run promote.yml -f backup_tag="post-build-x11-base-ok"

# Build window manager
gh workflow run build.yml -f specs="xfwm4" -f tag="xfce-wm"
gh workflow run promote.yml -f backup_tag="post-build-xfce-wm-ok"

# Build session and desktop
gh workflow run build.yml -f specs="xfce4-session,xfce4-desktop" -f tag="xfce-full"
gh workflow run promote.yml -f backup_tag="post-build-xfce-full-ok"
```

### Example 3: Rollback (Last Known Good)

```bash
# Build xfce4-panel (breaks something)
gh workflow run build.yml -f specs="xfce4-panel" -f tag="panel-update"
# ... tests show it's broken ...
# DO NOT promote

# Revert maquiroot to previous stable
gh workflow run promote.yml \
  -f backup_tag="post-build-xfce-full-ok" \
  -f skip_validation=true  # Already validated before

# Developers now download working version
```

## Directory Structure

### Local (Runner)
```
~/maqui-backups/
├── maquilinux-20260418-120000-pre-rust-attempt-1.tar.xz
├── maquilinux-20260418-150000-post-rust-attempt-2-ok.tar.xz  ← candidate
└── maquilinux-20260418-160000-post-x11-base-ok.tar.xz        ← stable
```

### Public (maquiroot.glats.org)
```
/srv/glats/nginx/maquiroot/
├── index.json                    # API listing
├── index.html                    # Human browsing (nginx autoindex)
├── latest/
│   ├── maquilinux-rootfs-latest.tar.xz      # ← current stable
│   └── maquilinux-rootfs-latest.tar.xz.meta # metadata
└── history/
    ├── maquilinux-20260418-120000-stable.tar.xz  # archived
    └── maquilinux-20260418-150000-stable.tar.xz
```

## Developer Usage

### Download Latest Stable

```bash
# Download from maquiroot
curl -O https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz
curl -O https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz.sha256
sha256sum -c *.sha256

# Extract to disk and develop
# ...
```

### Download Specific Version

```bash
# Browse history
curl https://maquiroot.glats.org/history/ | grep maquilinux

# Download specific
curl -O https://maquiroot.glats.org/history/maquilinux-20260418-120000-stable.tar.xz
```

### API (for Scripts)

```bash
# Get JSON listing
curl https://maquiroot.glats.org/index.json | jq '.'
```

## Comparison: build.yml vs promote.yml

| Aspect | build.yml | promote.yml |
|--------|-----------|-------------|
| **Trigger** | push, manual | **manual only** |
| **Purpose** | Compile packages | Publish stable rootfs |
| **Creates backups** | Yes (pre/post) | No (uses existing) |
| **Syncs to maquiroot** | No | **Yes** |
| **Validation** | Basic (dnf install works) | Thorough (archive, chroot, DNF, RPM DB) |
| **Can rollback** | Via local backups | Via re-promoting older backup |
| **Affects other devs** | No (local only) | **Yes (published)** |

## Best Practices

1. **Always test before promoting**
   ```bash
   # After build succeeds
   ./mql chroot --restore post-build-my-feature-ok
   ./mql chroot
   # Test: dnf install something, check versions, etc.
   # Then promote
   ```

2. **Use descriptive tags**
   - Good: `rust-1.75-bootstrap`, `xfce4-panel-4.18.0`
   - Bad: `test`, `temp`, `asdf`

3. **Keep history clean**
   - Local backups: cleaned by `mql backup archive` (90 days default)
   - Maquiroot history: kept forever (museum style)

4. **Validate unless emergency**
   - Skip validation only when you already tested manually
   - Dry run first if unsure: `dry_run=true`

5. **Document promotion**
   - Comment in PR: "Promoted as post-build-xyz-ok after testing..."
   - Helps others understand what's in `latest/`

## Troubleshooting

### "Backup not found"
Check available backups:
```bash
ls -la ~/maqui-backups/maquilinux-*.tar.xz
# Use exact tag from filename
```

### "Validation failed: DNF not working"
Backup is corrupted or incomplete. Do NOT promote. Debug:
```bash
# Extract and inspect
tar -xzf ~/maqui-backups/maquilinux-...-post-....tar.xz -C /tmp/test
ls /tmp/test/usr/bin/dnf
```

### "Need to rollback maquiroot"
Promote previous stable backup:
```bash
gh workflow run promote.yml -f backup_tag="post-build-previous-good-ok"
```

## Related Workflows

- `build.yml` — Package compilation
- `iso.yml` — ISO generation (uses latest/ from maquiroot)
- `promote.yml` — This workflow
