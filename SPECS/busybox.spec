# SPECS/busybox.spec
# busybox - The Swiss Army Knife of Embedded Linux
#
# Provides a static busybox binary for Maqui Linux initramfs and rescue
# environments. Built with a minimal config targeting:
#   - ash shell (for init scripts)
#   - mount/umount (rootfs mounting)
#   - switch_root/pivot_root (initramfs transition)
#   - static networking (ifconfig/ip/route for live boot)
#   - filesystem tools (mkfs.*, fsck, blkid, losetup for dmsquash)
#   - device management (mdev, modprobe, insmod, rmmod)
#   - compressed root support (zcat, gzip for initramfs unpacking)
#
# Decision: docs/DECISIONS.md 2026-04-02 "busybox for initramfs"

Name:           busybox
Version:        1.36.1
Release:        1.m264%{?dist}
Summary:        The Swiss Army Knife of Embedded Linux

%define debug_package        %{nil}

License:        GPL-2.0-only
URL:            https://busybox.net
Source0:        https://busybox.net/downloads/busybox-%{version}.tar.bz2
# No Source1 needed. The build uses 'make defconfig' as baseline.
# When a custom busybox-config is added to SOURCES/, add here:
# Source1:        busybox-config

# Build dependencies
BuildRequires:  gcc
BuildRequires:  make

%description
BusyBox combines common UNIX utilities into a single small executable,
providing a fairly complete POSIX environment in a small footprint. It is
designed for embedded systems and rescue environments.

This package provides the busybox binary configured for Maqui Linux
initramfs and rescue environments. The binary is statically linked
(CONFIG_STATIC=y) so it works in the early userspace before shared
libraries are available.

This package is required by dracut for live ISO boot (dmsquash-live
module uses busybox for mount, umount, switch_root, and device node
management).

%prep
%setup -q -n busybox-%{version}

%build
# Start from defconfig baseline, enable static linking, build busybox
make defconfig
sed -i 's/^# CONFIG_STATIC is not set$/CONFIG_STATIC=y/' .config
make %{?_smp_mflags} busybox

%install
# Install busybox binary to buildroot
install -m 755 busybox %{buildroot}/bin/busybox

# Create applet symlinks for initramfs use.
# busybox is installed at /bin/busybox; symlinks go in /usr/bin and /sbin.
mkdir -p %{buildroot}/bin %{buildroot}/sbin %{buildroot}/usr/bin %{buildroot}/usr/sbin

# Symlinks in /bin (POSIX utilities)
cd %{buildroot}/bin
ln -sf busybox ash
ln -sf busybox cat
ln -sf busybox cp
ln -sf busybox date
ln -sf busybox dd
ln -sf busybox df
ln -sf busybox dmesg
ln -sf busybox echo
ln -sf busybox false
ln -sf busybox hostname
ln -sf busybox kill
ln -sf busybox ln
ln -sf busybox ls
ln -sf busybox mkdir
ln -sf busybox mknod
ln -sf busybox mount
ln -sf busybox mv
ln -sf busybox od
ln -sf busybox ps
ln -sf busybox pwd
ln -sf busybox rm
ln -sf busybox rmdir
ln -sf busybox sed
ln -sf busybox sh
ln -sf busybox sleep
ln -sf busybox sync
ln -sf busybox true
ln -sf busybox umount
ln -sf busybox uname

# Symlinks in /sbin (system administration, initramfs-critical)
cd %{buildroot}/sbin
ln -sf ../bin/busybox init
ln -sf ../bin/busybox mdev
ln -sf ../bin/busybox switch_root
ln -sf ../bin/busybox pivot_root
ln -sf ../bin/busybox uevent
ln -sf ../bin/busybox modprobe
ln -sf ../bin/busybox insmod
ln -sf ../bin/busybox rmmod
ln -sf ../bin/busybox losetup
ln -sf ../bin/busybox blkid
ln -sf ../bin/busybox blockdev
ln -sf ../bin/busybox fdisk
ln -sf ../bin/busybox fsck
ln -sf ../bin/busybox getty
ln -sf ../bin/busybox halt
ln -sf ../bin/busybox hwclock
ln -sf ../bin/busybox ifconfig
ln -sf ../bin/busybox route
ln -sf ../bin/busybox ip
ln -sf ../bin/busybox mkfs.ext2
ln -sf ../bin/busybox mkfs.vfat
ln -sf ../bin/busybox mkfs
ln -sf ../bin/busybox reboot
ln -sf ../bin/busybox run-init
ln -sf ../bin/busybox vgchange
ln -sf ../bin/busybox vgmknodes

