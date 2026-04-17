Name:           cpio
Version:        2.15
Release:        3.m264%{?dist}
Summary:        A GNU archiving program

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/cpio/
Source0:        https://ftp.gnu.org/gnu/cpio/cpio-%{version}.tar.bz2
Patch0:         cpio-2.15-c23-extern.patch
Patch1:         cpio-2.15-c23-global.patch

BuildRequires:  gcc
BuildRequires:  make

Provides:       cpio

%description
GNU cpio is a program to manage archives of files. It can copy files
to and from archives, supporting various formats including the new
cpio and tar format.

%prep
%setup -q -n cpio-%{version}
%patch 0 -p1
%patch 1 -p1 -F2

%build
./configure \
    --prefix=%{_prefix} \
    --libdir=%{_libdir} \
    --bindir=%{_bindir}

make %{?_smp_mflags} V=1

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

# Remove info dir file
rm -f %{buildroot}%{_infodir}/dir

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/cpio-files.list

%files -f %{_builddir}/cpio-files.list
%defattr(-,root,root)

%changelog
* Thu Apr 09 2026 Maqui Linux Team <team@maqui-linux.org> - 2.15-1.m264
- Initial packaging for Maqui Linux
