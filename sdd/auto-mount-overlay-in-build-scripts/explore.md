# Exploration: Auto-mount overlay in build scripts

## Current State

### How overlay mounting works today

The Maqui Linux development system uses an overlayfs-based chroot:

```
/mnt/maquilinux/
├── base/            ← immutable rootfs (overlay lowerdir)
├── layers/
│   ├── upper/       ← current changes (overlay upperdir)
│   └── work/        ← overlay workdir
├── merged/          ← unified view (chroot target)
└── repo/            ← local RPM repo
```

**Mount command** (manual, user runs once):
```bash
sudo mount -t overlay overlay \
  -o lowerdir=/mnt/maquilinux/base,\
     upperdir=/mnt/maquilinux/layers/upper,\
     workdir=/mnt/maquilinux/layers/work \
  /mnt/maquilinux/merged
```

**After mount**, additional bind-mounts are needed:
- `$MQL_DISK/merged/workspace` ← bind-mounted to project root
- `$MQL_DISK/merged/proc`, `/dev`, `/sys`, `/run`, `/dev/pts`, `/dev/shm` ← virtual FS
- `$MQL_DISK/merged/etc/resolv.conf` ← network config

### Where mount logic lives

**There is NO centralized mount/unmount function.** The architecture is fragmented:

| Script | Mount logic |
|--------|------------|
| `mql` CLI (line 275) | Sources `lib/chroot.sh` and calls `mql_chroot "$@"` |
| `lib/chroot.sh` | **DOES NOT EXIST** — referenced in `mql` (line 275) and `DEVELOPMENT-SYSTEM-PLAN.md` (line 105) but never created |
| `scripts/build-spec.sh` | Has `verify_chroot()` — checks mount, prints error with manual mount command |
| `scripts/build-chain.sh` | No mount check at all — calls `build-spec.sh` and `install_built_rpms()` which use `chroot` directly |
| `scripts/run-in-chroot.sh` | Has `verify_chroot()` — same pattern: check + error + manual command |
| `scripts/enter-chroot.sh` | Mounts virtual FS (proc, dev, sys, etc.) but assumes overlay is already up |
| `scripts/enter-chroot-build.sh` | Mounts virtual FS + workspace bind-mount, same assumption |
| `scripts/install-spec.sh` | No mount check — assumes `$MQL_DISK/merged` exists |

**Key finding**: The `mql` CLI's `chroot` subcommand (line 275 of `mql`) sources `lib/chroot.sh` which does not exist. This means `mql chroot` will fail with a sourcing error. The planned library file was never implemented.

### The gap: Why builds fail

When a user runs `./scripts/build-spec.sh bash` without the overlay mounted:

1. `verify_chroot()` runs `mountpoint -q "$CHROOT_TARGET"` → fails
2. Prints: `ERROR: Overlay not mounted at /mnt/maquilinux/merged`
3. Prints the manual mount command
4. Exits with code 1

There is zero auto-mount logic. The user must:
1. Mount the disk (`sudo mount /dev/sdd1 /mnt/maquilinux`)
2. Mount the overlay (manual `mount -t overlay ...`)
3. Create workspace dir and bind-mount
4. Mount virtual filesystems
5. Only then can they build

This is a significant user experience gap — especially for CI/CD and new developers.

## Affected Areas

- `scripts/build-spec.sh` — has `verify_chroot()` that only checks, never mounts
- `scripts/build-chain.sh` — orchestrator that calls `build-spec.sh`; no mount awareness
- `scripts/run-in-chroot.sh` — same verify-only pattern
- `scripts/install-spec.sh` — no mount verification at all
- `mql` (main CLI) — references non-existent `lib/chroot.sh`
- `lib/common.sh` — has `is_mounted()` and `safe_umount()` but no mount function
- `lib/build.sh` — thin wrapper around `build-spec.sh`, no mount logic

## Approaches

### 1. Shared mount function in lib/common.sh

Create `mount_overlay()`, `mount_workspace()`, `mount_virtual_fs()`, and `unmount_all()` functions in `lib/common.sh`. Every build script sources `common.sh` and calls `ensure_mounted()` which checks + mounts as needed.

**Pros:**
- Single source of truth for mount logic
- All scripts benefit (build-spec, build-chain, run-in-chroot, install-spec)
- Follows existing pattern (common.sh already has `is_mounted()`, `safe_umount()`)
- Easy to test in isolation

