Summary:    Maqui Linux filesystem layout
Name:       filesystem
Version:    26.4
Release:    1.m264
License:    LicenseRef-FREE
Group:      System/Base
URL:        https://maquilinux.org
BuildArch:  noarch

# Conflicts signals that maquilinux.spec must be updated to version 2+
# (removing directory ownership) before both packages can coexist.
Conflicts: maquilinux < 2-1.m264

# Built inside a minimal Maqui Linux chroot without find-debuginfo or brp helpers.
# Disable automatic debuginfo and BRP post scripts for consistent packaging.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%description
This package installs the core FHS directory structure and required symlinks
for Maqui Linux. It defines the fundamental filesystem hierarchy including
standard directory paths and their permissions. Other packages should
Require: filesystem to ensure the directory structure is present.

%prep
%build
%install

# root directories
install -vdm 755 %{buildroot}/{boot,dev,etc,home,media,mnt,opt,proc,run,srv,sys,usr,var}
install -vdm 700 %{buildroot}/root
install -vdm 1777 %{buildroot}/tmp
# etc directories
install -vdm 755 %{buildroot}/etc/{ld.so.conf.d,opt,profile.d,skel,sysconfig}
install -vdm 755 %{buildroot}/etc/yum.repos.d
install -vdm 755 %{buildroot}/etc/dnf/vars
# media directories
install -vdm 755 %{buildroot}/media/{floppy,cdrom}
# usr directories
install -vdm 755 %{buildroot}/usr/{,local/}{bin,include,lib,sbin,src}
install -vdm 755 %{buildroot}/usr/lib/i386-linux-gnu
install -vdm 755 %{buildroot}/usr/lib/x86_64-linux-gnu
install -vdm 755 %{buildroot}/usr/lib/locale

# Multiarch symlinks: /usr/lib32 points to /usr/lib/i386-linux-gnu
# This ensures that software installing 32-bit libs in /usr/lib32 automatically
# ends up in the correct Debian-style multiarch directory.
ln -sv i386-linux-gnu %{buildroot}/usr/lib/lib32
ln -sv /usr/lib/i386-linux-gnu %{buildroot}/usr/lib32

install -vdm 755 %{buildroot}/usr/{,local/}share/{color,dict,doc,info,locale,man}
install -vdm 755 %{buildroot}/usr/{,local/}share/{misc,terminfo,zoneinfo}
install -vdm 755 %{buildroot}/usr/libexec
install -vdm 755 %{buildroot}/usr/{,local/}share/man/man{1..8}
# var directories
install -vdm 755 %{buildroot}/var/{log,spool}
install -vdm 1777 %{buildroot}/var/tmp
install -vdm 755 %{buildroot}/var/spool/mail
install -vdm 755 %{buildroot}/var/opt
install -vdm 755 %{buildroot}/var/cache
install -vdm 755 %{buildroot}/var/lib
install -vdm 755 %{buildroot}/var/lib/{misc,rpm}
install -vdm 755 %{buildroot}/var/local
# symlinks
ln -sv usr/bin %{buildroot}/bin
ln -sv usr/lib %{buildroot}/lib
ln -sv usr/sbin %{buildroot}/sbin
# /usr/lib64 compatibility symlink for packages using Fedora-style %{_libdir}
ln -sv x86_64-linux-gnu %{buildroot}/usr/lib64
# /lib64 symlink for FHS compatibility (points into /usr/lib hierarchy)
ln -sv usr/lib/x86_64-linux-gnu %{buildroot}/lib64
ln -sv ../run %{buildroot}/var/run
ln -sv ../run/lock %{buildroot}/var/lock
ln -sv spool/mail %{buildroot}/var/mail
ln -sv ../proc/self/mounts %{buildroot}/etc/mtab

%files
%defattr(-,root,root)

# Special permission directories
%attr(750,root,root)	/root
%attr(1777,root,root)	/tmp
%attr(1777,root,root)	/var/tmp

# Core directories
%dir /boot
%dir /dev
%dir /etc
%dir /etc/ld.so.conf.d
%dir /etc/opt
%dir /etc/profile.d
%dir /etc/skel
%dir /etc/sysconfig
%dir /etc/dnf
%dir /etc/dnf/vars
%dir /etc/yum.repos.d
%dir /home
%dir /media
%dir /media/cdrom
%dir /media/floppy
%dir /mnt
%dir /opt
%dir /proc
%dir /run
%dir /srv
%dir /sys
%dir /usr
%dir /usr/bin
%dir /usr/include
%dir /usr/lib
%dir /usr/lib/i386-linux-gnu
%dir /usr/lib/locale
%dir /usr/lib/x86_64-linux-gnu
%dir /usr/libexec
%dir /usr/local
%dir /usr/local/bin
%dir /usr/local/include
%dir /usr/local/lib
%dir /usr/local/sbin
%dir /usr/local/share
%dir /usr/local/share/color
%dir /usr/local/share/dict
%dir /usr/local/share/doc
%dir /usr/local/share/info
%dir /usr/local/share/locale
%dir /usr/local/share/man
%dir /usr/local/share/man/man1
%dir /usr/local/share/man/man2
%dir /usr/local/share/man/man3
%dir /usr/local/share/man/man4
%dir /usr/local/share/man/man5
%dir /usr/local/share/man/man6
%dir /usr/local/share/man/man7
%dir /usr/local/share/man/man8
%dir /usr/local/share/misc
%dir /usr/local/share/terminfo
%dir /usr/local/share/zoneinfo
%dir /usr/local/src
%dir /usr/sbin
%dir /usr/share
%dir /usr/share/color
%dir /usr/share/dict
%dir /usr/share/doc
%dir /usr/share/info
%dir /usr/share/locale
%dir /usr/share/man
%dir /usr/share/man/man1
%dir /usr/share/man/man2
%dir /usr/share/man/man3
%dir /usr/share/man/man4
%dir /usr/share/man/man5
%dir /usr/share/man/man6
%dir /usr/share/man/man7
%dir /usr/share/man/man8
%dir /usr/share/misc
%dir /usr/share/terminfo
%dir /usr/share/zoneinfo
%dir /usr/src
%dir /var
%dir /var/cache
%dir /var/lib
%dir /var/lib/misc
%dir /var/lib/rpm
%dir /var/local
%dir /var/log
%dir /var/opt
%dir /var/spool
%dir /var/spool/mail

# Symlinks
/bin
/etc/mtab
/lib
/lib64
/sbin
/var/lock
/var/mail
/var/run
/usr/lib/lib32
/usr/lib32

%changelog
* Sun May 03 2026 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 26.4-1.m264
- Initial filesystem package separated from maquilinux.
- Owns all FHS directory structure and required symlinks.