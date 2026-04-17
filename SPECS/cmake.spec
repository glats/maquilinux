Name:           cmake
Version:        4.2.1
Release:        1.m264%{?dist}
Summary:        Cross-platform, open-source build system

ExclusiveArch:  x86_64

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        BSD
URL:            https://cmake.org/
Source0:        https://github.com/Kitware/CMake/releases/download/v%{version}/cmake-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make

%description
CMake is an open-source, cross-platform family of tools designed to build,
test and package software.

%prep
%setup -q -n cmake-%{version}

%build
./bootstrap --prefix=%{_prefix}
make %{?_smp_mflags}

%check
:

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' | \
  while IFS= read -r p; do \
    case "$p" in \
      *[[:space:]]*) printf '"%%s"\n' "$p" ;; \
      *)             printf '%%s\n' "$p" ;; \
    esac; \
  done > %{_builddir}/cmake-files.list

%files -f %{_builddir}/cmake-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 4.2.1-1.m264
- Initial packaging for RPM dependency.
