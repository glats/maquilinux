Name:           gcc
Version:        15.2.0
Release:        1.m264%{?dist}
Summary:        GNU Compiler Collection (C and C++)

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        GPLv3+ and GPLv3+ with exceptions
URL:            https://gcc.gnu.org/
Source0:        https://ftp.gnu.org/gnu/gcc/gcc-%{version}/gcc-%{version}.tar.xz
Provides:       gcc-c++ = %{version}-%{release}

%description
The GCC package contains the GNU Compiler Collection, including the C and
C++ compilers and runtime libraries. This build enables PIE and SSP by
default and supports both 64-bit and 32-bit variants in a multiarch layout.

%prep
%setup -q -n gcc-%{version}

# Adjust the 64-bit library directory mapping so that 64-bit libraries
# use lib instead of lib64.
sed -e '/m64=/s/lib64/lib/' \
    -i.orig gcc/config/i386/t-linux64

# Out-of-tree build directory as recommended by GCC.
mkdir -v build

%build
cd build

# Choose multilib variants depending on target package arch
%if "%{_target_cpu}" == "i686"
mlist=m32
deps_libdir=/usr/lib/i386-linux-gnu
gmp_includedir=/usr/include/i386-linux-gnu
mpfr_includedir=/usr/include
mpc_includedir=/usr/include
export CC="gcc -m32"
export CXX="g++ -m32"
%else
mlist=m64,m32
deps_libdir=/usr/lib/x86_64-linux-gnu
gmp_includedir=/usr/include
mpfr_includedir=/usr/include
mpc_includedir=/usr/include
%endif

CPPFLAGS="${CPPFLAGS:-} -I${gmp_includedir} -I${mpfr_includedir} -I${mpc_includedir}"
LDFLAGS="${LDFLAGS:-} -L${deps_libdir}"
export CPPFLAGS LDFLAGS

SED=sed \
LD=ld \
../configure \
    --prefix=%{_prefix} \
    --enable-languages=c,c++ \
    --enable-default-pie \
    --enable-default-ssp \
    --enable-host-pie \
    --enable-multilib \
    --with-multilib-list=${mlist} \
    --disable-bootstrap \
    --disable-fixincludes \
    --with-system-zlib \
    --with-gmp-include=${gmp_includedir} \
    --with-gmp-lib=${deps_libdir} \
    --with-mpfr-include=${mpfr_includedir} \
    --with-mpfr-lib=${deps_libdir} \
    --with-mpc-include=${mpc_includedir} \
    --with-mpc-lib=${deps_libdir}

make %{?_smp_mflags}

%check
cd build

# Ensure enough stack for some complex tests.
ulimit -s -H unlimited || :

# Remove a known problematic test, matching the MLFS instructions.
sed -e '/cpython/d' -i ../gcc/testsuite/gcc.dg/plugin/plugin.exp || :

# Run the test suite but do not fail the build on unexpected failures in
# this constrained environment. First-time builders are encouraged to
# inspect the summary.
make -k check || :

../contrib/test_summary || :

%install
cd build
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

# Fix ownership of the installed headers as per LFS instructions.
chown -v -R root:root \
    %{buildroot}/usr/lib/gcc/$(gcc -dumpmachine)/%{version}/include{,-fixed} || :

