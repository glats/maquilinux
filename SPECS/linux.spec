Name:           linux
Version:        6.17.9
Release:        1.m264%{?dist}
Summary:        The Linux kernel

ExclusiveArch:  x86_64

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-only
URL:            https://www.kernel.org/
Source0:        https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  bison
BuildRequires:  flex
BuildRequires:  perl

%description
The Linux kernel.

%prep
%autosetup -n linux-%{version}

%build
make mrproper
make defconfig

./scripts/config --file .config \
  --enable DEVTMPFS \
  --enable DEVTMPFS_MOUNT \
  --enable TMPFS \
  --enable EXT4_FS \
  --enable VIRTIO \
  --enable VIRTIO_PCI \
  --enable VIRTIO_BLK \
  --enable SCSI_VIRTIO \
  --enable VIRTIO_NET \
  --enable VIRTIO_CONSOLE \
  --enable VIRTIO_BALLOON \
  --enable ATA \
  --enable SATA_AHCI \
  --enable NET \
  --enable E1000 \
  --enable SERIAL_8250 \
  --enable SERIAL_8250_CONSOLE \
  --enable IA32_EMULATION \
  --enable OVERLAY_FS \
  --enable OVERLAY_FS_REDIRECT_DIR \
  --enable OVERLAY_FS_INDEX \
  --enable OVERLAY_FS_XINO_AUTO \
  --enable OVERLAY_FS_METACOPY \
  --enable SQUASHFS \
  --enable SQUASHFS_ZLIB \
  --enable SQUASHFS_LZ4 \
  --enable SQUASHFS_LZO \
  --enable SQUASHFS_XZ \
  --enable SQUASHFS_ZSTD \
  --enable SQUASHFS_EMBEDDED \
  --enable ISO9660_FS \
  --enable CDROM \
  --enable BLK_DEV_SR \
  --enable LOOP \
  --enable BLK_DEV_DM \
  --enable DM_BUFIO \
  --enable DM_SNAPSHOT \
  --enable DM_MIRROR \
  --disable DEBUG_INFO

make olddefconfig
make %{?_smp_mflags}

%check
:

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}

krel="$(make -s kernelrelease)"

make modules_install INSTALL_MOD_PATH=%{buildroot}/usr

if [ -L %{buildroot}/usr/lib/modules/${krel}/build ]; then
  rm -f %{buildroot}/usr/lib/modules/${krel}/build
fi
if [ -L %{buildroot}/usr/lib/modules/${krel}/source ]; then
  rm -f %{buildroot}/usr/lib/modules/${krel}/source
fi

install -d %{buildroot}/boot
install -m 0644 arch/x86/boot/bzImage %{buildroot}/boot/vmlinuz-${krel}
install -m 0644 System.map %{buildroot}/boot/System.map-${krel}
install -m 0644 .config %{buildroot}/boot/config-${krel}

cd %{buildroot}
find . \( -type f -o -type l \) -print | \
  sed 's|^\./|/|' | \
  while IFS= read -r p; do \
    case "$p" in \
      *[[:space:]]*) printf '"%s"\n' "$p" ;; \
      *)             printf '%s\n' "$p" ;; \
    esac; \
  done > %{builddir}/linux-files.list

test -s %{builddir}/linux-files.list

%files -f %{builddir}/linux-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 6.17.9-1.m264
- Initial packaging of the Linux kernel for Maquilinux.
