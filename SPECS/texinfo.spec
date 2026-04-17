Name:           texinfo
Version:        7.2
Release:        1.m264%{?dist}
Summary:        GNU documentation system for on-line information and printed output

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/texinfo/
Source0:        https://ftp.gnu.org/gnu/texinfo/texinfo-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  perl
BuildRequires:  ncurses-devel

%description
Texinfo is the official documentation format of the GNU project, producing both
online and printed manuals from a single source.

%prep
%autosetup -n texinfo-%{version}

%build
./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
make DESTDIR=%{buildroot} install
if [ -d doc/info ]; then make -C doc/info DESTDIR=%{buildroot} install-info; fi

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' > %{builddir}/texinfo-files.list
test -s %{builddir}/texinfo-files.list

%files -f %{builddir}/texinfo-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 7.2-1.m264
- Initial packaging aligned with MLFS 8.75 instructions.
