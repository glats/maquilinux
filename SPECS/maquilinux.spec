Summary: Maqui Linux base configuration
Name: maquilinux
Version: 2
Release: 1.m264%{?dist}
License: BSD-3-Clause
Group: Maquilinux/Base
URL: https://maquilinux.com
BuildArch: noarch
Source0: maquilinux.repo

# Directory layout is now owned by filesystem.spec
Requires: filesystem

# Built inside a minimal Maqui Linux chroot without find-debuginfo or brp helpers.
# Disable automatic debuginfo and BRP post scripts for consistent packaging.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%description
Maqui Linux is an independent Linux distribution built from source,
managed with RPM and DNF5. This package provides the base system
configuration files (passwd, group, network config, os-release,
DNF repository setup) and log file seeds. Directory layout ownership
was moved to the filesystem package in version 2.

%prep
%build
%install

# Create only the directories this package needs for its config files
install -vdm 755 %{buildroot}/etc
install -vdm 755 %{buildroot}/etc/ld.so.conf.d
install -vdm 755 %{buildroot}/etc/yum.repos.d
install -vdm 755 %{buildroot}/etc/dnf/vars
install -vdm 755 %{buildroot}/var/log

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

# Create log file seeds
touch %{buildroot}/var/log/{btmp,lastlog,faillog,wtmp}
chgrp -v 13 %{buildroot}/var/log/lastlog
chmod -v 664 %{buildroot}/var/log/lastlog
chmod -v 600 %{buildroot}/var/log/btmp

%files
%defattr(-,root,root)

# Log files with special permissions
%attr(600,root,root) /var/log/btmp
%attr(664,root,utmp) /var/log/lastlog
%attr(664,root,utmp) /var/log/wtmp
%config(noreplace) %attr(664,root,root) /var/log/faillog

# System configuration files
%attr(664,root,root) /etc/ld.so.conf
%attr(664,root,root) /etc/nsswitch.conf
%config(noreplace) /etc/passwd
%config(noreplace) /etc/group
%config(noreplace) /etc/hosts
%config(noreplace) /etc/hostname
%config(noreplace) /etc/resolv.conf
%config(noreplace) /etc/fstab
%config(noreplace) /etc/os-release
%config(noreplace) /etc/yum.repos.d/maquilinux.repo
%config(noreplace) /etc/dnf/vars/releasever

%changelog
* Mon May 04 2026 Maqui Linux <info@maquilinux.org> - 2-1.m264
- Version 2: directory ownership transferred to filesystem.spec.
- Now owns only config files (passwd, group, os-release, etc.) and log seeds.
- Added Requires: filesystem for directory layout.
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1-1.m264
- Maquilinux base package and filesystem layout.
