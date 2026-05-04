# SPECS/libburn.spec
# Library for writing optical disc media (CD, DVD, Blu-ray)

Summary:        Library for writing optical disc media
Name:           libburn
Version:        1.5.8
Release:        1.m264%{?dist}
License:        GPL-2.0-or-later
Group:          System/Base
URL:            https://dev.lovelyhq.com/libburnia
Source0:        https://files.libburnia-project.org/releases/libburn-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconf

%global debug_package %{nil}

%description
Libburn is a library for writing optical disc media, including CD, DVD,
and Blu-ray. It is part of the Libburnia project and provides a
transparent interface for writing data to CD, DVD, and BD media.

%package devel
Summary:        Development files for libburn
Requires:       libburn = %{version}-%{release}
Provides:       libburn-devel = %{version}-%{release}

%description devel
Development files for libburn.
Headers and library links for building applications that use libburn.

%prep
%setup -q

%build
./configure \
    --prefix=/usr \
    --libdir=/usr/lib/x86_64-linux-gnu

make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot}

# Remove libtool archives and static lib
find %{buildroot} -name '*.la' -delete
find %{buildroot} -name '*.a' -delete
# Remove info dir file (managed by install-info)
rm -f %{buildroot}/usr/share/info/dir

%files
%license COPYING COPYRIGHT
%doc README
/usr/lib/x86_64-linux-gnu/libburn.so.*

%files devel
/usr/include/libburn/
/usr/lib/x86_64-linux-gnu/libburn.so
/usr/lib/x86_64-linux-gnu/pkgconfig/libburn*.pc

%post
/sbin/ldconfig

%postun
/sbin/ldconfig

%changelog
* Sun May 03 2026 Maqui Linux Team <team@maqui-linux.org> - 1.5.8-1.m264
- Initial package for Maqui Linux
- Provides RPM for libisoburn runtime dependency