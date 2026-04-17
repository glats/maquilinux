# SPECS/libisoburn.spec
# Library to create, modify, and burn ISO 9660 images (xorriso)

Summary:        Library for creating ISO 9660 images
Name:           libisoburn
Version:        1.5.6
Release:        1%{?dist}
License:        GPLv2+
Group:          System/Base
URL:            https://dev.lovelyhq.com/libburnia/libisoburn
Source0:        https://files.libburnia-project.org/releases/libisoburn-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
# libburn and libisofs are installed in the rootfs (not as -devel RPMs)
# readline and zlib headers present from LFS build

Requires:       libburn >= 1.5.6
Requires:       libisofs >= 1.5.6

%global debug_package %{nil}

%description
libisoburn is a library to create, modify, and burn ISO 9660 images.
It includes the xorriso command line tool, which can:
- Create ISO images from files and directories
- Extract files from ISO images
- Modify existing ISO images
- Copy ISO images to CD, DVD, or BD
- Provide a frontend to mkisofs and cdrecord

xorriso is used to create bootable ISO images for Maqui Linux releases.

%prep
%setup -q

%build
./configure \
    --prefix=/usr \
    --libdir=/usr/lib/x86_64-linux-gnu \
    --enable-xattr \
    --enable-acl \
    --enable-libz \
    --enable-libreadline

make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot}

# Remove libtool archives and static lib
find %{buildroot} -name '*.la' -delete
find %{buildroot} -name '*.a' -delete
# Remove info dir file (managed by install-info)
rm -f %{buildroot}/usr/share/info/dir

# Create symlink for mkisofs compatibility
ln -s xorrisofs %{buildroot}/usr/bin/mkisofs

%files
%license COPYING COPYRIGHT
%doc README
/usr/bin/xorriso
/usr/bin/xorrisofs
/usr/bin/xorrecord
/usr/bin/xorriso-dd-target
/usr/bin/xorriso-tcltk
/usr/bin/osirrox
/usr/bin/mkisofs
/usr/include/libisoburn/
/usr/lib/x86_64-linux-gnu/libisoburn.so*
/usr/lib/x86_64-linux-gnu/pkgconfig/libisoburn-1.pc
/usr/share/man/man1/xorriso.1*
/usr/share/man/man1/xorrisofs.1*
/usr/share/man/man1/xorrecord.1*
/usr/share/man/man1/xorriso-dd-target.1*
/usr/share/man/man1/xorriso-tcltk.1*
/usr/share/info/xorriso*.info*
/usr/share/info/xorrecord.info*

%post
/sbin/ldconfig

%postun
/sbin/ldconfig

%changelog
* Mon Mar 24 2025 Maqui Linux Team <team@maqui-linux.org> - 1.5.6-1
- Initial package for Maqui Linux
- Includes xorriso for ISO creation
- mkisofs symlink for compatibility
