Name:           shadow
Version:        4.18.0
Release:        1.m264%{?dist}
Summary:        Password and account management suite
ExclusiveArch:  x86_64

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        BSD-3-Clause
URL:            https://github.com/shadow-maint/shadow
Source0:        https://github.com/shadow-maint/shadow/releases/download/%{version}/shadow-%{version}.tar.xz

%description
Shadow provides programs for handling user and group accounts, including
password management, login, su, useradd, and related tools. It also
installs the libsubid library used for subordinate ID management.

%prep
%setup -q -n shadow-%{version}

# Do not install the groups program or its man page; coreutils provides a
# better implementation. Also avoid installing duplicate man pages
# already provided by the man-pages package.
sed -i 's/groups$(EXEEXT) //' src/Makefile.in
find man -name Makefile.in -exec sed -i 's/groups\.1 / /'   {} \;
find man -name Makefile.in -exec sed -i 's/getspnam\.3 / /' {} \;
find man -name Makefile.in -exec sed -i 's/passwd\.5 / /'   {} \;

# Use YESCRYPT as the default hash, update mailbox location to /var/mail,
# and remove /bin and /sbin from PATH as they are just symlinks into /usr.
sed -e 's:#ENCRYPT_METHOD DES:ENCRYPT_METHOD YESCRYPT:' \
    -e 's:/var/spool/mail:/var/mail:'                   \
    -e '/PATH=/{s@/sbin:@@;s@/bin:@@}'                  \
    -i etc/login.defs

%build
# Some helper programs hard-code /usr/bin/passwd; ensure it exists in the
# running system so installation scripts place files in the correct path.
touch %{_bindir}/passwd || :

# 64-bit build
LDFLAGS64="${LDFLAGS:-} -L/usr/lib/x86_64-linux-gnu"
export LDFLAGS="${LDFLAGS64}"

./configure \
    --prefix=%{_prefix} \
    --sysconfdir=%{_sysconfdir} \
    --disable-static \
    --with-{b,yes}crypt \
    --without-libbsd \
    --with-group-name-max-length=32 \
    --libdir=/usr/lib/x86_64-linux-gnu

make %{?_smp_mflags}

%install
rm -rf %{buildroot}

# 64-bit install: programs, configuration, man pages, and libraries.
make exec_prefix=%{_prefix} DESTDIR=%{buildroot} install
make -C man exec_prefix=%{_prefix} DESTDIR=%{buildroot} install-man

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/shadow-files.list

%files -f %{_builddir}/shadow-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 4.18.0-1.m264
- Initial RPM packaging for Shadow with multiarch libsubid.
