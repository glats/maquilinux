Name:           lvm2
Version:        2.03.38
Release:        1.m264%{?dist}
Summary:        Logical Volume Management tools and device-mapper

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-only AND LGPL-2.1-only
URL:            https://sourceware.org/lvm2/
Source0:        https://sourceware.org/ftp/lvm2/LVM2.%{version}.tgz

BuildRequires:  gcc
BuildRequires:  make

Provides:       device-mapper = %{version}-%{release}
Provides:       libdevmapper = %{version}-%{release}

%description
LVM2 provides logical volume management for Linux. This package includes
the device-mapper library and tools (dmsetup) required by dracut for
dmsquash-live ISO booting, as well as the LVM2 tools (lvcreate, vgchange, etc.).

%prep
%setup -q -n LVM2.%{version}

%build
%configure \
    --disable-selinux \
    --disable-cmirrord \
    --disable-dmeventd \
    --disable-lvmlockd-dlm \
    --disable-lvmlockd-sanlock \
    --disable-notify-dbus \
    --enable-pkgconfig \
    --with-systemdsystemunitdir=no \
    --with-tmpfilesdir=no

# Build only device-mapper (no libaio needed)
make device-mapper %{?_smp_mflags}

%install
# Install only device-mapper
make install_device-mapper DESTDIR=%{buildroot}

# Remove static libs
rm -f %{buildroot}%{_libdir}/libdevmapper.a

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/lvm2-files.list

%files -f %{_builddir}/lvm2-files.list
%defattr(-,root,root)

%changelog
* Sat Apr 11 2026 Maqui Linux Team <team@maqui-linux.org> - 2.03.38-1.m264
- Initial packaging for Maqui Linux
- Provides device-mapper for dracut dmsquash-live
