Name:           coreutils
Version:        9.9
Release:        1.m264%{?dist}
Summary:        Basic file, shell, and text manipulation utilities

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/coreutils/
Source0:        https://ftp.gnu.org/gnu/coreutils/coreutils-%{version}.tar.xz
Patch0:         coreutils-%{version}-i18n-1.patch

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  perl
BuildRequires:  python3
BuildRequires:  texinfo
BuildRequires:  patch
BuildRequires:  autoconf
BuildRequires:  automake

%description
GNU Coreutils provides the standard file, shell, and text manipulation
utilities required on every Linux system.

%prep
%autosetup -n coreutils-%{version} -p1

# Regenerate autotools files after applying i18n patch (modifies configure.ac)
autoreconf -fv
automake -af

%build
export FORCE_UNSAFE_CONFIGURE=1
./configure \
    --prefix=%{_prefix} \
    --enable-no-install-program=kill,uptime
make %{?_smp_mflags}

%check
# Full test suite requires extra setup (non-root tester user). Run best-effort subset.
make -k check || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

# Move chroot according to FHS guidance from MLFS instructions.
install -d %{buildroot}/usr/sbin
if [ -f %{buildroot}/usr/bin/chroot ]; then
  mv -f %{buildroot}/usr/bin/chroot %{buildroot}/usr/sbin/
fi
install -d %{buildroot}/usr/share/man/man8
if [ -f %{buildroot}/usr/share/man/man1/chroot.1 ]; then
  mv -f %{buildroot}/usr/share/man/man1/chroot.1 %{buildroot}/usr/share/man/man8/chroot.8
  sed -i 's/"1"/"8"/' %{buildroot}/usr/share/man/man8/chroot.8
fi

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/coreutils-files.list

%files -f %{_builddir}/coreutils-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 9.9-1.m264
- Initial packaging aligned with MLFS 8.62 instructions (i18n patch, chroot relocation).
