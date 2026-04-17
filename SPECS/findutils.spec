Name:           findutils
Version:        4.10.0
Release:        1.m264%{?dist}
Summary:        Utilities to find files and apply commands to them

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/findutils/
Source0:        https://ftp.gnu.org/gnu/findutils/findutils-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  texinfo

%description
GNU Findutils provides find, locate, updatedb, and xargs—programs used to
search directories and file name databases, and to run commands on the
results.

%prep
%autosetup -n findutils-%{version}

%build
./configure --prefix=%{_prefix} --localstatedir=/var/lib/locate
make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/findutils-files.list

%files -f %{_builddir}/findutils-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 4.10.0-1.m264
- Initial packaging aligned with MLFS 8.65 instructions.
