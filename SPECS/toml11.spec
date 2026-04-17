%define _toml11_version 4.4.0

# Header-only library; no debuginfo helpers available in the LFS-style chroot.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global toml11_multilibdir /usr/lib/i386-linux-gnu
%else
%global toml11_multilibdir /usr/lib/x86_64-linux-gnu
%endif

Name:           toml11
Version:        %{_toml11_version}
Release:        1.m264%{?dist}
Summary:        Header-only TOML parser/serializer for modern C++

License:        MIT
URL:            https://github.com/ToruNiina/toml11
Source0:        https://github.com/ToruNiina/toml11/archive/refs/tags/%{name}-v%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  cmake

%description
toml11 is a header-only TOML parser and serializer for modern C++ projects.
It implements the TOML specification and provides convenient conversion helpers
for mapping TOML data to native C++ types.

%package devel
Summary:        Development files for toml11
Requires:       %{name} = %{version}-%{release}

%description devel
Development files for toml11, including headers and CMake package
configuration files.

%prep
%setup -q -n %{name}-%{version}

%build
cmake -S . -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_INSTALL_LIBDIR=%{toml11_multilibdir} \
    -DCMAKE_INSTALL_DOCDIR=%{_docdir}/%{name} \
    -DTOML11_BUILD_TESTS=OFF \
    -DTOML11_BUILD_EXAMPLES=OFF \
    -DTOML11_BUILD_TOML_TESTS=OFF \
    -DTOML11_INSTALL=ON

cmake --build build

%install
rm -rf %{buildroot}
cmake --install build --prefix %{buildroot}%{_prefix}

# Ensure docs/licenses are present even if upstream skips installation.
install -vdm 755 %{buildroot}%{_docdir}/%{name}
install -pm644 README.md README_ja.md LICENSE %{buildroot}%{_docdir}/%{name}/

# Generate busybox-friendly file lists.
cd %{buildroot}
{
  if [ -d ./usr/share/doc/%{name} ]; then
    find ./usr/share/doc/%{name} -type f -o -type l
  fi
} | sed 's|^\.||' > %{_builddir}/toml11-runtime.list

{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d .%{toml11_multilibdir}/cmake ]; then
    find .%{toml11_multilibdir}/cmake -type f -o -type l
  fi
} | sed 's|^\.||' > %{_builddir}/toml11-devel.list

%files -f %{_builddir}/toml11-runtime.list
%defattr(-,root,root,-)

%files devel -f %{_builddir}/toml11-devel.list
%defattr(-,root,root,-)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 4.4.0-1.m264
- Initial toml11 packaging with runtime/docs and -devel split.
