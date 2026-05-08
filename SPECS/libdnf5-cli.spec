# SPECS/libdnf5-cli.spec
%define debug_package %{nil}

# libdnf5-cli is built from the same dnf5 source tree as libdnf5.
# The CMake build produces all dnf5 components. This spec only packages
# the libdnf5-cli shared library and devel files. The libdnf5 spec
# packages the core library, and dnf5.spec packages the CLI binary.
# Build order: libdnf5 -> libdnf5-cli -> dnf5 (all from same tarball).

Name: libdnf5-cli
Version:        5.3.0.0
Release:        1.m264%{?dist}
Summary:        CLI library for dnf5
License:        LGPL-2.1-or-later
URL:            https://github.com/rpm-software-management/dnf5
Source0:        https://github.com/rpm-software-management/dnf5/archive/refs/tags/%{version}.tar.gz
BuildRequires:  gcc
BuildRequires:  cmake
BuildRequires:  make
BuildRequires:  pkgconfig(fmt)
BuildRequires:  pkgconfig(json-c)
BuildRequires:  pkgconfig(smartcols)
BuildRequires:  libdnf5-devel
Requires:       libdnf5%{?_isa} = %{version}-%{release}

%description
Libdnf5-cli is the command-line interface library for dnf5. It provides
the shared CLI functionality used by the dnf5 command and other tools
that interact with the package manager.

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

%files
/usr/lib/x86_64-linux-gnu/libdnf5-cli.so.3

%package devel
Summary:        Development files for libdnf5-cli
Requires:       libdnf5-cli%{?_isa} = %{version}-%{release}

%description devel
Development files for libdnf5-cli: headers, cmake files, pkgconfig, and
shared library symlinks needed for compiling against libdnf5-cli.

%files devel
/usr/lib/x86_64-linux-gnu/libdnf5-cli.so
/usr/include/libdnf5-cli/
/usr/lib/x86_64-linux-gnu/cmake/libdnf5-cli/
/usr/lib/x86_64-linux-gnu/pkgconfig/libdnf5-cli.pc

%changelog
* Mon May 04 2026 Maqui Linux <info@maquilinux.org> - 5.3.0.0-1.m264
- Initial Maqui Linux release with m264 tag
