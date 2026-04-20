Name:           libassuan
Version:        3.0.1
Release:        1.m264%{?dist}
Summary:        IPC library for the GnuPG components

%define debug_package %{nil}
%define __os_install_post %{nil}

License:        LGPL-2.1-or-later AND GPL-3.0-or-later
URL:            https://www.gnupg.org/related_software/libassuan/
# Download URL: https://gnupg.org/ftp/gcrypt/libassuan/libassuan-3.0.1.tar.bz2
Source0:        libassuan-3.0.1.tar.bz2

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  libgpg-error-devel

Requires:       libgpg-error

%description
Libassuan is a small library implementing the so-called "Assuan protocol".
This protocol is used for IPC between most newer GnuPG components. Libassuan's
primary use is as a IPC system for GnuPG, gpgme and similar packages.

%package devel
Summary:        Development files for libassuan
Requires:       %{name} = %{version}-%{release}
Requires:       libgpg-error-devel

%description devel
The libassuan-devel package contains libraries and header files for developing
applications that use libassuan.

%prep
%setup -q

%build
./configure \
    --prefix=%{_prefix} \
    --libdir=%{_libdir} \
    --enable-shared \
    --disable-static \
    --with-libgpg-error-prefix=%{_prefix}

make %{?_smp_mflags}

%install
make DESTDIR=%{buildroot} install

# Remove static libraries
rm -f %{buildroot}%{_libdir}/*.la
rm -f %{buildroot}%{_libdir}/*.a

%check
make check || true

%files
%license COPYING* AUTHORS
%{_libdir}/libassuan.so.9*
%{_bindir}/libassuan-config

%files devel
%{_includedir}/assuan.h
%{_libdir}/libassuan.so
%{_libdir}/pkgconfig/libassuan.pc

%changelog
* Sun Apr 19 2026 Maqui Linux <security@maqui-linux.org> - 3.0.1-1.m264
- Initial build for Maqui Linux 26.4
