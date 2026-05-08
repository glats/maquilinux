# SPECS/libdnf5.spec
%define debug_package %{nil}

# libdnf5 and libdnf5-cli are built from the dnf5 source tree.
# The same CMake build produces both libraries. This spec packages
# both libdnf5 (core) and libdnf5-cli (CLI support) with their
# respective -devel subpackages.

Name: libdnf5
Version:        5.3.0.0
Release:        1.m264%{?dist}
Summary:        Package management library for RPM
License:        LGPL-2.1-or-later
URL:            https://github.com/rpm-software-management/dnf5
Source0:        https://github.com/rpm-software-management/dnf5/archive/refs/tags/%{version}.tar.gz
BuildRequires:  gcc
BuildRequires:  cmake
BuildRequires:  make
BuildRequires:  pkgconfig(fmt)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(json-c)
BuildRequires:  pkgconfig(librepo)
BuildRequires:  pkgconfig(libsolv)
BuildRequires:  pkgconfig(libsolvext)
BuildRequires:  pkgconfig(popt)
BuildRequires:  pkgconfig(sqlite3)
BuildRequires:  pkgconfig(smartcols)
BuildRequires:  rpm
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
%autosetup -p1 -n dnf5-%{version}

%build
export PKG_CONFIG_PATH=/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/lib/i386-linux-gnu/pkgconfig:/usr/lib/pkgconfig
rm -rf build
cmake -B build \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_LIBDIR=/usr/lib/x86_64-linux-gnu \
    -DWITH_SYSTEMD=OFF \
    -DWITH_DBUS=OFF \
    -DWITH_DNF5=OFF \
    -DWITH_DNF5DAEMON_SERVER=OFF \
    -DWITH_DNF5DAEMON_CLIENT=OFF \
    -DWITH_DNF5_PLUGINS=OFF \
    -DWITH_PLUGIN_ACTIONS=OFF \
    -DWITH_PLUGIN_APPSTREAM=OFF \
    -DWITH_PLUGIN_EXPIRED_PGP_KEYS=OFF \
    -DWITH_PLUGIN_MANIFEST=OFF \
    -DWITH_PLUGIN_LOCAL=OFF \
    -DWITH_PYTHON_PLUGINS_LOADER=OFF \
    -DWITH_MODULEMD=OFF \
    -DWITH_PERL5=OFF \
    -DWITH_PYTHON3=OFF \
    -DWITH_RUBY=OFF \
    -DWITH_GO=OFF \
    -DWITH_HTML=OFF \
    -DWITH_MAN=OFF \
    -DWITH_TRANSLATIONS=OFF \
    -DWITH_TESTS=OFF \
    -DWITH_DNF5_OBSOLETES_DNF=OFF

cmake --build build

%install
DESTDIR=%{buildroot} cmake --install build
# Remove systemd files (not used in Maqui Linux)
rm -rf %{buildroot}/usr/lib/systemd

%files
/usr/lib/x86_64-linux-gnu/libdnf5.so.2

%package devel
Summary:        Development files for libdnf5
Requires:       libdnf5%{?_isa} = %{version}-%{release}

%description devel
Development files for libdnf5: headers, pkgconfig, and shared library
symlinks needed for compiling against libdnf5.

%files devel
/usr/lib/x86_64-linux-gnu/libdnf5.so
/usr/include/libdnf5/
/usr/lib/x86_64-linux-gnu/pkgconfig/libdnf5.pc

%package cli
Summary:        CLI library for dnf5
Requires:       libdnf5%{?_isa} = %{version}-%{release}

%description cli
Libdnf5-cli is the command-line interface library for dnf5. It provides
the shared CLI functionality used by the dnf5 command and other tools
that interact with the package manager.

%files cli
/usr/lib/x86_64-linux-gnu/libdnf5-cli.so.3

%package cli-devel
Summary:        Development files for libdnf5-cli
Requires:       libdnf5-cli%{?_isa} = %{version}-%{release}

%description cli-devel
Development files for libdnf5-cli: headers, pkgconfig, and shared library
symlinks needed for compiling against libdnf5-cli.

%files cli-devel
/usr/lib/x86_64-linux-gnu/libdnf5-cli.so
/usr/include/libdnf5-cli/
/usr/lib/x86_64-linux-gnu/pkgconfig/libdnf5-cli.pc

%changelog
* Mon May 04 2026 Maqui Linux <info@maquilinux.org> - 5.3.0.0-1.m264
- Initial Maqui Linux release with m264 tag
