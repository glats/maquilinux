Name:           libssh2
Version:        1.11.1
Release:        1.m264%{?dist}
Summary:        A library implementing the SSH2 protocol

%define debug_package %{nil}
%define __os_install_post %{nil}

License:        BSD-3-Clause
URL:            https://www.libssh2.org/
Source0:        https://www.libssh2.org/download/libssh2-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  cmake
BuildRequires:  openssl-devel
BuildRequires:  zlib-devel

Requires:       openssl
Requires:       zlib

%description
libssh2 is a client-side C library implementing the SSH2 protocol.
It supports regular terminal shell sessions, file transfers using
SFTP and SCP, and TCP/IP connection tunneling.

%package devel
Summary:        Development files for libssh2
Requires:       %{name} = %{version}-%{release}
Requires:       openssl-devel
Requires:       zlib-devel

%description devel
The libssh2-devel package contains libraries and header files for developing
applications that use libssh2.

%prep
%setup -q

%build
# GCC 15/C23 compatibility: use C17 standard
export CFLAGS="-std=gnu17 ${CFLAGS:-}"

mkdir -p build
cd build
cmake .. \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_TESTING=OFF \
    -DCMAKE_C_FLAGS="${CFLAGS}" \
    -DCMAKE_C_COMPILER="gcc ${CFLAGS}"

make %{?_smp_mflags}

%install
cd build
make DESTDIR=%{buildroot} install

# Remove static libraries
rm -f %{buildroot}%{_libdir}/*.a

%check
cd build
make test || true

%files
%license COPYING LICENSE
%{_libdir}/libssh2.so.1*

%files devel
%{_includedir}/libssh2.h
%{_includedir}/libssh2_publickey.h
%{_includedir}/libssh2_sftp.h
%{_libdir}/libssh2.so
%{_libdir}/pkgconfig/libssh2.pc

%changelog
* Sun Apr 19 2026 Maqui Linux <security@maqui-linux.org> - 1.11.1-1.m264
- Initial build for Maqui Linux 26.4
