Name:           e2fsprogs
Version:        1.47.3
Release:        1.m264%{?dist}
Summary:        Utilities and libraries for ext2/3/4 filesystems

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-or-later
URL:            https://e2fsprogs.sourceforge.net/
Source0:        https://downloads.sourceforge.net/project/e2fsprogs/e2fsprogs/v%{version}/e2fsprogs-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconf
BuildRequires:  util-linux
BuildRequires:  zlib
BuildRequires:  bzip2
BuildRequires:  xz

%description
E2fsprogs provides the filesystem utilities for ext2/3/4 filesystems, including
e2fsck, mke2fs, tune2fs, blkid support libraries, and libext2fs.

%prep
%autosetup -n e2fsprogs-%{version}

mkdir build

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
LIBDIR=/usr/lib/i386-linux-gnu
%else
LIBDIR=/usr/lib/x86_64-linux-gnu
%endif

pushd build
../configure --prefix=%{_prefix} \
             --sysconfdir=%{_sysconfdir} \
             --libdir=${LIBDIR} \
             --enable-elf-shlibs \
             --disable-libblkid \
             --disable-libuuid \
             --disable-uuidd \
             --disable-fsck
make %{?_smp_mflags}
popd

%check
pushd build
make -k check || :
popd

%install
rm -rf %{buildroot}
pushd build
make DESTDIR=%{buildroot} install
popd

rm -f %{buildroot}/usr/share/info/dir || :
if [ -f %{buildroot}/usr/share/info/libext2fs.info.gz ]; then
  gunzip -v %{buildroot}/usr/share/info/libext2fs.info.gz
fi

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir}/e2fsck || :
rm -rf %{buildroot}%{_bindir}/mke2fs || :
rm -rf %{buildroot}%{_bindir}/tune2fs || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_docdir}/e2fsprogs-%{version} || :
rm -rf %{buildroot}%{_sysconfdir} || :
%endif

rm -f %{buildroot}/usr/lib*/libcom_err.a %{buildroot}/usr/lib*/libe2p.a \
      %{buildroot}/usr/lib*/libext2fs.a %{buildroot}/usr/lib*/libss.a || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/e2fsprogs-files.list

%files -f %{_builddir}/e2fsprogs-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.47.3-1.m264
- Initial packaging aligned with MLFS 8.83 instructions (shared libs only, no libuuid/libblkid).
