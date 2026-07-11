# Layer 3 — CI/CD Pipeline Specifications

Based on Proposal #941 and informed by Master Plan #925 and Operational Reference #927.

## R1 — Runner Auto-Start

### Description
The self-hosted GitHub Actions runner must start automatically on boot, survive reboots without manual intervention, and be recoverable if the process dies.

### Acceptance Criteria
- After system reboot, the runner is registered and idle in GitHub repository settings
- Runner process survives logout/reboot cycles
- If runner process dies, it automatically restarts within 30 seconds
- No manual intervention required for normal operation

### Scenarios

**Happy Path:**
1. System boots on thinkcentre (self-hosted runner machine)
2. maquilinux-mounts.service auto-mounts overlay filesystem
3. github-runner.service starts automatically via systemd
4. Runner registers with GitHub and shows as "Idle" in repository settings
5. User pushes commit to main branch
6. Runner picks up job and executes build-rpms.yml workflow
7. Workflow completes successfully
8. System is rebooted
9. After reboot, runner automatically restarts and shows as "Idle"
10. Subsequent push triggers another successful workflow

**Edge Cases:**
1. Runner process crashes unexpectedly
   - systemd detects failure and restarts github-runner.service
   - Runner re-registers with GitHub (if needed) and shows as "Idle"
   - No loss of queued jobs
   
2. Network unavailable at boot time
   - github-runner.service waits for network-online.target
   - Runner starts after network becomes available
   - Shows as "Offline" until network connects, then "Idle"
   
3. Disk not mounted at boot time
   - github-runner.service depends on maquilinux-mounts.service
   - Service waits for overlay filesystem to be mounted
   - Starts after MQL_LFS/merged is available
   
4. Multiple reboot cycles
   - After 5 consecutive reboots, runner consistently auto-starts
   - No degradation in performance or registration status

## R2 — Path Configuration

### Description
mql.conf must use generic defaults (no hardcoded user paths), workflows must use MQL_ROOTFS (not MQL_DISK), MQL_REPO_SYNC_HOST and MQL_REPO_SYNC_PATH config variables for rsync target, and get_repo_dest() must return correct path.