**Cons:**
- Still requires scripts to explicitly call the function
- `mql` CLI already sources common.sh, so `mql build` would benefit immediately
- Build scripts need to add `source "$TOPDIR/lib/common.sh"` (they currently don't)

**Effort:** Low — add ~50 lines to common.sh, update 3-4 scripts to source it

### 2. Auto-mount in build-spec.sh verify_chroot()

Modify the existing `verify_chroot()` in `scripts/build-spec.sh` to not just check but also mount if missing. Add the mount logic inline.

**Pros:**
- Minimal change — just extend existing function
- No refactoring of other scripts needed
- Direct fix for the most commonly used script

**Cons:**
- Only fixes `build-spec.sh` — `build-chain.sh` and `run-in-chroot.sh` still fail
- Duplicates mount logic if other scripts are updated
- `build-spec.sh` doesn't source common.sh, so no shared library benefit
- Tight coupling: build script knows too much about mount mechanics

**Effort:** Low — ~20 lines in one function

### 3. Fix lib/chroot.sh as the canonical mount/unmount library

Create the missing `lib/chroot.sh` with full lifecycle: `chroot_mount()`, `chroot_unmount()`, `chroot_verify()`, `chroot_enter()`. This becomes the single library for all chroot operations, used by both `mql chroot` and build scripts.

**Pros:**
- Fulfills the architecture planned in DEVELOPMENT-SYSTEM-PLAN.md
- `mql chroot` actually works as documented
- Build scripts can call `chroot_verify()` or `chroot_mount()` from the library
- Clean separation: chroot logic in chroot.sh, build logic in build-spec.sh
- Can add `--auto-mount` flag to `mql chroot`

**Cons:**
- Requires build scripts to source the library (currently they don't)
- More files to maintain
- Build scripts currently use `exec chroot` — would need refactoring to use library functions

**Effort:** Medium — create new file (~150 lines), update mql CLI, update build scripts to use library

### 4. NixOS systemd mount unit

Create a NixOS systemd mount unit that auto-mounts the overlay when the disk is mounted. This would be transparent to the user — the overlay appears automatically.

**Pros:**
- Fully transparent — no script changes needed
- Works for ALL tools (mql, build scripts, manual chroot, anything)
- System-level reliability

**Cons:**
- Only works on NixOS — not portable (violates "Nix is optional" principle)
- Overlay mount on boot is risky — what if base/ isn't set up yet?
- Requires the disk to be mounted first (circular dependency)
- Overly complex for a development workflow that's inherently interactive
- Would need `wants=` and `Before=` ordering with the disk mount

**Effort:** High — NixOS module, edge case handling, not portable

### 5. Wrapper script approach

Create a `scripts/chroot-setup.sh` that does all mount/unmount, and every build script calls it at the top. This is separate from common.sh since it's root-only.

**Pros:**
- Clear ownership: setup vs build separation
- Can be called by CI/CD pipelines explicitly
- No dependency on common.sh (which has non-root helpers)

**Cons:**
- Another file to maintain
- Similar to approach 1 but more fragmented
- Doesn't fix `mql chroot` which needs `lib/chroot.sh`

**Effort:** Low-Medium

## Recommendation

**Approach 3 (fix lib/chroot.sh) + Approach 1 (shared functions in common.sh)** combined.

Rationale:
1. The architecture already planned for `lib/chroot.sh` — it was never implemented. This is a gap, not a design question.
2. `mql chroot` currently cannot work because it sources a non-existent file. This is a bug.
3. Build scripts should use the library rather than duplicating mount logic.
4. `lib/common.sh` already has `is_mounted()` and `safe_umount()` — add `ensure_overlay_mounted()` there as a convenience function that build scripts can call.

### Specific implementation plan:

1. **Create `lib/chroot.sh`** with:
   - `chroot_mount()` — mounts overlay + workspace + virtual FS
   - `chroot_unmount()` — unmounts in reverse order
   - `chroot_verify()` — checks everything is mounted (current verify_chroot logic)
   - `chroot_enter()` — enters interactive chroot
   - `chroot_exec()` — runs a single command and exits

2. **Extend `lib/common.sh`** with:
   - `ensure_overlay_mounted()` — calls `chroot_verify()` or `chroot_mount()` as needed
   - Make it idempotent (no-op if already mounted)

3. **Update `scripts/build-spec.sh`**:
   - Source `lib/common.sh` (or `lib/chroot.sh`)
   - Replace inline `verify_chroot()` with library call
   - Add `--no-mount` flag for CI/CD where mount is done externally

4. **Update `scripts/build-chain.sh`**:
   - Source `lib/common.sh`
   - Call `ensure_overlay_mounted()` at the top of `main()`

5. **Update `mql` CLI**:
   - `mql chroot` now actually works via `lib/chroot.sh`
   - `mql build` delegates to `scripts/build-spec.sh` which auto-mounts

### Why not just approach 2?

Approach 2 (inline fix in build-spec.sh) is the quickest single-file fix, but it leaves the architecture broken: `mql chroot` doesn't work, `build-chain.sh` has no mount awareness, and `install-spec.sh` has no mount check. The planned `lib/chroot.sh` is referenced in the architecture document and the CLI — it needs to exist.

### Why not approach 4 (NixOS)?

The project explicitly states "Nix is optional, not required." A NixOS-only solution would create a two-tier system where NixOS users get transparent mounting and everyone else gets the current pain. This is the opposite of what the user wants.

## Risks

- **Idempotency**: `chroot_mount()` must handle "already mounted" gracefully (check mountpoint first)
- **Error messages**: Must be actionable — show exact commands, not just "mount failed"
- **Privilege escalation**: All mount operations require root — scripts need clear sudo handling
- **Cleanup on error**: If mount succeeds but chroot fails, unmount must still happen
- **`mql chroot` currently broken**: Fixing this is a prerequisite — the file `lib/chroot.sh` doesn't exist

## Ready for Proposal

**Yes.** The exploration is complete. The key finding is that `lib/chroot.sh` was planned but never implemented, leaving `mql chroot` non-functional and build scripts with duplicated, verify-only mount checks. The recommendation is to create `lib/chroot.sh` as the canonical mount/unmount library and have all build scripts use it.
