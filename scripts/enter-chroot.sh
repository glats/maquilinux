#!/usr/bin/env bash
# enter-chroot.sh - Entrar al chroot de Maquilinux
# Igual que en LFS, simple y directo

set -euo pipefail

MQL_DISK="${MQL_DISK:-${MQL_LFS:-/run/media/glats/maquilinux}}"
ROOTFS="${MQL_DISK}/merged"

if [ ! -d "$ROOTFS" ]; then
    echo "ERROR: Rootfs no encontrado en $ROOTFS"
    exit 1
fi

echo "Montando filesystems virtuales..."

# Crear directorios si no existen
mkdir -p "$ROOTFS"/{dev,proc,sys,run}

# Montar si no están montados
mountpoint -q "$ROOTFS/dev"    || mount --bind /dev "$ROOTFS/dev"
mountpoint -q "$ROOTFS/dev/pts" || mount -t devpts devpts -o gid=5,mode=0620 "$ROOTFS/dev/pts" 2>/dev/null || mkdir -p "$ROOTFS/dev/pts"
mountpoint -q "$ROOTFS/proc"   || mount -t proc proc "$ROOTFS/proc"
mountpoint -q "$ROOTFS/sys"    || mount -t sysfs sysfs "$ROOTFS/sys"
mountpoint -q "$ROOTFS/run"    || mount -t tmpfs tmpfs "$ROOTFS/run"

# dev/shm
mkdir -p "$ROOTFS/dev/shm"
mountpoint -q "$ROOTFS/dev/shm" || mount -t tmpfs -o nosuid,nodev tmpfs "$ROOTFS/dev/shm"

echo "Entrando al chroot..."
echo "Escribí 'exit' para salir."
echo ""

# Entrar al chroot
chroot "$ROOTFS" /usr/bin/env -i \
    HOME=/root \
    TERM="$TERM" \
    PS1='(maquilinux) \u:\w\$ ' \
    PATH=/usr/bin:/usr/sbin:/bin:/sbin \
    /bin/bash --login

# Al salir, desmontar
echo ""
echo "Desmontando filesystems..."
umount "$ROOTFS/dev/shm" 2>/dev/null || true
umount "$ROOTFS/dev/pts" 2>/dev/null || true
umount "$ROOTFS/run"     2>/dev/null || true
umount "$ROOTFS/sys"     2>/dev/null || true
umount "$ROOTFS/proc"    2>/dev/null || true
umount "$ROOTFS/dev"     2>/dev/null || true

echo "Listo."