%if "%{_target_cpu}" != "i686"
# GCC multilib (m64,m32) installs 32-bit libs in /usr/lib32. Since we use a symlink
# /usr/lib32 -> /usr/lib/i386-linux-gnu, verify content is in correct place.
if [ -d %{buildroot}/usr/lib32 ] && [ ! -L %{buildroot}/usr/lib32 ]; then
  mkdir -pv %{buildroot}/usr/lib/i386-linux-gnu
  cp -av %{buildroot}/usr/lib32/* %{buildroot}/usr/lib/i386-linux-gnu/ || :
  rm -rf %{buildroot}/usr/lib32
fi

# FHS symlink for historical /lib/cpp path.
install -vdm 755 %{buildroot}/lib
ln -svr %{_bindir}/cpp %{buildroot}/lib || :

# cc symlink to gcc.
install -vdm 755 %{buildroot}%{_bindir}
ln -sv gcc %{buildroot}%{_bindir}/cc || :

# LTO plugin symlink for Binutils bfd plugins.
install -vdm 755 %{buildroot}/usr/lib/bfd-plugins
ln -sfv ../../libexec/gcc/$(gcc -dumpmachine)/%{version}/liblto_plugin.so \
    %{buildroot}/usr/lib/bfd-plugins/ || :

# Move gdb auto-load scripts to the canonical location.
install -vdm 755 %{buildroot}/usr/share/gdb/auto-load/usr/lib
if ls %{buildroot}/usr/lib/*gdb.py >/dev/null 2>&1; then
    mv -v %{buildroot}/usr/lib/*gdb.py \
       %{buildroot}/usr/share/gdb/auto-load/usr/lib
fi
%else
# i686 package is libs-only. If GCC installed 32-bit runtime libs under /usr/lib32,
# mirror them into the Debian-like multiarch dir so consumers can link there.
if [ -d %{buildroot}/usr/lib32 ]; then
  mkdir -pv %{buildroot}/usr/lib/i386-linux-gnu
  cp -av %{buildroot}/usr/lib32/* %{buildroot}/usr/lib/i386-linux-gnu/ || :
  rm -rf %{buildroot}/usr/lib32 || :
fi

# Prune non-library content. The i686 RPM should only ship runtime libs.
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}/usr/libexec || :

# Drop GCC internal non-runtime content.
rm -rf %{buildroot}/usr/lib/gcc/*/*/include || :
rm -rf %{buildroot}/usr/lib/gcc/*/*/include-fixed || :
rm -rf %{buildroot}/usr/lib/gcc/*/*/install-tools || :
rm -rf %{buildroot}/usr/lib/gcc/*/*/plugin || :

# Drop compiler support objects and static archives that are not runtime.
rm -fv %{buildroot}/usr/lib/gcc/*/*/crt*.o || :
rm -fv %{buildroot}/usr/lib/gcc/*/*/libgcc*.a || :
rm -fv %{buildroot}/usr/lib/gcc/*/*/libgcov.a || :

# Drop static archives in the libs-only i686 RPM.
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.a || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.la || :
rm -fv %{buildroot}/usr/lib32/*.a || :
rm -fv %{buildroot}/usr/lib32/*.la || :

# If any libraries were installed into the non-multiarch /usr/lib, remove them.
# The i686 RPM should carry 32-bit runtime libs only under /usr/lib/i386-linux-gnu.
rm -fv %{buildroot}/usr/lib/libasan* || :
rm -fv %{buildroot}/usr/lib/libatomic* || :
rm -fv %{buildroot}/usr/lib/libcc1* || :
rm -fv %{buildroot}/usr/lib/libgomp* || :
rm -fv %{buildroot}/usr/lib/libhwasan* || :
rm -fv %{buildroot}/usr/lib/libitm* || :
rm -fv %{buildroot}/usr/lib/liblsan* || :
rm -fv %{buildroot}/usr/lib/libquadmath* || :
rm -fv %{buildroot}/usr/lib/libssp* || :
rm -fv %{buildroot}/usr/lib/libstdc++* || :
rm -fv %{buildroot}/usr/lib/libsupc++* || :
rm -fv %{buildroot}/usr/lib/libtsan* || :
rm -fv %{buildroot}/usr/lib/libubsan* || :
rm -fv %{buildroot}/usr/lib/libgcc_s* || :
rm -fv %{buildroot}/usr/lib/libsanitizer.spec || :
%endif

# Do not own the shared Info directory index.
rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
cd %{buildroot}
{
  # Prefer multiarch 32-bit runtime dir if populated
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu \( -type f -o -type l \)
  fi
  # Also include 32-bit multilib subdir inside GCC if present
  if compgen -G './usr/lib*/gcc/*/*/32/*' > /dev/null; then
    find ./usr/lib*/gcc/*/*/32 \( -type f -o -type l \)
  fi
  # Fallback: include top-level 32-bit runtime libs if placed in /usr/lib
  if compgen -G './usr/lib/libgcc_s*.so*' > /dev/null; then
    ls -1 ./usr/lib/libgcc_s*.so* || :
  fi
  if compgen -G './usr/lib/libstdc++*.so*' > /dev/null; then
    ls -1 ./usr/lib/libstdc++*.so* || :
  fi
} | sed 's|^\.||' > %{_builddir}/gcc-files.list
%else
cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/gcc-files.list
%endif

%files -f %{_builddir}/gcc-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 15.2.0-1.m264
- Initial RPM packaging for GCC 15.2.0 with multiarch support.
