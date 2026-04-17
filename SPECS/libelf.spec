Name:           libelf
Version:        0.194
Release:        1.m264%{?dist}
Summary:        Library for reading and writing ELF files (from elfutils)

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

%description
Libelf is part of the elfutils suite and provides an API for reading and
writing ELF (Executable and Linkable Format) object files.

%prep
%setup -q -n elfutils-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
CONFIG_LIBDIR=/usr/lib/i386-linux-gnu
CONFIG_HOST=--host=i686-pc-linux-gnu
%else
CONFIG_LIBDIR=/usr/lib/x86_64-linux-gnu
CONFIG_HOST=""
%endif

./configure \
    --prefix=%{_prefix} \
    --libdir=${CONFIG_LIBDIR} \
    ${CONFIG_HOST} \
    --disable-debuginfod \
    --enable-libdebuginfod=dummy

make -C lib %{?_smp_mflags}
make -C libelf %{?_smp_mflags}

%check
make -k check || :

%install
rm -rf %{buildroot}
make -C libelf DESTDIR=%{buildroot} install

%if "%{_target_cpu}" == "i686"
install -D -m 0644 config/libelf.pc \
    %{buildroot}/usr/lib/i386-linux-gnu/pkgconfig/libelf.pc
rm -f %{buildroot}/usr/lib/i386-linux-gnu/libelf.a || :
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
%else
install -D -m 0644 config/libelf.pc \
    %{buildroot}/usr/lib/x86_64-linux-gnu/pkgconfig/libelf.pc
rm -f %{buildroot}/usr/lib/x86_64-linux-gnu/libelf.a || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
cd %{buildroot}
{
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu -type f -o -type l | sed 's|^\.||'
  fi
} > %{_builddir}/libelf-files.list
%else
cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/libelf-files.list
%endif

%files -f %{_builddir}/libelf-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 0.194-1.m264
- Initial packaging of libelf from elfutils with multilib layout (x86_64 full, i686 libs-only).
