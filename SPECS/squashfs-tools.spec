Name:           squashfs-tools
Version:        4.6.1
Release:        1.m264%{?dist}
Summary:        Tools for creating and extracting SquashFS filesystems

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-or-later
URL:            https://github.com/plougher/squashfs-tools
Source0:        https://github.com/plougher/squashfs-tools/archive/refs/tags/%{version}/squashfs-tools-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  zlib
BuildRequires:  xz
BuildRequires:  zstd

%description
SquashFS is a compressed read-only filesystem for Linux. This package
contains tools to create and extract SquashFS filesystems.

%prep
%setup -q -n squashfs-tools-%{version}

%build
cd squashfs-tools
make %{?_smp_mflags} \
    XZ_SUPPORT=1 \
    ZSTD_SUPPORT=1 \
    GZIP_SUPPORT=1 \
    XATTR_SUPPORT=1 \
    INSTALL_PREFIX=%{_prefix}

%install
cd squashfs-tools
install -Dm 755 mksquashfs %{buildroot}%{_bindir}/mksquashfs
install -Dm 755 unsquashfs %{buildroot}%{_bindir}/unsquashfs

%files
%defattr(-,root,root)
%{_bindir}/mksquashfs
%{_bindir}/unsquashfs

%changelog
* Thu Apr 09 2026 Maqui Linux Team <team@maqui-linux.org> - 4.6.1-1.m264
- Initial packaging for Maqui Linux
