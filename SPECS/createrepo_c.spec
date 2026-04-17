# SPECS/createrepo_c.spec
# C implementation of createrepo

Summary:        Creates a common metadata repository
Name:           createrepo_c
Version:        1.2.3
Release:        1%{?dist}
License:        GPLv2+
Group:          System/PackageManager
URL:            https://github.com/rpm-software-management/createrepo_c
Source0:        https://github.com/rpm-software-management/createrepo_c/archive/refs/tags/%{version}/createrepo_c-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  make
# glib-2.0, libcurl, libxml-2.0, openssl, rpm, sqlite3, zstd
# are all present from LFS build with pkg-config files.
# zchunk is not available — disabled below.

%global debug_package %{nil}

%description
createrepo_c is a C implementation of createrepo. It creates a repository
metadata from a set of RPM packages. This metadata is used by DNF and other
package managers to browse and install packages from the repository.

%prep
%setup -q

%build
# Maqui Linux stores .pc files under the multiarch libdir
export PKG_CONFIG_PATH=/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig
mkdir build && cd build
cmake .. \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_LIBDIR=/usr/lib/x86_64-linux-gnu \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DWITH_ZCHUNK=OFF \
    -DWITH_LIBMODULEMD=OFF \
    -DENABLE_PYTHON=OFF \
    -DENABLE_DRPM=OFF \
    -DENABLE_BASHCOMP=OFF \
    -DBUILD_DOC_C=OFF

make %{?_smp_mflags}

%install
cd build
make install DESTDIR=%{buildroot}

%files
%license COPYING
%doc README.md
/usr/bin/createrepo_c
/usr/bin/mergerepo_c
/usr/bin/modifyrepo_c
/usr/bin/sqliterepo_c
/usr/lib/x86_64-linux-gnu/libcreaterepo_c.so*
/usr/lib/x86_64-linux-gnu/pkgconfig/createrepo_c.pc
/usr/include/createrepo_c/
/usr/share/man/man8/createrepo_c.8*
/usr/share/man/man8/mergerepo_c.8*
/usr/share/man/man8/modifyrepo_c.8*
/usr/share/man/man8/sqliterepo_c.8*

%post
/sbin/ldconfig

%postun
/sbin/ldconfig

%changelog
* Mon Mar 24 2025 Maqui Linux Team <team@maqui-linux.org> - 1.2.1-1
- Initial package for Maqui Linux
