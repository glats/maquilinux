%define openssl_version 3.6.0

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global openssl_multilibdir /usr/lib/i386-linux-gnu
%global openssl_enable_devel 0
%else
%global openssl_multilibdir /usr/lib/x86_64-linux-gnu
%global openssl_enable_devel 1
%endif

Name:           openssl
Version:        %{openssl_version}
Release:        1.m264%{?dist}
Summary:        TLS/SSL toolkit and crypto library

%if "%{_target_cpu}" == "x86_64"
Provides:       libssl.so.3()(64bit)
Provides:       libcrypto.so.3()(64bit)
%endif

License:        Apache-2.0
URL:            https://www.openssl.org/
Source0:        https://www.openssl.org/source/openssl-%{version}.tar.gz

%if %{openssl_enable_devel}
%package devel
Summary:        Development files for openssl
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlinks
for developing against OpenSSL.
%endif

BuildRequires:  perl

%description
OpenSSL provides cryptographic libraries libssl and libcrypto plus the
openssl tool for managing certificates, keys, and TLS/SSL connections.

%prep
%setup -q -n openssl-%{version}

%build
%if "%{_target_cpu}" == "i686"
CC="gcc -m32" ./config \
    --prefix=/usr \
    --openssldir=/etc/ssl \
    --libdir=/usr/lib/i386-linux-gnu \
    shared \
    zlib-dynamic \
    linux-x86
%else
./config \
    --prefix=/usr \
    --openssldir=/etc/ssl \
    --libdir=/usr/lib/x86_64-linux-gnu \
    shared \
    zlib-dynamic
%endif

make %{?_smp_mflags}

%check
HARNESS_JOBS=%{?_smp_build_ncpus} make test || :

%install
rm -rf %{buildroot}
sed -i '/INSTALL_LIBS/s/libcrypto.a libssl.a//' Makefile
make MANSUFFIX=ssl DESTDIR=%{buildroot} install

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_sysconfdir}/ssl || :
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_libdir}/engines* || :
%else
if [ -d %{buildroot}%{_datadir}/doc/openssl ]; then
  mv %{buildroot}%{_datadir}/doc/openssl %{buildroot}%{_datadir}/doc/openssl-%{version}
fi
mkdir -p %{buildroot}%{_datadir}/doc/openssl-%{version}
cp -a doc/* %{buildroot}%{_datadir}/doc/openssl-%{version}/
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{openssl_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/openssl-files.list
%else
# Runtime: versioned shared libs, binaries, config, engines, man pages, docs
{
  find .%{openssl_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d .%{openssl_multilibdir}/engines-3 ]; then
    find .%{openssl_multilibdir}/engines-3 -type f -o -type l
  fi
  if [ -d .%{openssl_multilibdir}/ossl-modules ]; then
    find .%{openssl_multilibdir}/ossl-modules -type f -o -type l
  fi
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
  if [ -d ./etc/ssl ]; then
    find ./etc/ssl -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/openssl-runtime.list

%if %{openssl_enable_devel}
# Development: headers, pkgconfig, unversioned .so symlinks
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{openssl_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -d .%{openssl_multilibdir}/pkgconfig ]; then
    find .%{openssl_multilibdir}/pkgconfig -type f -o -type l
  fi
  if [ -d .%{openssl_multilibdir}/cmake ]; then
    find .%{openssl_multilibdir}/cmake -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/openssl-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/openssl-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/openssl-runtime.list
%defattr(-,root,root,-)

%if %{openssl_enable_devel}
%files devel -f %{_builddir}/openssl-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.6.0-1.m264
- OpenSSL initial RPM packaging.
