Name:           binutils
Version:        2.45.1
Release:        1.m264%{?dist}
Summary:        Binary utilities including linker and assembler

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        GPLv3+
URL:            https://www.gnu.org/software/binutils/
Source0:        https://ftp.gnu.org/gnu/binutils/binutils-%{version}.tar.xz

%description
The GNU Binutils package contains a linker, an assembler, and other tools
for handling object files.

%prep
%setup -q -n binutils-%{version}

%build
mkdir build
pushd build
../configure \
    --prefix=%{_prefix} \
    --sysconfdir=%{_sysconfdir} \
    --enable-ld=default \
    --enable-plugins \
    --enable-shared \
    --disable-werror \
    --enable-64-bit-bfd \
    --enable-new-dtags \
    --with-system-zlib \
    --enable-default-hash-style=gnu

make tooldir=%{_prefix} %{?_smp_mflags}
popd

%check
pushd build
make -k check
grep -q "^FAIL:" $(find . -name '*.log') && exit 1 || true
popd

%install
rm -rf %{buildroot}
pushd build
make tooldir=%{_prefix} DESTDIR=%{buildroot} install
popd

rm -rfv %{buildroot}/usr/lib/lib{bfd,ctf,ctf-nobfd,gprofng,opcodes,sframe}.a \
        %{buildroot}/usr/share/doc/gprofng/ || :

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/binutils-files.list

%files -f %{_builddir}/binutils-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.45.1-1.m264
- Initial RPM packaging for binutils following MLFS instructions.
