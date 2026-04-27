%define pkg_version 3.0.1

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global pkg_multilibdir /usr/lib/i386-linux-gnu
%global pkg_enable_devel 0
%else
%global pkg_multilibdir /usr/lib/x86_64-linux-gnu
%global pkg_enable_devel 1
%endif

Name:           libassuan
Version:        %{pkg_version}
Release:        1.m264%{?dist}
Summary:        IPC library for the GnuPG components

License:        LGPL-2.1-or-later AND GPL-3.0-or-later
URL:            https://www.gnupg.org/related_software/libassuan/
Source0:        https://gnupg.org/ftp/gcrypt/libassuan/libassuan-%{version}.tar.bz2

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  libgpg-error-devel

Requires:       libgpg-error

%if "%{_target_cpu}" == "x86_64"
Provides:       libassuan.so.9()(64bit)
%endif

%description
Libassuan is a small library implementing the so-called "Assuan protocol".
This protocol is used for IPC between most newer GnuPG components. Libassuan's
primary use is as a IPC system for GnuPG, gpgme and similar packages.

%if %{pkg_enable_devel}
%package devel
Summary:        Development files for libassuan
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       libgpg-error-devel

%description devel
The libassuan-devel package contains libraries and header files for developing
applications that use libassuan.
%endif

%prep
%setup -q

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
export PKG_CONFIG_LIBDIR="/usr/lib/i386-linux-gnu/pkgconfig:/usr/share/pkgconfig"
CONFIG_HOST=--host=i686-pc-linux-gnu
%else
export PKG_CONFIG_LIBDIR="/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/share/pkgconfig"
CONFIG_HOST=""
%endif

export CFLAGS="-std=gnu17 ${CFLAGS:-}"

./configure \
    --prefix=%{_prefix} \
    --libdir=%{pkg_multilibdir} \
    --enable-shared \
    --disable-static \
    --with-libgpg-error-prefix=%{_prefix} \
    ${CONFIG_HOST} \
    CFLAGS="${CFLAGS}"

make %{?_smp_mflags} CFLAGS="${CFLAGS}"

%install
make DESTDIR=%{buildroot} install

rm -fv %{buildroot}%{pkg_multilibdir}/*.la || :
rm -fv %{buildroot}%{pkg_multilibdir}/*.a || :
rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_infodir} || :
%endif

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  if [ -d .%{pkg_multilibdir} ]; then
    find .%{pkg_multilibdir} -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libassuan-files.list
%else
find . \( -type f -o -type l \) | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libassuan-all.list

{
  if [ -d .%{pkg_multilibdir} ]; then
    find .%{pkg_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libassuan.so.*'
  fi
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libassuan-runtime.list

%if %{pkg_enable_devel}
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d .%{pkg_multilibdir}/pkgconfig ]; then
    find .%{pkg_multilibdir}/pkgconfig -type f -o -type l
  fi
  if [ -d .%{pkg_multilibdir} ]; then
    find .%{pkg_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libassuan.so'
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libassuan-devel.list
%endif
%endif

%post
%{_sbindir}/ldconfig || :

%postun
%{_sbindir}/ldconfig || :

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/libassuan-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/libassuan-runtime.list
%defattr(-,root,root,-)

%if %{pkg_enable_devel}
%files devel -f %{_builddir}/libassuan-devel.list
%defattr(-,root,root,-)
%endif
%endif

%changelog
* Sun Apr 19 2026 Maqui Linux <security@maqui-linux.org> - 3.0.1-1.m264
- Initial build for Maqui Linux 26.4
- Gen3 template: pkg_multilibdir, generated file lists, multiarch