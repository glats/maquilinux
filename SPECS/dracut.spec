# SPECS/dracut.spec
# dracut-ng initramfs generator for Maqui Linux
#
# Uses dracut-ng (the active fork of dracut, maintained since dracut 059
# was abandoned in December 2022). Built without Rust (dracut-cpio disabled)
# and without documentation (no asciidoctor required).
#
# Decision: docs/DECISIONS.md 2026-03-25 "initramfs generator"

Summary:        Initramfs generator for live ISO and installed systems
Name:           dracut
Version:        110
Release:        1%{?dist}
License:        GPL-2.0-or-later AND LGPL-2.1-or-later
Group:          System/Base
URL:            https://dracut-ng.github.io
Source0:        https://github.com/dracut-ng/dracut-ng/archive/refs/tags/%{version}.tar.gz

# Build dependencies
BuildRequires:  bash
BuildRequires:  coreutils
BuildRequires:  make
BuildRequires:  gcc
# kmod is present in rootfs (libkmod.pc at /usr/lib/x86_64-linux-gnu/pkgconfig/)
# Using package name instead of pkgconfig() since our kmod RPM lacks the auto-provides
BuildRequires:  kmod

# Runtime dependencies
Requires:       bash >= 4.0
Requires:       coreutils
Requires:       cpio
Requires:       findutils
Requires:       gawk
Requires:       grep
Requires:       kmod
Requires:       sed
Requires:       tar
Requires:       udev
Requires:       util-linux

# Optional but recommended for live ISO
Recommends:     squashfs-tools
Recommends:     device-mapper

%global debug_package %{nil}

%description
dracut-ng is an event-driven initramfs infrastructure and the actively
maintained fork of the original dracut project (which was last released
as dracut 059 in December 2022).

dracut creates an initramfs image by copying tools and files from an
installed system and combining it with dracut modules. This package is
built without systemd integration (for OpenRC) and without the optional
Rust-based dracut-cpio enhancement.

This package includes the dmsquash-live module for booting Maqui Linux
from live ISOs (USB drives, DVDs).

%prep
%setup -q -n dracut-ng-%{version}

%build
# Maqui Linux stores .pc files under the multiarch libdir
export PKG_CONFIG_PATH=/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig

./configure \
    --prefix=/usr \
    --sysconfdir=/etc \
    --libdir=/usr/lib \
    --disable-dracut-cpio \
    --disable-documentation

make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot} \
    DRACUT_FULL_VERSION="%{version}-%{release}"

# Create dracut.conf.d directory
mkdir -p %{buildroot}/etc/dracut.conf.d

# Maqui Linux OpenRC live ISO configuration
cat > %{buildroot}/etc/dracut.conf.d/maquilinux.conf << 'EOF'
# Maqui Linux dracut-ng configuration
# OpenRC system: systemd modules omitted
hostonly="no"
hostonly_cmdline="no"

# Modules for live ISO boot
add_dracutmodules+=" dmsquash-live livenet rootfs-block "

# Omit systemd — Maqui Linux uses OpenRC
omit_dracutmodules+=" systemd systemd-initrd "

# zstd: fast compression, good ratio
compress="zstd"
EOF

# Remove any systemd unit files (auto-detection may install them
# if systemd is present in the build host PATH, which it is not here)
rm -rf %{buildroot}/usr/lib/systemd
rm -rf %{buildroot}/etc/systemd

%files
%license COPYING
%doc README.md NEWS.md
%config(noreplace) /etc/dracut.conf
%dir /etc/dracut.conf.d
%config(noreplace) /etc/dracut.conf.d/maquilinux.conf
/usr/bin/dracut
/usr/bin/dracut-catimages
/usr/bin/lsinitrd
/usr/lib/dracut/
/usr/share/bash-completion/completions/dracut
/usr/share/bash-completion/completions/lsinitrd
/usr/lib/kernel/install.d/50-dracut.install
/usr/lib/kernel/install.d/51-dracut-rescue.install
/usr/share/pkgconfig/dracut.pc

%post
ldconfig || true
if [ -d /lib/modules/$(uname -r 2>/dev/null) ] 2>/dev/null; then
    echo "> dracut-ng installed. Generate initramfs with:"
    echo ">   dracut --no-hostonly --add 'dmsquash-live' /boot/initramfs-$(uname -r).img"
fi

%postun
ldconfig || true

%changelog
* Wed Mar 25 2026 Maqui Linux Team <team@maqui-linux.org> - 110-1
- Upgrade to dracut-ng 110 (active fork of dracut)
- dracut 059 was the last release of the original project (Dec 2022)
- Disabled dracut-cpio (Rust): deferred until Maqui Linux bootstraps Rust
- Disabled documentation build: no asciidoctor required
- OpenRC configuration: omit systemd modules
- See docs/DECISIONS.md for full rationale

* Mon Mar 24 2025 Maqui Linux Team <team@maqui-linux.org> - 059-1
- Initial package (dracut 059, now superseded)
