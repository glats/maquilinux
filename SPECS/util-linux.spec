Name:           util-linux
Version:        2.41.2
Release:        1.m264%{?dist}
Summary:        Essential system utilities (mount, fdisk, more)

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-or-later and BSD and Public Domain
URL:            https://www.kernel.org/pub/linux/utils/util-linux/
Source0:        https://www.kernel.org/pub/linux/utils/util-linux/v%{version}/util-linux-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconf
BuildRequires:  zlib
BuildRequires:  libcap
BuildRequires:  readline
BuildRequires:  ncurses
BuildRequires:  bzip2
BuildRequires:  xz

%description
Util-linux provides a large collection of essential low-level system utilities,
including mount/umount, fdisk family tools, hwclock, logger, and various
helpers required early in boot.

%prep
%autosetup -n util-linux-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
LIBDIR=/usr/lib/i386-linux-gnu
%else
LIBDIR=/usr/lib/x86_64-linux-gnu
%endif

./configure --prefix=%{_prefix} \
            --bindir=%{_bindir} \
            --sbindir=%{_sbindir} \
            --libdir=${LIBDIR} \
            --runstatedir=/run \
            --docdir=%{_datadir}/doc/util-linux-%{version} \
            --sysconfdir=%{_sysconfdir} \
            --disable-chfn-chsh \
            --disable-login \
            --disable-nologin \
            --disable-su \
            --disable-setpriv \
            --disable-runuser \
            --disable-pylibmount \
            --disable-liblastlog2 \
            --disable-static \
            --without-python \
            --without-systemd \
            --without-systemdsystemunitdir \
            --without-systemdtmpfilesdir \
            ADJTIME_PATH=%{_localstatedir}/lib/hwclock/adjtime
make %{?_smp_mflags}

%check
make -k check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

install -d %{buildroot}/%{_localstatedir}/lib/hwclock

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_docdir}/util-linux-%{version} || :
rm -rf %{buildroot}%{_sysconfdir} || :
rm -rf %{buildroot}/run || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/util-linux-files.list

%files -f %{_builddir}/util-linux-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.41.2-1.m264
- Initial packaging aligned with MLFS 8.82 instructions (utility disables, hwclock path).
