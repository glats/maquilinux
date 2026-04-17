Name:           gzip
Version:        1.14
Release:        1.m264%{?dist}
Summary:        GNU data compression programs

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/gzip/
Source0:        https://ftp.gnu.org/gnu/gzip/gzip-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make

%description
Gzip compresses and decompresses files using Lempel-Ziv coding.

%prep
%autosetup -n gzip-%{version}

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
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/gzip-files.list

%files -f %{_builddir}/gzip-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.14-1.m264
- Initial packaging aligned with MLFS 8.68 instructions.
