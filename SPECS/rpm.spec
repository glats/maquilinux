Name:           rpm
Version:        6.0.1
Release:        2.m264%{?dist}
Summary:        The RPM Package Manager

ExclusiveArch:  x86_64

# DNF5 looks for rpmdnf as a BuildRequires
Provides:       rpmdnf = %{version}-%{release}

# Provide library sonames for dependency resolution (bootstrap requirement)
Provides:       librpm.so.10()(64bit)
Provides:       librpmio.so.10()(64bit)
Provides:       librpmbuild.so.10()(64bit)
Provides:       librpmsign.so.10()(64bit)
# Lua is bundled with rpm build, provide soname temporarily
Provides:       liblua.so.5.4()(64bit)

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-or-later and LGPL-2.1-or-later
URL:            https://rpm.org/
Source0:        https://ftp.osuosl.org/pub/rpm/releases/rpm-6.0.x/rpm-%{version}.tar.bz2

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  cmake
BuildRequires:  pkgconf
BuildRequires:  popt
BuildRequires:  zlib
BuildRequires:  xz
BuildRequires:  zstd
BuildRequires:  file
BuildRequires:  libarchive
BuildRequires:  scdoc
BuildRequires:  openssl
BuildRequires:  sqlite
BuildRequires:  readline
BuildRequires:  libcap
BuildRequires:  acl
BuildRequires:  attr
BuildRequires:  elfutils

%description
RPM is the RPM Package Manager.

%prep
%setup -q -n rpm-%{version}

%build
mkdir -p _build
pushd _build
cmake .. \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_LIBDIR=lib/x86_64-linux-gnu \
    -DWITH_BZIP2=ON \
    -DENABLE_OPENMP=OFF \
    -DWITH_AUDIT=OFF \
    -DWITH_SELINUX=OFF \
    -DWITH_DBUS=OFF \
    -DWITH_SEQUOIA=OFF \
    -DWITH_OPENSSL=ON \
    -DENABLE_SQLITE=ON \
    -DENABLE_TESTSUITE=OFF \
    -DENABLE_PYTHON=ON \
    -DENABLE_PLUGINS=OFF \
    -DWITH_FAPOLICYD=OFF
make %{?_smp_mflags}
popd

%check
:

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}

pushd _build
make DESTDIR=%{buildroot} install
popd

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' | \
  while IFS= read -r p; do \
    case "$p" in \
      *[[:space:]]*) printf '"%%s"\n' "$p" ;; \
      *)             printf '%%s\n' "$p" ;; \
    esac; \
  done > %{_builddir}/rpm-files.list

test -s %{_builddir}/rpm-files.list

%files -f %{_builddir}/rpm-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 6.0.1-1.m264
- Initial packaging of rpm 6.0.1 for Maquilinux using a multiarch library layout (x86_64 libs in /usr/lib/x86_64-linux-gnu).