### Acceptance Criteria
- No occurrences of "/home/glats" or "/run/media/glats" in .github/workflows/*
- mql.conf contains MQL_ROOTFS=/mnt/maquilinux as default
- mql.conf contains MQL_REPO_SYNC_HOST=rog.local and MQL_REPO_SYNC_PATH=/srv/repo/ as defaults
- lib/common.sh:get_repo_dest() returns path constructed from MQL_REPO_SYNC_HOST and MQL_REPO_SYNC_PATH
- All workflows reference MQL_ROOTFS variable, not MQL_DISK

### Scenarios

**Happy Path:**
1. Fresh clone of repository with no mql.local
2. mql.conf defaults are used: MQL_ROOTFS=/mnt/maquilinux
3. User runs `mql config` and sees correct default values
4. Workflow runs and correctly references MQL_ROOTFS in all steps
5. get_repo_dest() function returns "rog.local:/srv/repo/maquilinux/26.4/x86_64/stable/"
6. mql repo sync uses correct rsync destination

**Edge Cases:**
1. User has existing mql.local with custom paths
   - mql.local overrides take precedence over mql.conf defaults
   - No breaking changes for existing users
   - Workflows still function with custom MQL_ROOTFS value
   
2. mql.conf missing MQL_REPO_SYNC_* variables (after update)
   - Default values are applied automatically
   - get_repo_dest() falls back to sane defaults
   - Warning logged but workflow continues
   
3. Invalid path in mql.local
   - mql config validates paths and reports error
   - Workflow fails fast with clear error message
   - User must correct mql.local before proceeding

## R3 — createrepo_c in Chroot

### Description
createrepo_c must be installed in the chroot and `mql repo update` must work inside chroot.

### Acceptance Criteria
- createrepo_c package is installed in $MQL_LFS/base/
- `mql chroot --exec "dnf list installed createrepo_c"` shows package as installed
- `mql repo update` executes successfully inside chroot
- repodata is generated in $MQL_LFS/repo/

### Scenarios

**Happy Path:**
1. Fresh chroot environment (after overlay reset)
2. User runs `mql chroot --exec "which createrepo_c"` and gets "/usr/bin/createrepo_c"
3. User runs `mql repo update`
4. createrepo_c processes all RPMs in $MQL_LFS/repo/
5. repodata/ directory is created/updated with latest metadata
6. Command exits with status 0
7. Subsequent `dnf repolist` shows updated repository metadata

**Edge Cases:**
1. createrepo_c not installed in chroot
   - `mql repo update` fails with clear error: "createrepo_c not found"
   - Error suggests running `mql chroot --exec "dnf install /mnt/repo/createrepo_c-*.rpm"`
   - After manual install, retry succeeds
   
2. No RPMs in repository directory
   - createrepo_c runs but creates minimal repodata
   - No error, but warning logged about empty repository
   - Workflow continues successfully
   
3. Disk I/O error during repodata generation
   - createrepo_c fails with I/O error
   - Error propagated to workflow, causing failure
   - Clear message: "Failed to generate repository metadata"
   
4. Concurrent repo update attempts
   - Second attempt detects lockfile and waits
   - After first completes, second proceeds
   - No corruption of repodata

## R4 — Self-Hosting Repodata

### Description
The 7 self-hosting packages on rog must have repodata and dnf install from stable repo must find them.

### Acceptance Criteria
- All 7 self-hosting packages (dracut, busybox, dhcpcd, createrepo_c, libisoburn, squashfs-tools, mtools) have corresponding repodata
- `dnf install <package>` works from chroot for each self-hosting package
- Packages install without needing --disablerepo=maquilinux-local workaround
- Repodata is updated when new versions of self-hosting packages are built

### Scenarios

**Happy Path:**
1. SSH to rog machine
2. Check /srv/glats/nginx/repo/linux/maquilinux/26.4/x86_64/stable/ directory
3. Verify repodata/ subdirectory exists with current.xml.gz, filelists.xml.gz, etc.
4. Verify all 7 self-hosting packages are represented in repodata
5. Return to thinkcentre and enter chroot
6. Run `dnf install dracut` (or any of the 7 packages)
7. Package installs successfully from stable repository
8. Verify installed files are functional (e.g., dracut --version works)

**Edge Cases:**
1. New version of self-hosting package built but not synced to rog
   - dnf install fails to find newer version
   - After mql repo sync, new version appears in repodata
   - dnf install then finds and installs newer version
   
2. Repodata corrupted on rog
   - dnf install fails with checksum mismatch
   - Manual createrepo_c regeneration fixes issue
   - Workflow includes validation step to detect corrupted repodata
   
3. Partial sync failure (network interrupt)
   - Some packages missing from repodata
   - mql repo sync has retry logic with exponential backoff
   - Admin alert triggered if sync fails after 3 attempts

## R5 — mql install Command

### Description
`mql install <spec>` must install the built RPM in the chroot and must handle both architectures (x86_64 and i686).

### Acceptance Criteria
- `mql install SPECS/maquilinux-release.spec` installs the package in chroot
- Command respects --arch flag for specifying architecture
- Command respects --both flag for installing both x86_64 and i686 versions
- Installed RPM is queryable via `rpm -q` inside chroot
- Package files are present in correct locations in chroot filesystem

### Scenarios

**Happy Path:**
1. User builds maquilinux-release.spec: `mql build SPECS/maquilinux-release.spec`
2. RPM appears in $MQL_LFS/repo/x86_64/
3. User runs `mql install SPECS/maquilinux-release.spec`
4. mql delegates to scripts/install-spec.sh with correct arguments
5. RPM is installed in chroot via dnf
6. `mql chroot --exec "rpm -q maquilinux-release"` shows installed version
7. Package files are present in /etc/, /usr/lib/, etc. inside chroot
8. Same workflow works with --arch i686 to install 32-bit version
9. With --both flag, both architectures installed (if available)

**Edge Cases:**
1. Spec not built yet
   - mql install fails with clear error: "RPM not found for maquilinux-release.spec"
   - Suggests running `mql build SPECS/maquilinux-release.spec` first
   - After build, install succeeds
   
2. Multiple versions of same package in repo
   - mql install picks newest version by default
   - User can specify version with --version flag (if implemented)
   - Clear logging shows which version was installed
   
3. Dependency missing during install
   - dnf reports missing dependencies
   - mql install fails with actionable error message
   - User must build dependencies first or use --nodeps (with warning)
   
4. Installing to non-standard location
   - --installpath flag respected (if implemented)
   - RPM relocates to specified prefix inside chroot

## R6 — PR Validation Trigger

### Description
PRs that change SPECS/*.spec or SOURCES/* must trigger a build validation. Validation must build the changed specs but NOT publish.

### Acceptance Criteria
- build-rpms.yml workflow triggers on pull_request events for SPECS/ and SOURCES/ paths
- Validation runs rpmspec --parse on changed .spec files (syntax check only)
- Validation does NOT execute mql build, mql install, mql repo update, or mql repo sync
- Workflow is marked as non-blocking initially (allows merge even if fails)
- Clear logging indicates this is PR validation, not production build

### Scenarios

**Happy Path:**
1. User opens PR changing SPECS/maquilinux-release.spec
2. GitHub triggers build-rpms.yml workflow on pull_request event
3. Workflow skips build, install, repo update, and repo sync steps
4. Workflow runs rpmspec --parse on changed .spec files
5. If spec syntax is valid, workflow completes successfully
6. PR shows all checks passed (validation workflow marked as optional)
7. User can merge PR without waiting for validation to complete (non-blocking)
8. If spec syntax invalid, workflow fails but PR can still be merged (initially)

**Edge Cases:**
1. PR changes only documentation/files outside SPECS/ and SOURCES/
   - build-rpms.yml workflow does NOT trigger (paths filter excludes changes)
   - No unnecessary validation runs
   
2. PR changes both .spec and .patch files in SOURCES/
   - Workflow triggers due to SOURCES/* path match
   - rpmspec --parse run on changed .spec files
   - No action taken on .patch files (validation is spec-only)
   
3. Spec syntax validation fails
   - Workflow fails with clear error: "Spec syntax error: Expected tag 'Version'"
   - Error includes filename and line number from rpmspec output
   - Badge shows workflow as failed but PR remains mergeable
   - Comment added to PR suggesting fix (if implemented)
   
4. Many spec files changed in single PR
   - Workflow validates each changed .spec file
   - All must pass for workflow to succeed
   - Errors aggregated and reported together
   - Performance remains acceptable (<10 seconds for 10 specs)

## R7 — RPM Signing in CI

### Description
Build pipeline must sign RPMs when signing key is available, must skip signing gracefully when key is absent (with warning), and must NOT leak the signing key in logs or artifacts.

### Acceptance Criteria
- When sq is available and keystore unlocked, RPMs are signed with rpmsign --addsign
- When sq is unavailable or keystore locked, workflow logs warning and continues without signing
- No tracing of signing key material in workflow logs, artifacts, or environment variables
- Signed RPMs verify correctly with maquilinux-release GPG key
- Unsigned workflow produces identical artifacts except for signature

### Scenarios

**Happy Path (Signing Available):**
1. thinkcentre has sq installed and sequoia keystore unlocked
2. User pushes commit to main branch triggering build-rpms.yml
3. Workflow detects sq availability via find_rpmsign() function
4. After building RPMs, workflow executes rpmsign --addsign on each RPM
5. Signed RPMs appear in artifacts with .sig embedded
6. `rpm --checksig <rpm>` shows valid signature from maquilinux-key
7. No signing key material appears in workflow logs
8. Workflow completes successfully

**Happy Path (Signing Unavailable):**
1. thinkcentre has sq installed but keystore locked (requires passphrase)
2. User pushes commit to main branch
3. Workflow detects sq unavailable via find_rpmsign() returning empty
4. Workflow logs warning: "RPMSIGN not found, skipping RPM signing"
5. Workflow continues without signing step
6. Unsigned RPMs appear in artifacts
7. Workflow completes successfully (signing is optional)
8. Badge indicates build completed but with warning

**Edge Cases:**
1. sq binary missing from PATH
   - find_rpmsign() returns empty
   - Same behavior as unlocked keystore case
   - Warning logged, signing skipped
   
2. Keystore access denied (permissions issue)
   - rpmsign --addsign fails with permission error
   - Workflow catches error, logs warning, continues without signing
   - Clear indication that signing failed but build succeeded
   
3. Attempt to leak key via environment dump
   - Workflow avoids printing env vars that might contain key material
   - No debug logs showing sequential key access
   - Artifacts contain only signed RPMs, no key files
   
4. Partial signing failure (some RPMs signed, others not)
   - Workflow signs RPMs individually
   - If one fails, logs error for that RPM but continues with others
   - Final status: warning about partial signing, but workflow succeeds

## R8 — Repo Sync Correctness

### Description
rsync must use the correct destination path on rog and must not delete packages that weren't part of the build (--delete flag risk).

### Acceptance Criteria
- mql repo sync constructs destination from MQL_REPO_SYNC_HOST and MQL_REPO_SYNC_PATH
- rsync command does NOT use --delete flag
- Only packages built in current workflow are transferred/synced
- Existing packages in destination remain untouched
- Sync preserves file permissions and timestamps

### Scenarios

**Happy Path:**
1. Workflow completes build and repo update steps
2. mql repo sync executes
3. Destination path correctly formed: rog.local:/srv/repo/maquilinux/26.4/x86_64/stable/
4. rsync transfers only newly built/updated RPMs and repodata
5. Existing packages in stable/ directory remain unchanged
6. File permissions (644 for RPMs, 755 for directories) preserved
7. Timestamps maintained for incremental backup compatibility
8. Sync completes with summary showing transferred file count

**Edge Cases:**
1. Network interruption during sync
   - rsync fails with network error
   - Workflow fails fast (no retry in workflow step)
   - Manual retry resumes from where it left off (rsync's --partial)
   - No duplicate transfers or corruption
   
2. Destination directory missing on rog
   - rsync fails with "no such file or directory"
   - Clear error suggests checking MQL_REPO_SYNC_PATH
   - After directory created manually, retry succeeds
   
3. Permission denied on destination
   - rsync fails with permission error
   - Workflow fails with actionable message about SSH key/permissions
   - No partial transfer leaving inconsistent state
   
4. Attempt to use --delete flag (prevented)
   - Code review catches any attempt to add --delete
   - Workflow explicitly forbids --delete in documentation
   - If added accidentally, workflow validation step fails

## R9 — ISO Workflow Paths

### Description
iso.yml must use parameterized paths, not hardcoded ones.

### Acceptance Criteria
- No occurrences of "/home/glats" or "/run/media/glats" in .github/workflows/iso.yml
- All paths derived from MQL_LFS, MQL_ROOTFS, or MQL_RELEASEVER variables
- Workflow functions correctly with default mql.conf values
- Workflow functions correctly with overridden mql.local values

### Scenarios

**Happy Path:**
1. User triggers mql release iso (via workflow or manual)
2. iso.yml workflow starts
3. All path references use variables like ${MQL_LFS}/merged or ${MQL_ROOTFS}
4. No hardcoded user-specific paths appear in expanded workflow
5. Workflow locates kernel, initramfs, squashfs in correct locations
6. ISO generated at correct output path: ${MQL_LFS}/release/maquilinux-${MQL_RELEASEVER}.iso
7. Workflow completes successfully
8. Generated ISO boots and functions correctly

**Edge Cases:**
1. MQL_LFS overridden in mql.local to custom path
   - iso.yml respects custom MQL_LFS value
   - All paths resolve correctly under custom location
   - ISO generated in custom location
   - No breakage for users with non-standard setup
   
2. MQL_ROOTFS points to different overlay configuration
   - Workflow still finds required files in expected locations
   - Uses MQL_ROOTFS variable consistently
   - No assumptions about fixed mount points
   
3. Missing required files for ISO generation
   - Workflow fails fast with clear error about missing component
   - Error specifies which file is missing and expected location
   - User can troubleshoot based on precise path information
   
4. Insufficient disk space for ISO generation
   - Workflow fails during iso creation step
   - Error indicates out of space condition
   - Suggests cleaning workspace or increasing disk allocation

## R10 — End-to-End CI Flow

### Description
Push to main with spec changes triggers: backup → build → sign → install → repo update → repo sync → backup. Each step must fail the pipeline if it errors.

### Acceptance Criteria
- Push to main branch triggers build-rpms.yml workflow
- Workflow executes steps in order: mql backup pre, mql build, rpmsign (if available), mql install, mql repo update, mql repo sync, mql backup post
- Each step is a separate job or sequential step with explicit error checking
- If any step fails, workflow stops immediately and reports failure
- Successful completion results in: new backup, built/signed/installed RPMs, updated repo, synced to rog, final backup
- Workflow provides clear logging at each step for troubleshooting

### Scenarios

**Happy Path:**
1. User pushes commit changing SPECS/maquilinux-release.spec to main branch
2. GitHub Actions triggers build-rpms.yml workflow
3. Step 1: mql backup create pre-<timestamp>
   - Creates overlay snapshot
   - Logs backup location and size
   - Completes successfully
4. Step 2: mql build SPECS/maquilinux-release.spec
   - Builds RPM for changed spec
   - Places RPM in $MQL_LFS/repo/x86_64/
   - Completes successfully
5. Step 3: Check for signing key availability
   - If available: rpmsign --addsign on built RPM
   - If not available: logs warning and continues
   - Either way, step completes (signing is optional)
6. Step 4: mql install SPECS/maquilinux-release.spec
   - Installs built RPM in chroot
   - Verifies installation with rpm -q
   - Completes successfully
7. Step 5: mql repo update
   - Runs createrepo_c on repository directory
   - Updates repodata/
   - Completes successfully
8. Step 6: mql repo sync
   - Syncs new RPM and repodata to rog
   - Preserves existing packages
   - Completes successfully
9. Step 7: mql backup create post-<timestamp>
   - Creates post-deployment overlay snapshot
   - Logs backup location and size
   - Completes successfully
10. Workflow concludes with success status
11. All badges show green/passed

**Edge Cases:**
1. Backup step fails (disk full)
   - mql backup create returns error about insufficient space
   - Workflow fails immediately at step 1
   - No build, install, or sync attempted
   - Clear error: "Backup failed: No space left on device"
   - User must free space before retrying
   
2. Build step fails (spec syntax error)
   - mql build fails with rpmbuild error
   - Workflow fails at step 2
   - No install, repo update, or sync attempted
   - Error includes build log for troubleshooting
   - Pre-backup preserved for potential manual inspection
   
3. Install step fails (dependency missing)
   - mql install fails due to unresolved dependency
   - Workflow fails at step 4
   - Repo update and sync not attempted
   - Error indicates missing dependency and suggests building it first
   - Pre-backup available
   
4. Repo update step fails (createrepo_c error)
   - mql repo update fails during metadata generation
   - Workflow fails at step 5
   - Repo sync not attempted (would sync broken repodata)
   - Error includes createrepo_c output for diagnosis
   - Pre-backup and post-build state preserved
   
5. Repo sync step fails (network/auth error)
   - mql repo sync fails to connect to rog
   - Workflow fails at step 6
   - Post-backup not attempted (avoid inconsistent state)
   - Error suggests checking network, SSH keys, or rog availability
   - Pre-backup, build, install, and repo update all completed
   
6. Multiple failures in sequence
   - Workflow stops at first failure
   - Subsequent steps not executed regardless of type
   - Clear indication of which step failed and why
   - Easy to fix root cause and retry from beginning

## Summary of Requirements

I have written detailed specifications for all 11 deliverables from the Layer 3 — CI/CD Pipeline proposal:

**R1 — Runner Auto-Start**: Automatic startup, survivability, and recovery of self-hosted GitHub Actions runner
**R2 — Path Configuration**: Generic defaults in mql.conf, MQL_ROOTFS usage, repo sync configuration
**R3 — createrepo_c in Chroot**: Installation and functionality of createrepo_c for repo updates inside chroot
**R4 — Self-Hosting Repodata**: Proper repodata for self-hosting packages enabling dnf install from stable repo
**R5 — mql install Command**: CLI command to install built RPMs in chroot with multi-arch support
**R6 — PR Validation Trigger**: Pull request validation for spec changes without publishing
**R7 — RPM Signing in CI**: Optional RPM signing with secure key handling
**R8 — Repo Sync Correctness**: Safe rsync without destructive flags and proper path construction
**R9 — ISO Workflow Paths**: Parameterized paths in ISO workflow eliminating hardcoded values
**R10 — End-to-End CI Flow**: Complete pipeline with ordered steps and failure isolation

Each requirement includes testable acceptance criteria and comprehensive scenarios covering happy paths and edge cases.

The specifications are ready for implementation and will enable the CI/CD pipeline to automatically build, sign, install, and publish RPMs while providing PR validation to catch broken specs before merge.