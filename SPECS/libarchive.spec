Name:           libarchive
Version:        3.8.4
Release:        2.m264%{?dist}
Summary:        Multi-format archive and compression library and tools

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

# Provide library sonames for dependency resolution
Provides:       libarchive.so.13()(64bit)

License:        BSD
URL:            https://www.libarchive.org/
Source0:        https://github.com/libarchive/libarchive/releases/download/v%{version}/libarchive-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  zlib
BuildRequires:  bzip2
BuildRequires:  xz
BuildRequires:  zstd
BuildRequires:  lz4
BuildRequires:  openssl

%description
libarchive is a library for reading and writing streaming archives, including
various tar, cpio, and zip formats, and includes the bsdtar and bsdcpio tools.

%prep
%setup -q -n libarchive-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
CONFIG_HOST=--host=i686-pc-linux-gnu
CONFIG_LIBDIR=/usr/lib/i386-linux-gnu
%else
CONFIG_HOST=""
CONFIG_LIBDIR=/usr/lib/x86_64-linux-gnu
%endif

./configure \
    --prefix=%{_prefix} \
    --libdir=${CONFIG_LIBDIR} \
    --disable-static \
    ${CONFIG_HOST}

make %{?_smp_mflags}

%check
make check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

%if "%{_target_cpu}" == "i686"
cd %{buildroot}
{
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu -type f -o -type l | sed 's|^\.||'
  fi
} > %{_builddir}/libarchive-files.list
%else
cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/libarchive-files.list
%endif

%files -f %{_builddir}/libarchive-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 3.7.6-1.m264
- Initial packaging for RPM dependency with multilib layout (x86_64 full, i686 libs-only).
