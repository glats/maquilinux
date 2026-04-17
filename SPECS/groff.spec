Name:           groff
Version:        1.23.0
Release:        1.m264%{?dist}
Summary:        GNU typesetting and document formatting system

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-or-later
URL:            https://www.gnu.org/software/groff/
Source0:        https://ftp.gnu.org/gnu/groff/groff-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  texinfo

%description
Groff contains programs for processing and formatting text and images,
providing the traditional troff/nroff toolchain.

%prep
%autosetup -n groff-%{version}

%build
PAGE=letter ./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/groff-files.list

%files -f %{_builddir}/groff-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.23.0-1.m264
- Initial packaging aligned with MLFS 8.66 instructions.
