Name:           kmod
Version:        34.2
Release:        1.m264%{?dist}
Summary:        Tools and libraries for loading kernel modules

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-or-later and LGPL-2.1-or-later
URL:            https://git.kernel.org/pub/scm/utils/kernel/kmod/kmod.git
Source0:        https://www.kernel.org/pub/linux/utils/kernel/kmod/kmod-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  meson
BuildRequires:  ninja
BuildRequires:  pkgconf
BuildRequires:  zlib-devel
BuildRequires:  xz
BuildRequires:  python3

%description
Kmod provides the kmod library and utilities used to load, query, and manage
Linux kernel modules, including depmod and modprobe.

%prep
%autosetup -n kmod-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32 -march=i686"
export CXX="g++ -m32 -march=i686"
export PKG_CONFIG_PATH="/usr/lib/i386-linux-gnu/pkgconfig"
LIBDIR=/usr/lib/i386-linux-gnu
%else
LIBDIR=/usr/lib/x86_64-linux-gnu
%endif

mkdir -p build
cd build
meson setup .. \
    --prefix=%{_prefix} \
    --libdir=${LIBDIR} \
    --buildtype=release \
    -Dmanpages=false

ninja %{?_smp_mflags}

%install
rm -rf %{buildroot}
cd build
DESTDIR=%{buildroot} ninja install

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
cd %{buildroot}
{
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu -type f -o -type l | sed 's|^\.||'
  fi
} > %{_builddir}/kmod-files.list
%else
cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/kmod-files.list
%endif

%files -f %{_builddir}/kmod-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 34.2-1.m264
- Initial packaging aligned with MLFS 8.61 instructions (multilib layout).
