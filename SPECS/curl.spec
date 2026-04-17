%define curl_version 8.17.0

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global curl_multilibdir /usr/lib/i386-linux-gnu
%global curl_enable_devel 0
%else
%global curl_multilibdir /usr/lib/x86_64-linux-gnu
%global curl_enable_devel 1
%endif

Name:           curl
Version:        %{curl_version}
Release:        1.m264%{?dist}
Summary:        Command line tool and library for transferring data with URLs

%if "%{_target_cpu}" == "x86_64"
Provides:       libcurl.so.4()(64bit)
%endif

License:        curl
URL:            https://curl.se/
Source0:        https://curl.se/download/curl-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconf
BuildRequires:  openssl
BuildRequires:  zlib

%description
curl is a command line tool and library for transferring data with URLs.

%if %{curl_enable_devel}
%package devel
Summary:        Development files for curl
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against libcurl.
%endif

%prep
%setup -q -n curl-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
export CPPFLAGS="${CPPFLAGS:-} -I/usr/include"
export LDFLAGS="${LDFLAGS:-} -L/usr/lib/i386-linux-gnu"
export PKG_CONFIG_LIBDIR="/usr/lib/i386-linux-gnu/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig"
CONFIG_HOST=--host=i686-pc-linux-gnu
CONFIG_LIBDIR=--libdir=/usr/lib/i386-linux-gnu
%else
export CPPFLAGS="${CPPFLAGS:-} -I/usr/include"
export LDFLAGS="${LDFLAGS:-} -L/usr/lib/x86_64-linux-gnu"
export PKG_CONFIG_LIBDIR="/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig"
CONFIG_HOST=""
CONFIG_LIBDIR=--libdir=/usr/lib/x86_64-linux-gnu
%endif

./configure \
    --prefix=%{_prefix} \
    ${CONFIG_LIBDIR} \
    ${CONFIG_HOST} \
    --disable-static \
    --with-openssl \
    --with-zlib \
    --without-libpsl \
    --disable-manual

make %{?_smp_mflags}

%check
:

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

rm -f %{buildroot}%{curl_multilibdir}/*.la || :
rm -f %{buildroot}%{curl_multilibdir}/*.a || :

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  if [ -d .%{curl_multilibdir} ]; then
    find .%{curl_multilibdir} -type f -o -type l
  fi
} | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/curl-files.list

test -s %{_builddir}/curl-files.list
%else
find . \( -type f -o -type l \) | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/curl-all.list

test -s %{_builddir}/curl-all.list

%if %{curl_enable_devel}
{
  if [ -d ./usr/include/curl ]; then
    find ./usr/include/curl -type f -o -type l
  fi
  if [ -d .%{curl_multilibdir} ]; then
    if [ -d .%{curl_multilibdir}/pkgconfig ]; then
      find .%{curl_multilibdir}/pkgconfig -type f -o -type l
    fi
    if [ -d .%{curl_multilibdir}/cmake ]; then
      find .%{curl_multilibdir}/cmake -type f -o -type l
    fi
    find .%{curl_multilibdir} -maxdepth 1 -type f -name 'libcurl.so'
    find .%{curl_multilibdir} -maxdepth 1 -type l -name 'libcurl.so'
  fi
  if [ -f ./usr/bin/curl-config ]; then
    echo ./usr/bin/curl-config
  fi
} | sed 's|^\.||' | LC_ALL=C sort -u > %{_builddir}/curl-devel.list

test -s %{_builddir}/curl-devel.list

grep -F -x -v -f %{_builddir}/curl-devel.list %{_builddir}/curl-all.list > %{_builddir}/curl-runtime.list

test -s %{_builddir}/curl-runtime.list
%else
cp %{_builddir}/curl-all.list %{_builddir}/curl-runtime.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/curl-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/curl-runtime.list
%defattr(-,root,root,-)

%if %{curl_enable_devel}
%files devel -f %{_builddir}/curl-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 8.17.0-1.m264
- Initial curl packaging with runtime and -devel split.
