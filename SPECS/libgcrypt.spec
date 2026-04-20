Name:           libgcrypt
Version:        1.11.0
Release:        1.m264%{?dist}
Summary:        General-purpose cryptographic library based on code from GnuPG

%define debug_package %{nil}
%define __os_install_post %{nil}

License:        LGPL-2.1-or-later
URL:            https://www.gnupg.org/related_software/libgcrypt/
Source0:        https://gnupg.org/ftp/gcrypt/libgcrypt/libgcrypt-%{version}.tar.bz2

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  libgpg-error-devel
BuildRequires:  gmp-devel

Requires:       libgpg-error
Requires:       gmp

%description
libgcrypt is a general-purpose cryptographic library based on the code from
GnuPG. It provides functions for all cryptographic building blocks:
symmetric ciphers, hash algorithms, MACs, public key algorithms, large integer
functions, and random numbers.

%package devel
Summary:        Development files for libgcrypt
Requires:       %{name} = %{version}-%{release}
Requires:       libgpg-error-devel

%description devel
The libgcrypt-devel package contains libraries and header files for developing
applications that use libgcrypt.

%prep
%setup -q

%build
./configure \
    --prefix=%{_prefix} \
    --libdir=%{_libdir} \
    --enable-shared \
    --disable-static \
    --disable-doc \
    --disable-asm \
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
%license COPYING* AUTHORS THANKS
%{_libdir}/libgcrypt.so.20*
%{_bindir}/libgcrypt-config
%{_bindir}/dumpsexp
%{_bindir}/hmac256
%{_libdir}/libgcrypt

%files devel
%{_includedir}/gcrypt.h
%{_libdir}/libgcrypt.so
%{_libdir}/pkgconfig/libgcrypt.pc
%{_aclocaldir}/libgcrypt.m4

%changelog
* Sun Apr 19 2026 Maqui Linux <security@maqui-linux.org> - 1.11.0-1.m264
- Initial build for Maqui Linux 26.4
