Name:           pkgconf
Version:        2.5.1
Release:        1.m264%{?dist}
Summary:        Successor to pkg-config for retrieving build flags
ExclusiveArch:  x86_64

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        ISC
URL:            https://gitlab.freedesktop.org/pkg-config/pkgconf
Source0:        https://distfiles.ariadne.space/pkgconf/pkgconf-%{version}.tar.xz

%description
pkgconf is a program which helps to configure compiler and linker flags
for development frameworks. It is similar to pkg-config but aims to be a
more flexible higher-performance implementation.

%prep
%setup -q -n pkgconf-%{version}

%build
./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --docdir=%{_datadir}/doc/pkgconf-%{version}

make %{?_smp_mflags}

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

# Provide compatibility symlinks for the traditional pkg-config name
ln -sv pkgconf %{buildroot}/usr/bin/pkg-config
ln -sv pkgconf.1 %{buildroot}/usr/share/man/man1/pkg-config.1

# Multiarch helpers for explicit 32/64-bit .pc resolution
install -vdm 755 %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/pkg-config32 << 'EOF'
#!/bin/sh
PKG_CONFIG_LIBDIR=/usr/lib/i386-linux-gnu/pkgconfig:/usr/share/pkgconfig exec /usr/bin/pkgconf "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/pkg-config32

cat > %{buildroot}%{_bindir}/pkg-config64 << 'EOF'
#!/bin/sh
PKG_CONFIG_LIBDIR=/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/share/pkgconfig exec /usr/bin/pkgconf "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/pkg-config64

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/pkgconf-files.list

%files -f %{_builddir}/pkgconf-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.5.1-1.m264
- Initial RPM packaging for pkgconf following MLFS instructions.
