Name:           gawk
Version:        5.3.2
Release:        1.m264%{?dist}
Summary:        GNU implementation of the AWK programming language

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/gawk/
Source0:        https://ftp.gnu.org/gnu/gawk/gawk-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  texinfo

%description
Gawk is the GNU version of the AWK programming language, used for text
processing and data extraction.

%prep
%autosetup -n gawk-%{version}
sed -i 's/extras//' Makefile.in

%build
./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
# Full test suite requires non-root user; run best-effort and ignore failures.
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
ln -sf gawk.1 %{buildroot}/usr/share/man/man1/awk.1

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/gawk-files.list

%files -f %{_builddir}/gawk-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 5.3.2-1.m264
- Initial packaging aligned with MLFS 8.64 instructions.
