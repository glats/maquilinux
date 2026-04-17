Name:           udev
Version:        258.1
Release:        1.m264%{?dist}
Summary:        Userspace device management from systemd (standalone build)

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

ExclusiveArch:  x86_64

License:        LGPL-2.1-or-later and GPL-2.0-or-later
URL:            https://www.freedesktop.org/wiki/Software/systemd/
Source0:        https://github.com/systemd/systemd/archive/refs/tags/v%{version}/systemd-%{version}.tar.gz
Source1:        https://anduin.linuxfromscratch.org/LFS/udev-lfs-20230818.tar.xz
Source2:        https://anduin.linuxfromscratch.org/LFS/systemd/systemd-man-pages-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  meson
BuildRequires:  ninja
BuildRequires:  pkgconf
BuildRequires:  gperf
BuildRequires:  libcap
BuildRequires:  elfutils
BuildRequires:  util-linux
BuildRequires:  python3

%description
Udev provides the userspace components of the Linux device manager from
systemd. This standalone build supplies udevadm, hwdb utilities, helper
programs, rules, and libudev without installing the rest of systemd.

%prep
%autosetup -n systemd-%{version}

# Follow MLFS instructions to trim unneeded functionality.
sed -e 's/GROUP="render"/GROUP="video"/' \
    -e 's/GROUP="sgx", //' -i rules.d/50-udev-default.rules.in
sed -i '/systemd-sysctl/s/^/#/' rules.d/99-systemd.rules.in
sed -e '/NETWORK_DIRS/s/systemd/udev/' -i src/libsystemd/sd-network/network-util.h

# Capture helper list for reuse during build/install.
grep "'name' :" src/udev/meson.build | awk '{print $3}' | tr -d ",'" | \
  grep -v 'udevadm' > udev-helpers.list

%build
export udev_helpers="$(cat udev-helpers.list)"

meson setup build \
    --prefix=%{_prefix} \
    --buildtype=release \
    -D mode=release \
    -D dev-kvm-mode=0660 \
    -D link-udev-shared=false \
    -D logind=false \
    -D vconsole=false \
    -D man=false

pushd build
udev_targets="$(ninja -n | grep -Eo '(src/(lib)?udev|rules.d|hwdb.d)/[^ ]*')"
libudev_target="$(realpath libudev.so --relative-to .)"
ninja udevadm systemd-hwdb ${udev_targets} "${libudev_target}" ${udev_helpers}
popd

%install
rm -rf %{buildroot}
install -vd %{buildroot}/etc/udev
install -vd %{buildroot}/usr/{bin,sbin,include,lib/x86_64-linux-gnu}
install -vd %{buildroot}/usr/lib/udev/{rules.d,hwdb.d,network}
install -vd %{buildroot}/usr/lib/pkgconfig
install -vd %{buildroot}/usr/share/{pkgconfig,man}

udev_helpers="$(cat udev-helpers.list)"

pushd build
install -Dm755 udevadm               %{buildroot}/usr/bin/udevadm
install -Dm755 systemd-hwdb          %{buildroot}/usr/bin/udev-hwdb
ln -svfn ../bin/udevadm              %{buildroot}/usr/sbin/udevd

cp -av libudev.so{,*[0-9]}          %{buildroot}/usr/lib/x86_64-linux-gnu/
install -Dm644 ../src/libudev/libudev.h %{buildroot}/usr/include/libudev.h
install -Dm644 src/libudev/*.pc      %{buildroot}/usr/lib/pkgconfig/
install -Dm644 src/udev/*.pc         %{buildroot}/usr/share/pkgconfig/
install -Dm644 ../src/udev/udev.conf %{buildroot}/etc/udev/udev.conf

install -m644 -t %{buildroot}/usr/lib/udev/rules.d rules.d/*
install -Dm644 ../rules.d/README %{buildroot}/usr/lib/udev/rules.d/README
find ../rules.d -name '*.rules' ! -name '*power-switch*' -exec \
  install -m644 {} %{buildroot}/usr/lib/udev/rules.d/ \;

install -m644 -t %{buildroot}/usr/lib/udev/hwdb.d hwdb.d/*
install -m644 -t %{buildroot}/usr/lib/udev/hwdb.d ../hwdb.d/*.hwdb
install -Dm644 ../hwdb.d/README %{buildroot}/usr/lib/udev/hwdb.d/README
install -Dm644 ../network/99-default.link %{buildroot}/usr/lib/udev/network/99-default.link

for helper in $udev_helpers; do
  install -Dm755 "$helper" %{buildroot}/usr/lib/udev/$(basename "$helper")
done
popd

# Install LFS-specific rules and support files.
tar -xf %{SOURCE1}
make -f udev-lfs-20230818/Makefile.lfs DESTDIR=%{buildroot} install

# Install relevant man pages from systemd bundle.
tar -xf %{SOURCE2} \
    --no-same-owner \
    --strip-components=1 \
    -C %{buildroot}/usr/share/man \
    --wildcards '*/udev*' '*/libudev*' '*/systemd.link.5' \
                 '*/systemd-hwdb.8' '*/systemd-udevd.service.8'

if [ -f %{buildroot}/usr/share/man/man5/systemd.link.5 ]; then
  sed 's|systemd/network|udev/network|' \
      %{buildroot}/usr/share/man/man5/systemd.link.5 \
    > %{buildroot}/usr/share/man/man5/udev.link.5
fi
if [ -f %{buildroot}/usr/share/man/man8/systemd-hwdb.8 ]; then
  sed 's/systemd\(-\)/udev\1/' \
      %{buildroot}/usr/share/man/man8/systemd-hwdb.8 \
    > %{buildroot}/usr/share/man/man8/udev-hwdb.8
fi
if [ -f %{buildroot}/usr/share/man/man8/systemd-udevd.service.8 ]; then
  sed 's|lib.*/udevd|sbin/udevd|' \
      %{buildroot}/usr/share/man/man8/systemd-udevd.service.8 \
    > %{buildroot}/usr/share/man/man8/udevd.8
fi
rm -f %{buildroot}/usr/share/man/man*/systemd* || :

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/udev-files.list

%files -f %{_builddir}/udev-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 258.1-1.m264
- Standalone udev build from systemd 258.1 per MLFS 8.79 instructions.
