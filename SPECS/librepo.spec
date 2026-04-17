%define librepo_version 1.20.0

# Built inside an LFS-style chroot with no debuginfo helpers available.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global librepo_multilibdir /usr/lib/i386-linux-gnu
%global librepo_lib_subdir lib/i386-linux-gnu
%global librepo_enable_devel 0
%else
%global librepo_multilibdir /usr/lib/x86_64-linux-gnu
%global librepo_lib_subdir lib/x86_64-linux-gnu
%global librepo_enable_devel 1
%endif

Name:           librepo
Version:        %{librepo_version}
Release:        1.m264%{?dist}
Summary:        Repository handling library for DNF and other tools

# librepo depends on curl/libxml2/rpm which we don't build for i686
ExclusiveArch:  x86_64

Provides:       librepo.so.0()(64bit)

License:        LGPL-2.1-or-later
URL:            https://github.com/rpm-software-management/librepo
Source0:        %{url}/archive/refs/tags/%{name}-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  cmake
BuildRequires:  ninja
BuildRequires:  pkgconf

# Core runtime dependencies as used by upstream CMake.
BuildRequires:  openssl-devel
BuildRequires:  curl-devel
BuildRequires:  libxml2-devel
BuildRequires:  glib2-devel

# Use rpm instead of gpgme for OpenPGP support.
BuildRequires:  rpm

%description
librepo is a library for downloading and processing repository metadata.
It is used by DNF and related tools for handling yum/dnf style repositories.

%if %{librepo_enable_devel}
%package devel
Summary:        Development files for librepo
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against librepo.
%endif

%prep
%setup -q -n %{name}-%{version}

%build
export PKG_CONFIG_LIBDIR="%{librepo_multilibdir}/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig"
export LDFLAGS="${LDFLAGS:-} -L%{librepo_multilibdir}"

cmake -S . -B build \
    -G Ninja \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_INSTALL_LIBDIR=%{librepo_lib_subdir} \
    -DENABLE_TESTS=OFF \
    -DENABLE_DOCS=OFF \
    -DENABLE_EXAMPLES=OFF \
    -DENABLE_PYTHON=OFF \
    -DWITH_ZCHUNK=OFF \
    -DUSE_GPGME=OFF \
    -DENABLE_SELINUX=OFF

cmake --build build

%install
rm -rf %{buildroot}
DESTDIR=%{buildroot} cmake --install build

# Ensure docs/licenses exist.
install -vdm 755 %{buildroot}%{_docdir}/%{name}
install -pm644 README.md COPYING %{buildroot}%{_docdir}/%{name}/

cd %{buildroot}
# Runtime: versioned shared libs and docs.
{
  if [ -d .%{librepo_multilibdir} ]; then
    find .%{librepo_multilibdir} -maxdepth 1 -type f -name 'librepo.so.*'
    find .%{librepo_multilibdir} -maxdepth 1 -type l -name 'librepo.so.*'
  fi
  if [ -d ./usr/share/doc/%{name} ]; then
    find ./usr/share/doc/%{name} -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
} | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/librepo-runtime.list

%if %{librepo_enable_devel}
# Development: headers, pkgconfig file, and unversioned shared library symlink.
{
  if [ -d ./usr/include/librepo ]; then
    find ./usr/include/librepo -type f -o -type l
  fi
  if [ -d .%{librepo_multilibdir} ]; then
    find .%{librepo_multilibdir} -maxdepth 1 -type f -name 'librepo.so'
    find .%{librepo_multilibdir} -maxdepth 1 -type l -name 'librepo.so'
    if [ -d .%{librepo_multilibdir}/pkgconfig ]; then
      find .%{librepo_multilibdir}/pkgconfig -type f -o -type l
    fi
  fi
} | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/librepo-devel.list
%endif

%files -f %{_builddir}/librepo-runtime.list
%defattr(-,root,root,-)

%if %{librepo_enable_devel}
%files devel -f %{_builddir}/librepo-devel.list
%defattr(-,root,root,-)
%endif

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.20.0-1.m264
- Initial librepo packaging with runtime and -devel split.
