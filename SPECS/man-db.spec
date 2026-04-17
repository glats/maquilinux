Name:           man-db
Version:        2.13.1
Release:        1.m264%{?dist}
Summary:        Programs for finding and viewing manual pages

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.nongnu.org/man-db/
Source0:        https://download.savannah.gnu.org/releases/man-db/man-db-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  groff
BuildRequires:  gdbm
BuildRequires:  libpipeline
BuildRequires:  zlib
BuildRequires:  bzip2
BuildRequires:  xz
BuildRequires:  pkgconf

%description
The man-db suite provides the man, apropos, whatis, mandb, and related tools
used to manage and view manual pages on Linux systems.

%prep
%autosetup -n man-db-%{version}

%build
./configure --prefix=%{_prefix} \
            --docdir=%{_datadir}/doc/man-db-%{version} \
            --sysconfdir=%{_sysconfdir} \
            --disable-setuid \
            --enable-cache-owner=bin \
            --with-browser=/usr/bin/lynx \
            --with-vgrind=/usr/bin/vgrind \
            --with-grap=/usr/bin/grap \
            --with-systemdtmpfilesdir= \
            --with-systemdsystemunitdir=
make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/man-db-files.list

%files -f %{_builddir}/man-db-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.13.1-1.m264
- Initial packaging aligned with MLFS 8.80 instructions.
