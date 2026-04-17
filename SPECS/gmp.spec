%define gmp_version 6.3.0

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global gmp_multilibdir /usr/lib/i386-linux-gnu
%global gmp_enable_devel 0
%else
%global gmp_multilibdir /usr/lib/x86_64-linux-gnu
%global gmp_enable_devel 1
%endif

Name:           gmp
Version:        %{gmp_version}
Release:        1.m264%{?dist}
Summary:        GNU multiple precision arithmetic library

%if "%{_target_cpu}" == "x86_64"
Provides:       libgmp.so.10()(64bit)
Provides:       libgmpxx.so.4()(64bit)
%endif

License:        LGPLv3+ and GPLv2+
URL:            https://gmplib.org/
Source0:        https://ftp.gnu.org/gnu/gmp/gmp-%{version}.tar.xz

%if %{gmp_enable_devel}
%package devel
Summary:        Development files for gmp
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers and the unversioned shared library symlinks for developing
against GNU MP.
%endif

%description
The GNU MP (GMP) library provides high-performance arithmetic on arbitrary
precision integers, rational numbers, and floating-point numbers. It
includes both C and C++ interfaces.

%prep
%setup -q -n gmp-%{version}

# Adjust configure for gcc-15 and later, per upstream/MLFS guidance
sed -i '/long long t1;/,+1s/()/(...)/' configure

%build
%if "%{_target_cpu}" == "i686"
cp -v configfsf.guess config.guess || :
cp -v configfsf.sub   config.sub   || :

ABI="32" \
CFLAGS="-m32 -O2 -pedantic -fomit-frame-pointer -mtune=generic -march=i686" \
CXXFLAGS="$CFLAGS" \
CPPFLAGS="-D__GMP_BITS_PER_MP_LIMB=32 -DGMP_NUMB_BITS=32 -DGMP_LIMB_BITS=32" \
PKG_CONFIG_PATH="/usr/lib/i386-linux-gnu/pkgconfig" \
ac_cv_prog_cc_works=yes \
ac_cv_prog_cxx_works=yes \
gmp_cv_cxx_works=yes \
gmp_cv_prog_cxx_works=yes \
gmp_cv_prog_cc_works=yes \
CC="gcc -m32" \
CXX="g++ -m32" \
CC_FOR_BUILD="gcc" \
CXX_FOR_BUILD="g++" \
MPN_PATH="x86 generic" \
./configure \
    --prefix=%{_prefix} \
    --build=x86_64-pc-linux-gnu \
    --host=i686-pc-linux-gnu \
    --disable-static \
    --enable-cxx \
    --libdir=/usr/lib/i386-linux-gnu
%else
./configure \
    --prefix=%{_prefix} \
    --enable-cxx \
    --disable-static \
    --docdir=%{_datadir}/doc/gmp-%{version} \
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
make check 2>&1 | tee gmp-check-log
awk '/# PASS:/{total+=$3} END{if (total < 199) {exit 1}}' gmp-check-log
%endif

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install
%if "%{_target_cpu}" != "i686"
make DESTDIR=%{buildroot} install-html
%endif

%if "%{_target_cpu}" == "i686"
# Move 32-bit headers into an arch-specific include dir to avoid conflicts
if [ -d "%{buildroot}%{_includedir}" ]; then
  install -vdm 755 "%{buildroot}%{_includedir}/i386-linux-gnu"
  for h in gmp.h gmpxx.h; do
    if [ -f "%{buildroot}%{_includedir}/$h" ]; then
      mv -v "%{buildroot}%{_includedir}/$h" "%{buildroot}%{_includedir}/i386-linux-gnu/"
    fi
  done
  # drop any stray top-level gmp headers left in the default include dir
  find "%{buildroot}%{_includedir}" -maxdepth 1 -type f -name 'gmp*.h' -delete || :
fi
%endif

# Prune and remove static libs accordingly
%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.a || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.la || :
# Ensure devel symlinks exist for dynamic linking during dependent 32-bit builds
if [ -d "%{buildroot}/usr/lib/i386-linux-gnu" ]; then
  pushd "%{buildroot}/usr/lib/i386-linux-gnu" >/dev/null
  if [ -e libgmp.so.10 ] && [ ! -e libgmp.so ]; then ln -sv libgmp.so.10 libgmp.so; fi
  if [ -e libgmpxx.so.4 ] && [ ! -e libgmpxx.so ]; then ln -sv libgmpxx.so.4 libgmpxx.so; fi
  popd >/dev/null
fi
%else
rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/*.a || :
rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/*.la || :
# Ensure devel symlinks exist for dynamic linking
if [ -d "%{buildroot}/usr/lib/x86_64-linux-gnu" ]; then
  pushd "%{buildroot}/usr/lib/x86_64-linux-gnu" >/dev/null
  if [ -e libgmp.so.10 ] && [ ! -e libgmp.so ]; then ln -sv libgmp.so.10 libgmp.so; fi
  if [ -e libgmpxx.so.4 ] && [ ! -e libgmpxx.so ]; then ln -sv libgmpxx.so.4 libgmpxx.so; fi
  popd >/dev/null
fi

# Provide a top-level linker-friendly symlink for 64-bit like other libs
install -vdm 755 %{buildroot}/usr/lib
ln -sv x86_64-linux-gnu/libgmp.so %{buildroot}/usr/lib/libgmp.so || :
ln -sv x86_64-linux-gnu/libgmpxx.so %{buildroot}/usr/lib/libgmpxx.so || :
%endif

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  if [ -d .%{gmp_multilibdir} ]; then
    find .%{gmp_multilibdir} -type f -o -type l
  fi
  if [ -d ./usr/include/i386-linux-gnu ]; then
    find ./usr/include/i386-linux-gnu -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/gmp-files.list
%else
# Runtime: versioned shared libs, info pages, docs
{
  find .%{gmp_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/share/info ]; then
    find ./usr/share/info -type f -o -type l
  fi
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/gmp-runtime.list

%if %{gmp_enable_devel}
# Development: headers, unversioned .so symlinks
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{gmp_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -f ./usr/lib/libgmp.so ]; then
    echo ./usr/lib/libgmp.so
  fi
  if [ -f ./usr/lib/libgmpxx.so ]; then
    echo ./usr/lib/libgmpxx.so
  fi
  if [ -d .%{gmp_multilibdir}/pkgconfig ]; then
    find .%{gmp_multilibdir}/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/gmp-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/gmp-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/gmp-runtime.list
%defattr(-,root,root,-)

%if %{gmp_enable_devel}
%files devel -f %{_builddir}/gmp-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 6.3.0-1.m264
- Initial RPM packaging for GMP with 64-bit and 32-bit libraries.
