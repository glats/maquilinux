Summary:    Maquilinux
Name:       maquilinux
Version:    1
Release:    1.m264%{?dist}
License:    BSD-3-Clause
Group:      Maquilinux/Base
URL:        https://maquilinux.com
BuildArch:  noarch
Source0:    maquilinux.repo

# Built inside a minimal LFS-style chroot without find-debuginfo or brp helpers.
# Disable automatic debuginfo and BRP post scripts for consistent packaging.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

# NOTE about dependencies for this base package:
# rpmbuild normally scans the scripts in this spec (like %install and %pre)
# and automatically adds Requires such as /bin/sh. In our LFS bootstrap
# environment, /bin/sh already exists because it was created by the
# temporary tools, but it is not yet owned by any RPM package. That makes
# the automatically generated /bin/sh dependency fail, even though the
# interpreter is really present and working.


%description
Maquilinux is a Linux distribution based on LFS and RPM.
This package contains the basic directory layout for a Linux operating system,
including the correct permissions for the directories.


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
install -vdm 755 %{buildroot}/usr/lib64
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
install -vdm 755 %{buildroot}/lib64
ln -sv ../run %{buildroot}/var/run
ln -sv ../run/lock %{buildroot}/var/lock
ln -sv spool/mail %{buildroot}/var/mail
ln -sv ../proc/self/mounts %{buildroot}/etc/mtab
touch %{buildroot}/var/log/{btmp,lastlog,faillog,wtmp}
chgrp -v 13	%{buildroot}/var/log/lastlog
chmod -v 664	%{buildroot}/var/log/lastlog
chmod -v 600	%{buildroot}/var/log/btmp

cat > %{buildroot}/etc/passwd <<- EOF
root:x:0:0:root:/root:/bin/bash
bin:x:1:1:bin:/dev/null:/usr/bin/false
daemon:x:6:6:Daemon User:/dev/null:/usr/bin/false
messagebus:x:18:18:D-Bus Message Daemon User:/run/dbus:/usr/bin/false
uuidd:x:80:80:UUID Generation Daemon User:/dev/null:/usr/bin/false
nobody:x:65534:65534:Unprivileged User:/dev/null:/usr/bin/false
EOF

cat > %{buildroot}/etc/group <<- EOF
root:x:0:
bin:x:1:daemon
sys:x:2:
kmem:x:3:
tape:x:4:
tty:x:5:
daemon:x:6:
floppy:x:7:
disk:x:8:
lp:x:9:
dialout:x:10:
audio:x:11:
video:x:12:
utmp:x:13:
cdrom:x:15:
adm:x:16:
messagebus:x:18:
input:x:24:
mail:x:34:
kvm:x:61:
uuidd:x:80:
wheel:x:97:
users:x:999:
nogroup:x:65534:
EOF

cat > %{buildroot}/etc/ld.so.conf <<- EOF
include /etc/ld.so.conf.d/*.conf
/usr/local/lib
/usr/lib
/opt/lib
EOF

cat > %{buildroot}/etc/nsswitch.conf <<- EOF
passwd: files
group: files
shadow: files

hosts: files dns
networks: files

protocols: files
services: files
ethers: files
rpc: files
EOF

cat > %{buildroot}/etc/hosts <<- EOF
127.0.0.1  localhost
::1        localhost
EOF

cat > %{buildroot}/etc/hostname <<- EOF
# Set the system hostname. Example:
# maquilinux
EOF

cat > %{buildroot}/etc/resolv.conf <<- EOF
# DNS resolver configuration. Example:
# nameserver 1.1.1.1
# nameserver 8.8.8.8
EOF

cat > %{buildroot}/etc/fstab <<- EOF
# <file system> <dir> <type> <options> <dump> <pass>
# /dev/sda1      /     ext4   defaults  1      1
EOF

echo %{version} > %{buildroot}/etc/os-release
cat > %{buildroot}/etc/os-release <<- EOF
NAME="Maqui Linux"
VERSION="26.4"
ID=maquilinux
VERSION_ID=26.4
PRETTY_NAME="Maqui Linux 26.4"
HOME_URL="https://maquilinux.org/"
EOF

# DNF/YUM repository configuration
install -Dm 644 %{_sourcedir}/maquilinux.repo %{buildroot}/etc/yum.repos.d/maquilinux.repo

# DNF releasever variable (ensures $releasever resolves correctly)
echo "26.4" > %{buildroot}/etc/dnf/vars/releasever

# Temporary workaround: on early systems /var/mail may exist as a directory
# created by the temporary LFS setup. We remove that directory here so the
# maquilinux base package can own /var/mail as a symlink to /var/spool/mail.
# Similarly, /usr/lib32 may exist as a real directory from the temporary toolchain.
# We remove it so the package can create the symlink.
%pre
if [ -d /var/mail ] && [ ! -L /var/mail ]; then
  rm -rf /var/mail
fi

if [ -d /usr/lib32 ] && [ ! -L /usr/lib32 ]; then
  rm -rf /usr/lib32
fi

%files
%defattr(-,root,root)
%attr(600,root,root)	/var/log/btmp
%attr(664,root,utmp)	/var/log/lastlog
%attr(664,root,utmp)	/var/log/wtmp
%attr(750,root,root)	/root
%attr(1777,root,root)	/tmp
%attr(1777,root,root)	/var/tmp
%attr(664,root,root)	/etc/ld.so.conf
%attr(664,root,root)	/etc/nsswitch.conf

# Directories created and owned by this package
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
/usr/lib/lib32
/usr/lib32
%dir /usr/include
%dir /usr/lib
%dir /usr/lib64
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

# Files and Symlinks
/bin
/etc/mtab
%config(noreplace) /etc/group
%config(noreplace) /etc/hosts
%config(noreplace) /etc/hostname
%config(noreplace) /etc/resolv.conf
%config(noreplace) /etc/fstab
%config(noreplace) /etc/os-release
%config(noreplace) /etc/passwd
%config(noreplace) /etc/yum.repos.d/maquilinux.repo
%config(noreplace) /etc/dnf/vars/releasever
/lib
/lib64
/sbin
/var/lock
/var/mail
%config(noreplace) /var/log/faillog
/var/run

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1-1.m264
- Maquilinux base package and filesystem layout.
