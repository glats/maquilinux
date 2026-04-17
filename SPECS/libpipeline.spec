Name:           libpipeline
Version:        1.5.8
Release:        1.m264%{?dist}
Summary:        Library for manipulating pipelines of subprocesses

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://gitlab.com/libpipeline/libpipeline
Source0:        https://download.savannah.gnu.org/releases/libpipeline/libpipeline-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconf

%description
Libpipeline provides a library for setting up and running pipelines of
processes in a flexible way.

%prep
%autosetup -n libpipeline-%{version}

%build
./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
# Tests require additional dependencies; skip here.
:

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/libpipeline-files.list

%files -f %{_builddir}/libpipeline-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.5.8-1.m264
- Initial packaging aligned with MLFS 8.71 instructions.