# Symlinks in /usr/bin (userland utilities)
cd %{buildroot}/usr/bin
ln -sf ../../bin/busybox cpio
ln -sf ../../bin/busybox tar
ln -sf ../../bin/busybox gzip
ln -sf ../../bin/busybox zcat
ln -sf ../../bin/busybox bzcat
ln -sf ../../bin/busybox xz
ln -sf ../../bin/busybox vi
ln -sf ../../bin/busybox wget
ln -sf ../../bin/busybox head
ln -sf ../../bin/busybox tail
ln -sf ../../bin/busybox cut
ln -sf ../../bin/busybox sort
ln -sf ../../bin/busybox uniq
ln -sf ../../bin/busybox grep
ln -sf ../../bin/busybox find
ln -sf ../../bin/busybox xargs
ln -sf ../../bin/busybox which
ln -sf ../../bin/busybox whoami
ln -sf ../../bin/busybox id
ln -sf ../../bin/busybox stat
ln -sf ../../bin/busybox touch
ln -sf ../../bin/busybox tr
ln -sf ../../bin/busybox expr
ln -sf ../../bin/busybox test
ln -sf ../../bin/busybox yes
ln -sf ../../bin/busybox printf
ln -sf ../../bin/busybox readlink
ln -sf ../../bin/busybox realpath
ln -sf ../../bin/busybox dirname
ln -sf ../../bin/busybox basename
ln -sf ../../bin/busybox tee
ln -sf ../../bin/busybox wc
ln -sf ../../bin/busybox du
ln -sf ../../bin/busybox free
ln -sf ../../bin/busybox tty

# Symlinks in /usr/sbin (additional system admin)
cd %{buildroot}/usr/sbin
ln -sf ../../bin/busybox poweroff
ln -sf ../../bin/busybox shutdown
ln -sf ../../bin/busybox udhcpc
ln -sf ../../bin/busybox arp

%files
%defattr(-,root,root)
/bin/busybox
/bin/ash
/bin/cat
/bin/cp
/bin/date
/bin/dd
/bin/df
/bin/dmesg
/bin/echo
/bin/false
/bin/hostname
/bin/kill
/bin/ln
/bin/ls
/bin/mkdir
/bin/mknod
/bin/mount
/bin/mv
/bin/od
/bin/ps
/bin/pwd
/bin/rm
/bin/rmdir
/bin/sed
/bin/sh
/bin/sleep
/bin/sync
/bin/true
/bin/umount
/bin/uname
/sbin/init
/sbin/mdev
/sbin/switch_root
/sbin/pivot_root
/sbin/uevent
/sbin/modprobe
/sbin/insmod
/sbin/rmmod
/sbin/losetup
/sbin/blkid
/sbin/blockdev
/sbin/fdisk
/sbin/fsck
/sbin/getty
/sbin/halt
/sbin/hwclock
/sbin/ifconfig
/sbin/route
/sbin/ip
/sbin/mkfs.ext2
/sbin/mkfs.vfat
/sbin/mkfs
/sbin/reboot
/sbin/run-init
/sbin/vgchange
/sbin/vgmknodes
/usr/bin/cpio
/usr/bin/tar
/usr/bin/gzip
/usr/bin/zcat
/usr/bin/bzcat
/usr/bin/xz
/usr/bin/vi
/usr/bin/wget
/usr/bin/head
/usr/bin/tail
/usr/bin/cut
/usr/bin/sort
/usr/bin/uniq
/usr/bin/grep
/usr/bin/find
/usr/bin/xargs
/usr/bin/which
/usr/bin/whoami
/usr/bin/id
/usr/bin/stat
/usr/bin/touch
/usr/bin/tr
/usr/bin/expr
/usr/bin/test
/usr/bin/yes
/usr/bin/printf
/usr/bin/readlink
/usr/bin/realpath
/usr/bin/dirname
/usr/bin/basename
/usr/bin/tee
/usr/bin/wc
/usr/bin/du
/usr/bin/free
/usr/bin/tty
/usr/sbin/poweroff
/usr/sbin/shutdown
/usr/sbin/udhcpc
/usr/sbin/arp

%changelog
* Thu May 02 2026 Maqui Linux Team <team@maqui-linux.org> - 1.36.1-1.m264
- Initial packaging with m264 tag (provenance resolved)
- Provides static busybox binary for initramfs/dracut dmsquash-live
- See docs/DECISIONS.md for build rationale