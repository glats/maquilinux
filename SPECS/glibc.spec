%define glibc_version 2.42
%define kernel_version 5.4

# This spec is used in a minimal LFS-style chroot where the standard
# debuginfo tools (find-debuginfo, debugedit, etc.) are not available.
# Disable automatic debuginfo generation so rpmbuild does not try to
# call /usr/bin/find-debuginfo, and disable post-install BRP scripts.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

Name:           glibc
Version:        %{glibc_version}
Release:        1.m264%{?dist}
Summary:        The GNU C Library
License:        LGPLv2+ and LGPLv2+ with exceptions and GPLv2+ and GPLv2+ with exceptions and BSD and ISC and Public Domain and GFDL
URL:            https://www.gnu.org/software/libc/

Source0:        https://ftp.gnu.org/gnu/glibc/glibc-%{version}.tar.xz
Patch0:         glibc-%{version}-upstream_fixes-1.patch
Patch1:         glibc-%{version}-fhs-1.patch

Provides:       rtld(GNU_HASH)

%description
The GNU C Library (glibc) is the standard C library for GNU/Linux systems.
It provides the system calls and basic functions such as open, malloc, printf, etc.
This package contains the shared libraries needed by almost all programs.

%prep
%setup -q -n glibc-%{version}

# Apply upstream fixes and FHS patches from local SOURCES (already present in /sources)
patch -Np1 -i %{PATCH0}
patch -Np1 -i %{PATCH1}

%build
%if "%{_target_cpu}" == "i686"
mkdir -v build32
cd build32
echo "rootsbindir=%{_sbindir}" > configparms

CC="gcc -m32" CXX="g++ -m32" \
../configure \
    --prefix=%{_prefix} \
    --build=$(../scripts/config.guess) \
    --host=i686-pc-linux-gnu \
    --disable-werror \
    --disable-nscd \
    --enable-kernel=%{kernel_version} \
    --enable-stack-protector=strong \
    --enable-multi-arch \
    --libdir=/usr/lib/i386-linux-gnu \
    --libexecdir=/usr/lib/i386-linux-gnu \
    libc_cv_slibdir=/usr/lib/i386-linux-gnu

make %{?_smp_mflags}
cd ..
%else
mkdir -v build
cd build
echo "rootsbindir=%{_sbindir}" > configparms

../configure \
    --prefix=%{_prefix} \
    --build=$(../scripts/config.guess) \
    --disable-werror \
    --disable-nscd \
    --enable-kernel=%{kernel_version} \
    --enable-stack-protector=strong \
    --enable-multi-arch \
    --libdir=/usr/lib/x86_64-linux-gnu \
    --libexecdir=/usr/lib/x86_64-linux-gnu \
    libc_cv_slibdir=/usr/lib/x86_64-linux-gnu

make %{?_smp_mflags}
cd ..
%endif

%install
rm -rf %{buildroot}

%if "%{_target_cpu}" == "i686"
cd build32
rm -rf DESTDIR
make DESTDIR=$PWD/DESTDIR install

mkdir -pv %{buildroot}/usr/lib
cp -av DESTDIR/usr/lib/i386-linux-gnu %{buildroot}/usr/lib/ || :

# Provide 32-bit loader link (will resolve via /lib -> usr/lib)
ln -sv i386-linux-gnu/ld-linux.so.2 \
    %{buildroot}/usr/lib/ld-linux.so.2

install -vdm 755 %{buildroot}%{_sysconfdir}/ld.so.conf.d
echo "/usr/lib/i386-linux-gnu" > %{buildroot}%{_sysconfdir}/ld.so.conf.d/i386-linux-gnu.conf

# Install only the 32-bit gnu headers needed
install -vdm 755 %{buildroot}/usr/include/gnu
install -vm644 DESTDIR/usr/include/gnu/{lib-names,stubs}-32.h \
    %{buildroot}/usr/include/gnu/ || :
cd ..
%else
cd build
make install DESTDIR=%{buildroot}
cd ..

# Loader symlinks for compatibility with common interpreter paths
# Real loaders live in the multiarch directories set by libc_cv_slibdir.
# Here we provide extra links so that paths like /lib64/ld-linux-x86-64.so.2 work
ln -sv x86_64-linux-gnu/ld-linux-x86-64.so.2 \
    %{buildroot}/usr/lib/ld-linux-x86-64.so.2
ln -sv ld-linux-x86-64.so.2 \
    %{buildroot}/usr/lib/ld-lsb-x86-64.so.3

install -vdm 755 %{buildroot}/usr/lib

# Fix hardcoded path in ldd script as per LFS
sed '/RTLDLIST=/s@%{_prefix}@@g' -i %{buildroot}%{_bindir}/ldd
sed -i 's@^RTLDLIST=.*@RTLDLIST="/lib64/ld-linux-x86-64.so.2 /lib/ld-linux.so.2"@' \
    %{buildroot}%{_bindir}/ldd

install -vdm 755 %{buildroot}%{_sysconfdir}/ld.so.conf.d
echo "/usr/lib/x86_64-linux-gnu" > %{buildroot}%{_sysconfdir}/ld.so.conf.d/x86_64-linux-gnu.conf
%endif

# Generate a file list for this build
%if "%{_target_cpu}" == "i686"
cd %{buildroot}
{
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu -type f -o -type l
  fi
  if [ -f ./usr/lib/ld-linux.so.2 ]; then
    echo ./usr/lib/ld-linux.so.2
  fi
  if [ -d ./usr/include/gnu ]; then
    find ./usr/include/gnu -maxdepth 1 -type f -name '*-32.h'
  fi
  if [ -f ./etc/ld.so.conf.d/i386-linux-gnu.conf ]; then
    echo ./etc/ld.so.conf.d/i386-linux-gnu.conf
  fi
} | sed 's|^\.||' > %{_builddir}/glibc-files.list
%else
cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/glibc-files.list
echo "%ghost /usr/lib/libc.so.6" >> %{_builddir}/glibc-files.list
%endif

%files -f %{_builddir}/glibc-files.list
%defattr(-,root,root)

%post
%if "%{_target_cpu}" != "i686"
if [ -f /etc/ld.so.conf ]; then
  case "$(cat /etc/ld.so.conf 2>/dev/null || true)" in
    *"/etc/ld.so.conf.d/"*) : ;;
    *) printf '%s\n' 'include /etc/ld.so.conf.d/*.conf' >> /etc/ld.so.conf ;;
  esac
else
  mkdir -p /etc/ld.so.conf.d || :
  printf '%s\n' 'include /etc/ld.so.conf.d/*.conf' > /etc/ld.so.conf
fi

if [ -e /usr/lib/x86_64-linux-gnu/libc.so.6 ]; then
  tmp="/usr/lib/.libc.so.6.tmp.$$"
  rm -f "$tmp"
  ln -sf x86_64-linux-gnu/libc.so.6 "$tmp"
  mv -f "$tmp" /usr/lib/libc.so.6
fi
%endif
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.42-1.m264
- Initial RPM packaging for LFS.
