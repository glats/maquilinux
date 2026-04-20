Name:           libgpg-error
Version:        1.50
Release:        1.m264%{?dist}
Summary:        Library for error values used by GnuPG components

%define debug_package %{nil}
%define __os_install_post %{nil}

License:        LGPL-2.1-or-later
URL:            https://www.gnupg.org/related_software/libgpg-error/
Source0:        https://gnupg.org/ftp/gcrypt/libgpg-error/libgpg-error-%{version}.tar.bz2

BuildRequires:  gcc
BuildRequires:  make

%description
libgpg-error is a small library with error codes and descriptions shared by all
GnuPG related software. This package is required for building GnuPG, GPGME,
and other GnuPG related software.

%package devel
Summary:        Development files for libgpg-error
Requires:       %{name} = %{version}-%{release}

%description devel
The libgpg-error-devel package contains libraries and header files for developing
applications that use libgpg-error.

%prep
%setup -q

%build
# Fix for GCC 15 / C23: nullptr is a keyword in C23, but this code uses it as variable name
export CFLAGS="-std=gnu17 ${CFLAGS:-}"

./configure \
    --prefix=%{_prefix} \
    --libdir=%{_libdir} \
    --enable-shared \
    --disable-static \
    --enable-install-gpg-error-config \
    CFLAGS="${CFLAGS}"

make %{?_smp_mflags} CFLAGS="${CFLAGS}"

%install
make DESTDIR=%{buildroot} install

# Remove static libraries
rm -f %{buildroot}%{_libdir}/*.la
rm -f %{buildroot}%{_libdir}/*.a

%check
make check || true

%files
%license COPYING* AUTHORS
%{_libdir}/libgpg-error.so.0*
%{_bindir}/gpg-error
%{_bindir}/gpg-error-config
%{_datadir}/libgpg-error/

%files devel
%{_includedir}/gpg-error.h
%{_includedir}/gpgrt.h
%{_libdir}/libgpg-error.so
%{_libdir}/pkgconfig/gpg-error.pc

%changelog
* Sun Apr 19 2026 Maqui Linux <security@maqui-linux.org> - 1.50-1.m264
- Initial build for Maqui Linux 26.4
