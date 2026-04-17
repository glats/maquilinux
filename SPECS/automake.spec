Name:           automake
Version:        1.18.1
Release:        1.m264%{?dist}
Summary:        Generates Makefile.in files for use with Autoconf

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPLv2+
URL:            https://www.gnu.org/software/automake/
Source0:        https://ftp.gnu.org/gnu/automake/automake-%{version}.tar.xz

%description
Automake is a tool for automatically generating Makefile.in files from
Makefile.am templates, typically used alongside Autoconf.

%prep
%setup -q -n automake-%{version}

%build
./configure \
    --prefix=%{_prefix} \
    --docdir=%{_datadir}/doc/automake-%{version}

make %{?_smp_mflags}

%check
check_jobs=$(nproc 2>/dev/null || echo 1)
if [ "$check_jobs" -lt 4 ]; then
  check_jobs=4
fi
make -j"$check_jobs" check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/automake-files.list

%files -f %{_builddir}/automake-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.18.1-1.m264
- Initial packaging aligned with MLFS 8.49 instructions.
