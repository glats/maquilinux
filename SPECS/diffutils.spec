Name:           diffutils
Version:        3.12
Release:        1.m264%{?dist}
Summary:        File comparison utilities (diff, cmp, sdiff)

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/diffutils/
Source0:        https://ftp.gnu.org/gnu/diffutils/diffutils-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  texinfo

%description
The GNU Diffutils package provides cmp, diff, diff3, and sdiff—tools used to
compare files and directories and report differences.

%prep
%autosetup -n diffutils-%{version}

%build
./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/diffutils-files.list

%files -f %{_builddir}/diffutils-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.12-1.m264
- Initial packaging aligned with MLFS 8.63 instructions.
