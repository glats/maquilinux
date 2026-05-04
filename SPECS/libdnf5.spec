# SPECS/libdnf5.spec
%define debug_package %{nil}

# libdnf5 is built from the dnf5 source tree. The same CMake build
# produces libdnf5, libdnf5-cli, and dnf5. This spec only packages
# the core libdnf5 library and devel files. See also: libdnf5-cli.spec

Name: libdnf5
Version:        5.3.0.0
Release:        1.m264%{?dist}
Summary:        Package management library for RPM
License:        LGPL-2.1-or-later
URL:            https://github.com/rpm-software-management/dnf5
Source0:        https://github.com/rpm-software-management/dnf5/archive/refs/tags/%{version}.tar.gz
BuildRequires:  gcc
BuildRequires: gcc
BuildRequires: cmake
BuildRequires: make
BuildRequires: pkgconfig(fmt)
BuildRequires: pkgconfig(glib-2.0)
BuildRequires: pkgconfig(json-c)
BuildRequires: pkgconfig(librepo)
BuildRequires: pkgconfig(libsolv)
BuildRequires: pkgconfig(libsolvext)
BuildRequires: pkgconfig(popt)
BuildRequires: pkgconfig(sqlite3)
BuildRequires: rpm
Requires:       libsolv
Requires:       librepo
Requires:       rpm-libs
Requires:       sqlite
Requires:       json-c
Requires:       fmt
Requires:       glib2
Requires:       popt

%description
Libdnf5 is the RPM package management library used by dnf5. It provides
the core functionality for resolving dependencies, querying packages,
and performing transactions on an RPM-based system.

%prep
%autosetup -p1

%build
cmake -B build \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_LIBDIR=/usr/lib/x86_64-linux-gnu \
    -DWITH_SYSTEMD=OFF \
    -DWITH_DBUS=OFF \
    -DWITH_PLUGIN_ACTIONS=ON

cmake --build build

%install
cmake --install build

%files
%config(noreplace) /etc/dnf/dnf.conf
%dir %attr(0755, root, root) /etc/dnf/dnf5-aliases.d
%dir %attr(0755, root, root) /etc/dnf/libdnf5-plugins
%config(noreplace) /etc/dnf/libdnf5-plugins/local.conf
%dir %attr(0755, root, root) /usr/lib/sysimage/libdnf5
/usr/lib/x86_64-linux-gnu/libdnf5.so.2
/usr/lib/x86_64-linux-gnu/libdnf5/plugins/local.so
/usr/share/dnf5/aliases.d/compatibility.conf

%package devel
Summary:        Development files for libdnf5
Requires:       libdnf5%{?_isa} = %{version}-%{release}

%files devel
/usr/lib/x86_64-linux-gnu/libdnf5.so
/usr/include/libdnf5/
/usr/lib/x86_64-linux-gnu/cmake/libdnf5/
/usr/lib/x86_64-linux-gnu/pkgconfig/libdnf5.pc

%changelog
* Mon May 04 2026 Maqui Linux <info@maquilinux.org> - 5.3.0.0-1.m264
- Initial Maqui Linux release with m264 tag