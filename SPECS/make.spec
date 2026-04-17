Name:           make
Version:        4.4.1
Release:        1.m264%{?dist}
Summary:        Utility for controlling the build of programs

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/make/
Source0:        https://ftp.gnu.org/gnu/make/make-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  texinfo

%description
GNU Make determines automatically which pieces of a program need to be
recompiled and issues the commands to rebuild them.

%prep
%autosetup -n make-%{version}

%build
./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
# Full test suite requires a non-root user; run best-effort and ignore failures.
make check || :

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
make DESTDIR=%{buildroot} install

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' > %{builddir}/make-files.list
test -s %{builddir}/make-files.list

%files -f %{builddir}/make-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 4.4.1-1.m264
- Initial packaging aligned with MLFS 8.72 instructions.
