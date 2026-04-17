Name:           autoconf
Version:        2.72
Release:        1.m264%{?dist}
Summary:        Generates configure scripts for building packages

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPLv3+
URL:            https://www.gnu.org/software/autoconf/
Source0:        https://ftp.gnu.org/gnu/autoconf/autoconf-%{version}.tar.xz

%description
Autoconf is a tool for producing shell scripts that automatically configure
software source code packages to adapt to many kinds of Unix-like systems.

%prep
%setup -q -n autoconf-%{version}

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
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/autoconf-files.list

%files -f %{_builddir}/autoconf-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.72-1.m264
- Initial packaging aligned with MLFS 8.48 instructions.
