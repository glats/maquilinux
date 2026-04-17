# SPECS/libisofs.spec
# Library to create ISO 9660 filesystem images

Summary:        Library to create ISO 9660 images
Name:           libisofs
Version:        1.5.6
Release:        1%{?dist}
License:        GPLv2+
Group:          System/Libraries
URL:            https://dev.lovelyhq.com/libburnia/libisofs
Source0:        https://files.libburnia-project.org/releases/libisofs-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
# Note: zlib and acl headers/libs are present from LFS build
# but not packaged as -devel RPMs yet

%global debug_package %{nil}

%description
libisofs is a library to create an ISO 9660 filesystem and supports
extensions like RockRidge and Joliet. Required by libisoburn/xorriso.

%prep
%setup -q

%build
./configure \
    --prefix=/usr \
    --libdir=/usr/lib/x86_64-linux-gnu \
    --disable-static \
    --enable-xattr \
    --enable-acl \
    --enable-zlib

make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot}
# Remove libtool archives
find %{buildroot} -name '*.la' -delete

%files
%license COPYING COPYRIGHT
/usr/lib/x86_64-linux-gnu/libisofs.so*
/usr/lib/x86_64-linux-gnu/pkgconfig/libisofs-1.pc
/usr/include/libisofs/

%post
/sbin/ldconfig

%postun
/sbin/ldconfig

%changelog
* Wed Apr 02 2025 Maqui Linux Team <team@maqui-linux.org> - 1.5.6-1
- Initial package for Maqui Linux
- Dependency for libisoburn/xorriso
