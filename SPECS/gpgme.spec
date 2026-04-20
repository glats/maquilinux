Name:           gpgme
Version:        1.24.0
Release:        1.m264%{?dist}
Summary:        GnuPG Made Easy - high level crypto API

%define debug_package %{nil}
%define __os_install_post %{nil}

License:        LGPL-2.1-or-later
URL:            https://www.gnupg.org/related_software/gpgme/
Source0:        https://gnupg.org/ftp/gcrypt/gpgme/gpgme-%{version}.tar.bz2

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  libgpg-error-devel
BuildRequires:  libgcrypt-devel
BuildRequires:  libassuan-devel

Requires:       libgpg-error
Requires:       libgcrypt
Requires:       libassuan

%description
GPGME (GnuPG Made Easy) is a C language library that allows to add support
for cryptography to a program. It is designed to make access to public key
infrastructure like GnuPG or GPGSM easier.

%package devel
Summary:        Development files for gpgme
Requires:       %{name} = %{version}-%{release}
Requires:       libgpg-error-devel
Requires:       libgcrypt-devel
Requires:       libassuan-devel

%description devel
The gpgme-devel package contains libraries and header files for developing
applications that use gpgme.

%prep
%setup -q

%build
# GCC 15/C23 compatibility: use C17 standard
export CFLAGS="-std=gnu17 ${CFLAGS:-}"

./configure \
    --prefix=%{_prefix} \
    --libdir=%{_libdir} \
    --enable-shared \
    --disable-static \
    --disable-gpg-test \
    --disable-gpgsm-test \
    --with-libgpg-error-prefix=%{_prefix} \
    --with-libgcrypt-prefix=%{_prefix} \
    --with-libassuan-prefix=%{_prefix} \
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
%license COPYING* AUTHORS THANKS
%{_libdir}/libgpgme.so.11*
%{_bindir}/gpgme-config
%{_bindir}/gpgme-json
# C++ bindings may not be built/installed by default:
# %{_libdir}/libgpgmepp.so.6*

%files devel
%{_includedir}/gpgme.h
%{_libdir}/libgpgme.so
%{_libdir}/pkgconfig/gpgme.pc
# C++ devel files (if C++ bindings are enabled):
# %{_includedir}/gpgmepp
# %{_libdir}/libgpgmepp.so
# %{_libdir}/pkgconfig/gpgmepp.pc

%changelog
* Sun Apr 19 2026 Maqui Linux <security@maqui-linux.org> - 1.24.0-1.m264
- Initial build for Maqui Linux 26.4
