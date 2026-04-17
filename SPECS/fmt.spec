%define fmt_version 12.1.0

# Packed inside an LFS-style chroot lacking debuginfo helpers.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global fmt_multilibdir /usr/lib/i386-linux-gnu
%global fmt_enable_devel 0
%else
%global fmt_multilibdir /usr/lib/x86_64-linux-gnu
%global fmt_enable_devel 1
%endif

Name:           fmt
Version:        %{fmt_version}
Release:        1.m264%{?dist}
Summary:        Modern formatting library for C++

%if "%{_target_cpu}" == "x86_64"
Provides:       libfmt.so.12()(64bit)
%endif

License:        MIT
URL:            https://github.com/fmtlib/fmt
Source0:        https://github.com/fmtlib/fmt/releases/download/%{version}/fmt-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  cmake
BuildRequires:  ninja

%description
fmt is an open-source formatting library providing fast and safe
fmt::format-style APIs as well as a drop-in replacement for std::format
across multiple C++ standards.

%if %{fmt_enable_devel}
%package devel
Summary:        Development files for fmt
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Header files, CMake configuration, pkg-config metadata, and the unversioned
shared library symlink for developing against libfmt.
%endif

%prep
%setup -q -n fmt-%{version}

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
    -DCMAKE_INSTALL_LIBDIR=%{fmt_multilibdir} \
    -DCMAKE_INSTALL_DOCDIR=%{_docdir}/%{name} \
    -DFMT_DOC=OFF \
    -DFMT_TEST=OFF \
    -DFMT_FUZZ=OFF \
    -DBUILD_SHARED_LIBS=ON

cmake --build build

%install
rm -rf %{buildroot}
cmake --install build --prefix %{buildroot}%{_prefix}

# i686 build is libs-only. Drop headers and dev artifacts.
%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_includedir} || :
rm -f %{buildroot}%{fmt_multilibdir}/libfmt.so || :
rm -f %{buildroot}%{fmt_multilibdir}/libfmt.a || :
rm -rf %{buildroot}%{fmt_multilibdir}/pkgconfig || :
rm -rf %{buildroot}%{fmt_multilibdir}/cmake || :
%endif

# Ensure documentation and license files exist even if upstream skips them.
install -vdm 755 %{buildroot}%{_docdir}/%{name}
install -pm644 README.md LICENSE %{buildroot}%{_docdir}/%{name}/

cd %{buildroot}
# Runtime files: versioned shared libs plus docs/licenses.
{
  if [ -d .%{fmt_multilibdir} ]; then
    find .%{fmt_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libfmt.so.*'
  fi
  if [ -d ./usr/share/doc/%{name} ]; then
    find ./usr/share/doc/%{name} -type f -o -type l
  fi
} | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/fmt-runtime.list

%if %{fmt_enable_devel}
# Development files: headers, pkgconfig, cmake config, archives, and the
# unversioned shared library symlink.
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d .%{fmt_multilibdir} ]; then
    find .%{fmt_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libfmt.so'
    find .%{fmt_multilibdir} -type f -name 'libfmt.a' -o -type l -name 'libfmt.a'
    if [ -d .%{fmt_multilibdir}/pkgconfig ]; then
      find .%{fmt_multilibdir}/pkgconfig -type f -o -type l
    fi
    if [ -d .%{fmt_multilibdir}/cmake ]; then
      find .%{fmt_multilibdir}/cmake -type f -o -type l
    fi
  fi
} | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/fmt-devel.list
%endif

%files -f %{_builddir}/fmt-runtime.list
%defattr(-,root,root,-)

%if %{fmt_enable_devel}
%files devel -f %{_builddir}/fmt-devel.list
%defattr(-,root,root,-)
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 12.1.0-1.m264
- Initial fmt packaging with runtime and -devel split.
