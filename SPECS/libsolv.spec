%define libsolv_version 0.7.35

# Built inside an LFS-style chroot with no debuginfo helpers available.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global solv_multilibdir /usr/lib/i386-linux-gnu
%global solv_lib_subdir lib/i386-linux-gnu
%global solv_enable_devel 0
%else
%global solv_multilibdir /usr/lib/x86_64-linux-gnu
%global solv_lib_subdir lib/x86_64-linux-gnu
%global solv_enable_devel 1
%endif

Name:           libsolv
Version:        %{libsolv_version}
Release:        5.m264%{?dist}
Summary:        Package dependency solver library

%if "%{_target_cpu}" == "x86_64"
Provides:       libsolv.so.1()(64bit)
Provides:       libsolvext.so.1()(64bit)
%endif

License:        BSD
URL:            https://github.com/openSUSE/libsolv
Source0:        https://github.com/openSUSE/libsolv/archive/refs/tags/%{version}/libsolv-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  cmake
BuildRequires:  ninja
BuildRequires:  zlib
BuildRequires:  zlib-devel
BuildRequires:  bzip2
BuildRequires:  xz-devel
BuildRequires:  zstd-devel
BuildRequires:  expat-devel
BuildRequires:  rpm

%description
libsolv is a fast and flexible dependency solver library used by package
managers such as DNF and Zypper. It provides support for rpmmd metadata,
rich dependencies, and multiple compression formats.

%if %{solv_enable_devel}
%package devel
Summary:        Development files for libsolv
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, CMake configuration files, and helper tools
needed to build software against libsolv.
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
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_INSTALL_LIBDIR=%{solv_lib_subdir} \
    -DLIB=%{solv_lib_subdir} \
    -DINCLUDE=include \
    -DPKGCONFIG_INSTALL_DIR=%{solv_multilibdir}/pkgconfig \
%if "%{_target_cpu}" == "i686"
    -DENABLE_RPMDB=OFF \
    -DENABLE_COMPS=OFF \
%else
    -DENABLE_RPMDB=ON \
    -DENABLE_COMPS=ON \
%endif
    -DENABLE_COMPLEX_DEPS=ON \
%if "%{_target_cpu}" == "i686"
    -DENABLE_RPMMD=OFF \
    -DENABLE_RPMPKG=OFF \
%else
    -DENABLE_RPMMD=ON \
    -DENABLE_RPMPKG=ON \
%endif
    -DENABLE_ZLIB_COMPRESSION=ON \
    -DENABLE_BZIP2_COMPRESSION=ON \
    -DENABLE_LZMA_COMPRESSION=ON \
    -DENABLE_ZSTD_COMPRESSION=ON \
    -DENABLE_APPDATA=OFF \
    -DENABLE_TESTS=OFF \
    -DENABLE_DEBIAN=OFF \
    -DENABLE_ARCHREPO=OFF \
    -DENABLE_CONDA=OFF \
    -DENABLE_RUBY=OFF \
    -DENABLE_PYTHON=OFF \
    -DENABLE_PERL=OFF \
    -DENABLE_TCL=OFF \
    -DENABLE_STATIC=OFF \
    -DDISABLE_SHARED=OFF

cmake --build build

%install
rm -rf %{buildroot}
DESTDIR=%{buildroot} cmake --install build

%if "%{_target_cpu}" == "i686"
# i686 package is libs-only: drop tools, headers and devel metadata
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}/usr/lib/cmake || :
rm -rf %{buildroot}/usr/share/cmake || :
rm -rf %{buildroot}%{solv_multilibdir}/pkgconfig || :
rm -f %{buildroot}%{solv_multilibdir}/libsolv.so || :
rm -f %{buildroot}%{solv_multilibdir}/libsolvext.so || :
rm -f %{buildroot}%{solv_multilibdir}/libsolv.a || :
rm -f %{buildroot}%{solv_multilibdir}/libsolvext.a || :
%endif

# Some builds default to /usr/lib64. Relocate to the multiarch libdir.
if [ -d %{buildroot}/usr/lib64 ]; then
  mkdir -p %{buildroot}%{solv_multilibdir}
  cp -a %{buildroot}/usr/lib64/. %{buildroot}%{solv_multilibdir}/
  rm -rf %{buildroot}/usr/lib64
fi

%if %{solv_enable_devel}
if [ ! -d %{buildroot}%{_includedir}/solv ]; then
  install -vdm 755 %{buildroot}%{_includedir}/solv
fi

# Some upstream install setups in our bootstrap environment may miss headers.
# Ensure dnf5 can compile against libsolv by shipping a complete /usr/include/solv.
for h in include/solv/*.h src/*.h ext/*.h src/solv/*.h; do
  if [ -f "$h" ]; then
    base="$(basename "$h")"
    if [ ! -f "%{buildroot}%{_includedir}/solv/$base" ]; then
      install -pm644 "$h" "%{buildroot}%{_includedir}/solv/"
    fi
  fi
done
%endif

# Ensure docs and licenses exist.
install -vdm 755 %{buildroot}%{_docdir}/%{name}
install -pm644 README NEWS LICENSE.BSD %{buildroot}%{_docdir}/%{name}/

cd %{buildroot}
# Runtime: shared libs, plugin helpers, manpages, docs.
{
  if [ -d .%{solv_multilibdir} ]; then
    find .%{solv_multilibdir} -maxdepth 1 -type f -name 'libsolv.so.*'
    find .%{solv_multilibdir} -maxdepth 1 -type l -name 'libsolv.so.*'
    find .%{solv_multilibdir} -maxdepth 1 -type f -name 'libsolvext.so.*'
    find .%{solv_multilibdir} -maxdepth 1 -type l -name 'libsolvext.so.*'
  fi
  if [ -d ./usr/libexec ]; then
    find ./usr/libexec -type f -o -type l
  fi
  if [ -d ./usr/share/doc/%{name} ]; then
    find ./usr/share/doc/%{name} -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
} | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/libsolv-runtime.list

%if %{solv_enable_devel}
# Development: headers, pkgconfig, cmake files, static libs, binaries, .so symlinks.
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d .%{solv_multilibdir} ]; then
    find .%{solv_multilibdir} -maxdepth 1 -type f -name 'libsolv.so'
    find .%{solv_multilibdir} -maxdepth 1 -type l -name 'libsolv.so'
    find .%{solv_multilibdir} -type f -name 'libsolvext.so'
    find .%{solv_multilibdir} -type l -name 'libsolvext.so'
    find .%{solv_multilibdir} -type f -name 'libsolv.a'
    find .%{solv_multilibdir} -type l -name 'libsolv.a'
    if [ -d .%{solv_multilibdir}/pkgconfig ]; then
      find .%{solv_multilibdir}/pkgconfig -type f -o -type l
    fi
  fi
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
  if [ -d ./usr/lib/cmake ]; then
    find ./usr/lib/cmake -type f -o -type l
  fi
  if [ -d ./usr/share/cmake/Modules ]; then
    find ./usr/share/cmake/Modules -type f -o -type l
  fi
} | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/libsolv-devel.list
%endif

%files -f %{_builddir}/libsolv-runtime.list
%defattr(-,root,root,-)

%if %{solv_enable_devel}
%files devel -f %{_builddir}/libsolv-devel.list
%defattr(-,root,root,-)
%endif

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 0.7.35-4.m264
- Enable rpmdb/comps/richdeps support required by dnf5 (libsolvext symbols).
