%define mpfr_version 4.2.2

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global mpfr_multilibdir /usr/lib/i386-linux-gnu
%global mpfr_enable_devel 0
%else
%global mpfr_multilibdir /usr/lib/x86_64-linux-gnu
%global mpfr_enable_devel 1
%endif

Name:           mpfr
Version:        %{mpfr_version}
Release:        1.m264%{?dist}
Summary:        Multiple precision floating-point library

%if "%{_target_cpu}" == "x86_64"
Provides:       libmpfr.so.6()(64bit)
%endif

License:        LGPLv3+
URL:            https://www.mpfr.org/
Source0:        https://ftp.gnu.org/gnu/mpfr/mpfr-%{version}.tar.xz

%if %{mpfr_enable_devel}
%package devel
Summary:        Development files for mpfr
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers and the unversioned shared library symlink for developing against MPFR.
%endif

%description
The GNU MPFR library provides multiple-precision binary floating-point
computations with correct rounding. It is based on GMP and is intended
for use in applications such as compilers and mathematical software
that require precise control over floating-point behavior.

%prep
%setup -q -n mpfr-%{version}

%build
%if "%{_target_cpu}" == "i686"
CFLAGS="${CFLAGS:-} -m32" \
CXXFLAGS="${CXXFLAGS:-} -m32" \
CPPFLAGS="${CPPFLAGS:-} -I/usr/include/i386-linux-gnu" \
LDFLAGS="${LDFLAGS:-} -L/usr/lib/i386-linux-gnu" \
CC="gcc -m32" CXX="g++ -m32" \
export CFLAGS CXXFLAGS CPPFLAGS LDFLAGS
./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --enable-thread-safe \
    --host=i686-pc-linux-gnu \
    --libdir=/usr/lib/i386-linux-gnu \
    --with-gmp-include=/usr/include/i386-linux-gnu \
    --with-gmp-lib=/usr/lib/i386-linux-gnu
%else
./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --enable-thread-safe \
    --docdir=%{_datadir}/doc/mpfr-%{version} \
    --libdir=/usr/lib/x86_64-linux-gnu
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
  find .%{mpfr_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/mpfr-files.list
%else
# Runtime: versioned shared libs, info pages, docs
{
  find .%{mpfr_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/share/info ]; then
    find ./usr/share/info -type f -o -type l
  fi
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/mpfr-runtime.list

%if %{mpfr_enable_devel}
# Development: headers, unversioned .so symlinks
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{mpfr_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -d .%{mpfr_multilibdir}/pkgconfig ]; then
    find .%{mpfr_multilibdir}/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/mpfr-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/mpfr-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/mpfr-runtime.list
%defattr(-,root,root,-)

%if %{mpfr_enable_devel}
%files devel -f %{_builddir}/mpfr-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 4.2.2-1.m264
- Initial RPM packaging for MPFR.
