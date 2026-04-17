Name:           kbd
Version:        2.9.0
Release:        1.m264%{?dist}
Summary:        Key-table files, console fonts, and keyboard utilities

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-or-later
URL:            https://www.kernel.org/pub/linux/utils/kbd/
Source0:        https://www.kernel.org/pub/linux/utils/kbd/kbd-%{version}.tar.xz
Patch0:         https://www.linuxfromscratch.org/patches/lfs/development/kbd-%{version}-backspace-1.patch

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconf

%description
The kbd package provides keymaps, console fonts, and utilities for configuring
virtual terminals and keyboard behavior.

%prep
%autosetup -n kbd-%{version} -p1
sed -i '/RESIZECONS_PROGS=/s/yes/no/' configure
sed -i 's/resizecons.8 //' docs/man/man8/Makefile.in

%build
./configure --prefix=%{_prefix} --disable-vlock
make %{?_smp_mflags}

%check
# Tests require valgrind and a non-chroot environment; skip here.
:

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
make DESTDIR=%{buildroot} install
install -d %{buildroot}/usr/share/doc/kbd-%{version}
cp -a docs/doc/. %{buildroot}/usr/share/doc/kbd-%{version}/

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' > %{builddir}/kbd-files.list
test -s %{builddir}/kbd-files.list

%files -f %{builddir}/kbd-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.9.0-1.m264
- Initial packaging aligned with MLFS 8.70 instructions (backspace patch, no resizecons, disable vlock).
