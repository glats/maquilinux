%define mpc_version 1.3.1

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global mpc_multilibdir /usr/lib/i386-linux-gnu
%global mpc_enable_devel 0
%else
%global mpc_multilibdir /usr/lib/x86_64-linux-gnu
%global mpc_enable_devel 1
%endif

Name:           mpc
Version:        %{mpc_version}
Release:        1.m264%{?dist}
Summary:        Multiple precision complex arithmetic library

%if "%{_target_cpu}" == "x86_64"
Provides:       libmpc.so.3()(64bit)
%endif

License:        LGPLv3+
URL:            http://www.multiprecision.org/mpc/
Source0:        https://ftp.gnu.org/gnu/mpc/mpc-%{version}.tar.gz

%if %{mpc_enable_devel}
%package devel
Summary:        Development files for mpc
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers and the unversioned shared library symlink for developing against MPC.
%endif

%description
The GNU MPC library provides multiple-precision complex floating-point
computations with correct rounding. It is based on GMP and MPFR and is
used by software such as compilers that require precise complex arithmetic.

%prep
%setup -q -n mpc-%{version}

%build
%if "%{_target_cpu}" == "i686"
CFLAGS="${CFLAGS:-} -m32" \
CXXFLAGS="${CXXFLAGS:-} -m32" \
CPPFLAGS="${CPPFLAGS:-} -I/usr/include/i386-linux-gnu" \
LDFLAGS="${LDFLAGS:-} -L/usr/lib/i386-linux-gnu" \
CC="gcc -m32" CXX="g++ -m32" \
PKG_CONFIG=pkgconf \
PKG_CONFIG_LIBDIR="/usr/lib/i386-linux-gnu/pkgconfig:/usr/share/pkgconfig" \
export CFLAGS CXXFLAGS CPPFLAGS LDFLAGS PKG_CONFIG PKG_CONFIG_LIBDIR
./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --host=i686-pc-linux-gnu \
    --libdir=/usr/lib/i386-linux-gnu \
    --with-gmp-include=/usr/include/i386-linux-gnu \
    --with-gmp-lib=/usr/lib/i386-linux-gnu \
    --with-mpfr-include=/usr/include \
    --with-mpfr-lib=/usr/lib/i386-linux-gnu
%else
PKG_CONFIG=pkgconf \
PKG_CONFIG_LIBDIR="/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/share/pkgconfig" \
export PKG_CONFIG PKG_CONFIG_LIBDIR
./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --docdir=%{_datadir}/doc/mpc-%{version} \
    --libdir=/usr/lib/x86_64-linux-gnu \
    --with-gmp-include=/usr/include \
    --with-gmp-lib=/usr/lib/x86_64-linux-gnu \
    --with-mpfr-include=/usr/include \
    --with-mpfr-lib=/usr/lib/x86_64-linux-gnu
%endif

make %{?_smp_mflags}
%if "%{_target_cpu}" != "i686"
make html
%endif

%check
%if "%{_target_cpu}" == "i686"
make check || :
%else
make check
%endif

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install
%if "%{_target_cpu}" != "i686"
make DESTDIR=%{buildroot} install-html
%endif

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.a || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.la || :
%else
rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/*.a || :
rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/*.la || :
%endif

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{mpc_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/mpc-files.list
%else
# Runtime: versioned shared libs, info pages, docs
{
  find .%{mpc_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/share/info ]; then
    find ./usr/share/info -type f -o -type l
  fi
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/mpc-runtime.list

%if %{mpc_enable_devel}
# Development: headers, unversioned .so symlinks
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{mpc_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -d .%{mpc_multilibdir}/pkgconfig ]; then
    find .%{mpc_multilibdir}/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/mpc-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/mpc-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/mpc-runtime.list
%defattr(-,root,root,-)

%if %{mpc_enable_devel}
%files devel -f %{_builddir}/mpc-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.3.1-1.m264
- Initial RPM packaging for MPC.
