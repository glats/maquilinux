%define pkg_version 3.10

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

Name:           nettle
Version:        %{pkg_version}
Release:        1.m264%{?dist}
Summary:        A low-level cryptographic library

License:        LGPL-3.0-or-later AND GPL-2.0-or-later
URL:            https://www.lysator.liu.se/~nisse/nettle/
Source0:        https://ftp.gnu.org/gnu/nettle/nettle-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  gmp-devel

Requires:       gmp

%if "%{_target_cpu}" == "x86_64"
Provides:       libnettle.so.8()(64bit)
Provides:       libhogweed.so.6()(64bit)
%endif

%description
Nettle is a cryptographic library that is designed to fit easily in more or less
any context: In crypto toolkits for object-oriented languages (C++, Python, Pike,
etc.), in applications like LSH or GnuPG, or even in kernel space. It is written
in an object-oriented manner with many objects and flexible functions.

%if %{pkg_enable_devel}
%package devel
Summary:        Development files for nettle
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       gmp-devel

%description devel
The nettle-devel package contains libraries and header files for developing
applications that use nettle.
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
    ${CONFIG_HOST} \
    CFLAGS="${CFLAGS}"

make %{?_smp_mflags}

%install
make DESTDIR=%{buildroot} install

rm -fv %{buildroot}%{pkg_multilibdir}/*.a || :
rm -fv %{buildroot}%{pkg_multilibdir}/*.la || :
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
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/nettle-files.list
%else
find . \( -type f -o -type l \) | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/nettle-all.list

{
  if [ -d .%{pkg_multilibdir} ]; then
    find .%{pkg_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libnettle.so.*'
    find .%{pkg_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libhogweed.so.*'
  fi
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/nettle-runtime.list

%if %{pkg_enable_devel}
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d .%{pkg_multilibdir}/pkgconfig ]; then
    find .%{pkg_multilibdir}/pkgconfig -type f -o -type l
  fi
  if [ -d .%{pkg_multilibdir} ]; then
    find .%{pkg_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libnettle.so'
    find .%{pkg_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libhogweed.so'
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/nettle-devel.list
%endif
%endif

%post
%{_sbindir}/ldconfig || :

%postun
%{_sbindir}/ldconfig || :

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/nettle-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/nettle-runtime.list
%defattr(-,root,root,-)

%if %{pkg_enable_devel}
%files devel -f %{_builddir}/nettle-devel.list
%defattr(-,root,root,-)
%endif
%endif

%changelog
* Sun Apr 19 2026 Maqui Linux <security@maqui-linux.org> - 3.10-1.m264
- Initial build for Maqui Linux 26.4
- Gen3 template: pkg_multilibdir, generated file lists, multiarch