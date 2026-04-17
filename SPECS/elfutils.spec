Name:           elfutils
Version:        0.194
Release:        1.m264%{?dist}
Summary:        ELF utilities and libdw (from elfutils)

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPLv3+ and LGPLv3+
URL:            https://sourceware.org/elfutils/
Source0:        https://sourceware.org/ftp/elfutils/%{version}/elfutils-%{version}.tar.bz2

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  zlib-devel
BuildRequires:  bzip2
BuildRequires:  xz

Requires:       libelf

%description
elfutils provides utilities and libraries for handling ELF files.

This package is intended to complement the separate libelf package in this
build tree, and removes libelf files from its payload to avoid file conflicts.

%prep
%setup -q -n elfutils-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
export PKG_CONFIG_PATH=""
export PKG_CONFIG_LIBDIR="/usr/lib/i386-linux-gnu/pkgconfig:/usr/share/pkgconfig"
CONFIG_LIBDIR=/usr/lib/i386-linux-gnu
CONFIG_HOST=--host=i686-pc-linux-gnu
%else
CONFIG_LIBDIR=/usr/lib/x86_64-linux-gnu
CONFIG_HOST=""
%endif

LIBARCHIVE_OPT=""
if ./configure --help 2>/dev/null | grep -q -- '--with-libarchive'; then
    LIBARCHIVE_OPT="--without-libarchive"
fi

./configure \
    --prefix=%{_prefix} \
    --libdir=${CONFIG_LIBDIR} \
    ${CONFIG_HOST} \
    ${LIBARCHIVE_OPT} \
    --disable-debuginfod \
    --enable-libdebuginfod=dummy

make %{?_smp_mflags}

%check
make -k check || :

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
make DESTDIR=%{buildroot} install

%if "%{_target_cpu}" == "i686"
rm -f %{buildroot}/usr/lib/i386-linux-gnu/pkgconfig/libelf.pc || :
rm -f %{buildroot}/usr/lib/i386-linux-gnu/libelf.so* || :
rm -f %{buildroot}/usr/lib/i386-linux-gnu/libelf-*.so* || :
rm -f %{buildroot}/usr/lib/i386-linux-gnu/*.a || :
%else
rm -f %{buildroot}%{_includedir}/libelf.h || :
rm -f %{buildroot}%{_includedir}/gelf.h || :
rm -f %{buildroot}%{_includedir}/nlist.h || :
rm -f %{buildroot}/usr/lib/x86_64-linux-gnu/pkgconfig/libelf.pc || :
rm -f %{buildroot}/usr/lib/x86_64-linux-gnu/libelf.so* || :
rm -f %{buildroot}/usr/lib/x86_64-linux-gnu/libelf-*.so* || :
rm -f %{buildroot}/usr/lib/x86_64-linux-gnu/*.a || :
%endif

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_prefix}/etc || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
cd %{buildroot}
if [ -d ./usr/lib/i386-linux-gnu ]; then
  find ./usr/lib/i386-linux-gnu \( -type f -o -type l \) -printf '/usr/lib/i386-linux-gnu/%%P\n'
fi > %{builddir}/elfutils-files.list
%else
cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' > %{builddir}/elfutils-files.list
%endif

test -s %{builddir}/elfutils-files.list

%files -f %{builddir}/elfutils-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 0.194-1.m264
- Initial packaging of elfutils (tools + libdw) with multilib layout (x86_64 full, i686 libs-only).
