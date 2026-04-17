%define jsonc_version 0.18

# Built inside an LFS-style chroot with no debuginfo helpers available.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global jsonc_multilibdir /usr/lib/i386-linux-gnu
%global jsonc_enable_devel 0
%else
%global jsonc_multilibdir /usr/lib/x86_64-linux-gnu
%global jsonc_enable_devel 1
%endif

Name:           json-c
Version:        %{jsonc_version}
Release:        1.m264%{?dist}
Summary:        JSON implementation in C

%if "%{_target_cpu}" == "x86_64"
Provides:       libjson-c.so.5()(64bit)
%endif

License:        MIT
URL:            https://github.com/json-c/json-c
Source0:        https://s3.amazonaws.com/json-c_releases/releases/json-c-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  cmake
BuildRequires:  ninja
BuildRequires:  pkgconf

%description
json-c implements a reference counting JSON object model in C, providing
simple APIs for parsing, manipulating, and serializing JSON documents
while keeping dependencies minimal.

%if %{jsonc_enable_devel}
%package devel
Summary:        Development files for json-c
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, CMake package files, and development
libraries needed for building software against json-c.
%endif

%prep
%setup -q -n %{name}-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
export CFLAGS="${CFLAGS:-} -m32"
export CXXFLAGS="${CXXFLAGS:-} -m32"
export LDFLAGS="${LDFLAGS:-} -L/usr/lib/i386-linux-gnu -m32"
%endif

cmake -S . -B build \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_INSTALL_LIBDIR=%{jsonc_multilibdir} \
    -DCMAKE_INSTALL_DOCDIR=%{_docdir}/%{name} \
    -DBUILD_SHARED_LIBS=ON \
    -DENABLE_THREADING=ON \
    -DBUILD_APPS=OFF \
    -DBUILD_TESTING=OFF

cmake --build build

%install
rm -rf %{buildroot}
DESTDIR=%{buildroot} cmake --install build

%if "%{_target_cpu}" == "i686"
# i686 package is libs-only: drop headers, doc files, devel artifacts
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -f %{buildroot}%{jsonc_multilibdir}/libjson-c.so || :
rm -f %{buildroot}%{jsonc_multilibdir}/libjson-c.a || :
rm -rf %{buildroot}%{jsonc_multilibdir}/cmake || :
rm -rf %{buildroot}%{jsonc_multilibdir}/pkgconfig || :
%endif

# json-c installs LICENSE automatically, ensure README is included.
install -vdm 755 %{buildroot}%{_docdir}/%{name}
install -pm644 README.md %{buildroot}%{_docdir}/%{name}/README.md || :

cd %{buildroot}
# Runtime: versioned shared libraries plus docs.
{
  if [ -d .%{jsonc_multilibdir} ]; then
    find .%{jsonc_multilibdir} -maxdepth 1 -type f -name 'libjson-c.so.*'
    find .%{jsonc_multilibdir} -maxdepth 1 -type l -name 'libjson-c.so.*'
  fi
  if [ -d ./usr/share/doc/%{name} ]; then
    find ./usr/share/doc/%{name} -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
} | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/jsonc-runtime.list

%if %{jsonc_enable_devel}
# Development: headers, pkgconfig, cmake files, static libs, and .so linker symlink.
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d .%{jsonc_multilibdir} ]; then
    find .%{jsonc_multilibdir} -maxdepth 1 -type f -name 'libjson-c.so'
    find .%{jsonc_multilibdir} -maxdepth 1 -type l -name 'libjson-c.so'
    find .%{jsonc_multilibdir} -type f -name 'libjson-c.a'
    find .%{jsonc_multilibdir} -type l -name 'libjson-c.a'
  fi
  if [ -d .%{jsonc_multilibdir}/pkgconfig ]; then
      find .%{jsonc_multilibdir}/pkgconfig -type f -o -type l
    fi
    if [ -d .%{jsonc_multilibdir}/cmake ]; then
      find .%{jsonc_multilibdir}/cmake -type f -o -type l
    fi
} | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/jsonc-devel.list
%endif

%files -f %{_builddir}/jsonc-runtime.list
%defattr(-,root,root,-)

%if %{jsonc_enable_devel}
%files devel -f %{_builddir}/jsonc-devel.list
%defattr(-,root,root,-)
%endif

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 0.18-1.m264
- Initial json-c packaging with runtime and -devel split.
