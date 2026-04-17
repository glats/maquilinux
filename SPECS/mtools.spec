# SPECS/mtools.spec
# Tools for accessing MS-DOS disks without mounting

Summary:        Tools for accessing MS-DOS disks
Name:           mtools
Version:        4.0.43
Release:        2%{?dist}
License:        GPLv3+
Group:          System/Base
URL:            https://www.gnu.org/software/mtools/
Source0:        https://ftp.gnu.org/gnu/mtools/mtools-%{version}.tar.bz2

BuildRequires:  gcc
BuildRequires:  make

# Minimal dependencies - mtools is quite standalone

%global debug_package %{nil}

%description
Mtools is a collection of utilities to access MS-DOS disks from Unix
without mounting them. It supports Win'95 style long file names, OS/2
Warp extended attributes, and OS/2 Warp 2 extended attributes.

Mtools is used by ISO creation tools to generate EFI boot images.

%prep
%setup -q

%build
./configure \
    --prefix=/usr \
    --sysconfdir=/etc \
    --disable-floppyd \
    --disable-x11

make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot}

# Create default mtools.conf if not present
mkdir -p %{buildroot}/etc
if [[ ! -f %{buildroot}/etc/mtools.conf ]]; then
cat > %{buildroot}/etc/mtools.conf << 'EOF'
# mtools configuration file
# Default drive definitions

drive a: file="/dev/fd0" exclusive
# drive c: file="/dev/sda1"
EOF
fi

# Don't package the info files to keep it minimal
rm -rf %{buildroot}/usr/share/info

%files
%license COPYING
%doc README* NEWS*
/etc/mtools.conf
/usr/bin/mtools
/usr/bin/amuFormat.sh
/usr/bin/lz
/usr/bin/mcheck
/usr/bin/mcomp
/usr/bin/mkmanifest
/usr/bin/mxtar
/usr/bin/tgz
/usr/bin/uz
/usr/bin/mattrib
/usr/bin/mbadblocks
/usr/bin/mcat
/usr/bin/mcd
/usr/bin/mcopy
/usr/bin/mdel
/usr/bin/mdeltree
/usr/bin/mdir
/usr/bin/mdu
/usr/bin/mformat
/usr/bin/minfo
/usr/bin/mlabel
/usr/bin/mmd
/usr/bin/mmount
/usr/bin/mmove
/usr/bin/mpartition
/usr/bin/mrd
/usr/bin/mren
/usr/bin/mshortname
/usr/bin/mshowfat
/usr/bin/mtoolstest
/usr/bin/mtype
/usr/bin/mzip
/usr/share/man/man1/*.1*
/usr/share/man/man5/*.5*

%post
# Update mtools configuration if needed

%changelog
* Wed Apr 02 2026 Maqui Linux Team <team@maqui-linux.org> - 4.0.43-2
- Rebuild for self-hosting validation (dnf update test)

* Mon Mar 24 2025 Maqui Linux Team <team@maqui-linux.org> - 4.0.43-1
- Initial package for Maqui Linux
- Minimal build without X11 or floppy daemon
