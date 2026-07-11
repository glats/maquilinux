# Standalone Developer Setup
<!-- stability: mostly-stable | last-reviewed: 2026-07-10 -->

Two paths to set up a Maqui Linux build environment on your own machine.

## Path A: Nix Shell (NixOS / Nix users)

If you have Nix installed, all build tools are provided via the shell:

```bash
git clone https://github.com/glats/maquilinux
cd maquilinux
nix develop
```

This provides: rpm, rpmbuild, createrepo_c, dnf5, xorriso, grub2.

## Path B: Standalone (any Linux distro)

Install build tools via your host package manager:

**Ubuntu/Debian:**
```bash
sudo apt install rpm rpm2cpio createrepo_c dnf5 xorriso grub2
```

**Fedora:**
```bash
sudo dnf install rpm-build createrepo_c dnf5 xorriso grub2
```

**Arch:**
```bash
sudo pacman -S rpm-tools createrepo_c dnf5 xorriso grub
```

## Rootfs Download

After tools are installed, download the latest rootfs tarball:

```bash
curl -O https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz
sudo mkdir -p /mnt/maquilinux
sudo tar -xJf maquilinux-rootfs-latest.tar.xz -C /mnt/maquilinux
```

## Configuration

Set `MQL_ROOTFS` if your rootfs is not at the default path:

```bash
echo "MQL_ROOTFS=/mnt/maquilinux" > mql.local
```

## First Chroot Entry

```bash
mql chroot
```

This mounts the overlay (if not already mounted) and drops into a shell inside
the chroot. The workspace is at `/mnt/workspace`, the local RPM repo at
`/mnt/repo`.

## Push vs Read Boundary

| Direction | You can... | You cannot... |
|-----------|------------|---------------|
| Read | Download rootfs from `maquiroot.glats.org` | -- |
| Read | Install RPMs from `repo.glats.org` via DNF5 | -- |
| Push | Build RPMs in your local chroot | Push RPMs to production repos |
| Push | Push spec changes to GitHub | SSH to thinkcentre.local or rog.local |

As a standalone developer, you operate on the READ side of the boundary. Your
builds are local pre-checks only. Canonical builds happen on thinkcentre.local
and are synced to production repositories.

## Related Docs

- [Build Workflow](../../agent_docs/build-workflow.md) -- spec to RPM pipeline
- [Chroot Lifecycle](../../agent_docs/chroot-lifecycle.md) -- overlay management
- [Backup Flow](../../agent_docs/backup-flow.md) -- backup and restore lifecycle
- [Runner Setup](runner-setup.md) -- self-hosted GitHub Actions runner
