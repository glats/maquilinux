# Rootfs Backup System (Museum Style)

**Philosophy:** Never delete backups. Archive to cold storage. Each backup captures a moment in the distribution's evolution.

## Quick Commands

```bash
# Create backup
cd ~/Work/maquilinux
./mql backup create pre-rust-bootstrap

# List backups
./mql backup list
./mql backup museum  # hot + cold storage

# Restore backup
./mql backup restore maquilinux-20260418-191000-pre-rust.tar.xz

# Archive old backups (moves, doesn't delete)
./mql backup archive 90  # 90+ days to cold storage
```

## Storage Layout

```
~/maqui-backups/              # Hot storage (fast access)
  maquilinux-YYYYMMDD-HHMMSS-<tag>.tar.xz
  maquilinux-YYYYMMDD-HHMMSS-<tag>.tar.xz.meta
  
~/maqui-archive/              # Cold storage (historical)
  maquilinux-2026-01-*.tar.xz
  .metadata/
```

## Backup in CI/CD

Backups run automatically at the start of risky workflows (e.g., `bootstrap-rust.yml`):

```yaml
- name: Backup rootfs before changes
  run: ./mql backup create pre-<job>-$GITHUB_RUN_ID
```

## Metadata Format

Each `.meta` file contains:
- `timestamp` - ISO 8601 format
- `git_commit` - Git hash at backup time
- `git_branch` - Active branch
- `packages_count` - Number of RPMs in rootfs
- `tag` - Descriptive tag (e.g., "pre-rust-bootstrap")

## Manual Backup (Emergency)

```bash
# Direct tar (when mql not available)
cd /run/media/glats/maquilinux/base
tar -cJpf ~/maqui-backups/maquilinux-$(date +%Y%m%d-%H%M%S)-manual.tar.xz .
```

## Restoration

**⚠️ Destructive operation - will overwrite current rootfs**

```bash
# 1. Unmount overlay first
sudo umount -l /mnt/maquilinux/merged

# 2. Restore
./mql backup restore <backup-name>

# 3. Remount overlay
./mql chroot --mount
```

## Archive vs Delete

- **Archive** (`mql backup archive`): Moves to cold storage, keeps history
- **Never delete**: Philosophy is museum-style preservation
- Cold storage can be on external disk, NFS, etc.
