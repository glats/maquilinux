Name:           procps-ng
Version:        4.0.5
Release:        1.m264%{?dist}
Summary:        Process monitoring utilities and libraries

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-or-later
URL:            https://gitlab.com/procps-ng/procps
Source0:        https://download.savannah.gnu.org/releases/procps-ng/procps-ng-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  ncurses
BuildRequires:  pkgconf
BuildRequires:  libtool

%description
Procps-ng provides the standard Linux utilities for monitoring processes and
system resources (ps, top, free, vmstat, sysctl, and more), along with the
libproc shared library.

%prep
%autosetup -n procps-ng-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
LIBDIR=/usr/lib/i386-linux-gnu
%else
LIBDIR=/usr/lib/x86_64-linux-gnu
%endif

SYSTEMD_OPT=""
if ./configure --help 2>/dev/null | grep -q -- '--with-systemd'; then
    SYSTEMD_OPT="--without-systemd"
fi

./configure --prefix=%{_prefix} \
            --docdir=%{_datadir}/doc/procps-ng-%{version} \
            --sysconfdir=%{_sysconfdir} \
            --libdir=${LIBDIR} \
            --disable-static \
            --disable-kill \
            --enable-watch8bit \
            ${SYSTEMD_OPT}
make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_docdir}/procps-ng-%{version} || :
rm -rf %{buildroot}/etc || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/procps-ng-files.list

%files -f %{_builddir}/procps-ng-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 4.0.5-1.m264
- Initial packaging aligned with MLFS 8.81 instructions (watch 8-bit, no kill).
