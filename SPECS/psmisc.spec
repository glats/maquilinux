Name:           psmisc
Version:        23.7
Release:        1.m264%{?dist}
Summary:        Utilities for displaying information about running processes

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        GPLv2+
URL:            https://gitlab.com/psmisc/psmisc
Source0:        psmisc-%{version}.tar.xz

%description
Psmisc provides utilities to display information about running processes and
related resources: fuser, killall, peekfd, prtstat, pslog, pstree, and pstree.x11.

%prep
%setup -q -n psmisc-%{version}

%build
./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
# Run test suite but do not fail the build in the minimal chroot environment.
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/psmisc-files.list

%files -f %{_builddir}/psmisc-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 23.7-1.m264
- Initial RPM packaging for psmisc.
