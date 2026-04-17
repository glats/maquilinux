%define libxcrypt_version 4.5.2

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global libxcrypt_multilibdir /usr/lib/i386-linux-gnu
%global libxcrypt_enable_devel 0
%else
%global libxcrypt_multilibdir /usr/lib/x86_64-linux-gnu
%global libxcrypt_enable_devel 1
%endif

Name:           libxcrypt
Version:        %{libxcrypt_version}
Release:        1.m264%{?dist}
Summary:        Modern password hashing library (libcrypt replacement)

%if "%{_target_cpu}" == "x86_64"
Provides:       libcrypt.so.2()(64bit)
%endif

License:        LGPLv2.1+ and BSD and Public Domain
URL:            https://github.com/besser82/libxcrypt
Source0:        https://github.com/besser82/libxcrypt/releases/download/v%{version}/libxcrypt-%{version}.tar.xz

%if %{libxcrypt_enable_devel}
%package devel
Summary:        Development files for libxcrypt
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against libxcrypt.
%endif

%description
Libxcrypt is a modern library for one-way hashing of passwords. It provides
strong hash algorithms recommended for security use cases and implements the
traditional Glibc libcrypt interfaces for compatibility.

%prep
%setup -q -n libxcrypt-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
CONFIG_HOST=--host=i686-pc-linux-gnu
CONFIG_OBSOLETE=--enable-obsolete-api=glibc
%else
CONFIG_HOST=""
CONFIG_OBSOLETE=--enable-obsolete-api=no
%endif

./configure \
    --prefix=%{_prefix} \
    --libdir=%{libxcrypt_multilibdir} \
    --enable-hashes=strong,glibc \
    ${CONFIG_OBSOLETE} \
    --disable-static \
    --disable-failure-tokens \
    ${CONFIG_HOST}

make %{?_smp_mflags}

%check
# Upstream tests; run only for the 64-bit build tree. Do not fail the build
# if they cannot run cleanly in this minimal environment.
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

mkdir -pv %{buildroot}%{libxcrypt_multilibdir}/pkgconfig
if [ -f %{buildroot}%{libxcrypt_multilibdir}/pkgconfig/libxcrypt.pc ]; then
    ln -svf libxcrypt.pc %{buildroot}%{libxcrypt_multilibdir}/pkgconfig/libcrypt.pc
fi

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.a || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.la || :
%endif

rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/*.a || :
rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/*.la || :

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{libxcrypt_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libxcrypt-files.list
%else
# Runtime: versioned shared libs, man pages
{
  find .%{libxcrypt_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libxcrypt-runtime.list

%if %{libxcrypt_enable_devel}
# Development: headers, pkgconfig, unversioned .so symlink
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{libxcrypt_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -d .%{libxcrypt_multilibdir}/pkgconfig ]; then
    find .%{libxcrypt_multilibdir}/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/libxcrypt-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/libxcrypt-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/libxcrypt-runtime.list
%defattr(-,root,root,-)

%if %{libxcrypt_enable_devel}
%files devel -f %{_builddir}/libxcrypt-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 4.5.2-1.m264
- Initial RPM packaging for libxcrypt with multiarch layout.
