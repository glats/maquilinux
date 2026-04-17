#!/usr/bin/env bash
# enter-chroot-build.sh - Entrar al chroot con el workspace montado
# Para construir RPMs
#
# Uso:
#   ./enter-chroot-build.sh              # Modo interactivo
#   ./enter-chroot-build.sh -c "comando" # Ejecutar comando

set -euo pipefail

ROOTFS="${MQL_LFS:-/run/media/glats/maquilinux}"
WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
CMD=""
INTERACTIVE=true

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case "$1" in
        -c|--command)
            shift
            CMD="$1"
            INTERACTIVE=false
            ;;
        *)
            ;;
    esac
    shift
done

if [ ! -d "$ROOTFS" ]; then
    echo "ERROR: Rootfs no encontrado en $ROOTFS"
    exit 1
fi

if [ "$INTERACTIVE" = true ]; then
    echo "=== Preparando chroot de build ==="
fi
echo "Rootfs:   $ROOTFS"
echo "Workspace: $WORKSPACE"
echo ""

# Montar filesystems virtuales
echo "Montando filesystems virtuales..."
mkdir -p "$ROOTFS"/{dev,proc,sys,run}
mountpoint -q "$ROOTFS/dev"    || mount --bind /dev "$ROOTFS/dev"
mkdir -p "$ROOTFS/dev/pts"
mountpoint -q "$ROOTFS/dev/pts" || mount -t devpts devpts -o gid=5,mode=0620 "$ROOTFS/dev/pts"
mountpoint -q "$ROOTFS/proc"   || mount -t proc proc "$ROOTFS/proc"
mountpoint -q "$ROOTFS/sys"    || mount -t sysfs sysfs "$ROOTFS/sys"
mountpoint -q "$ROOTFS/run"    || mount -t tmpfs tmpfs "$ROOTFS/run"
mkdir -p "$ROOTFS/dev/shm"
mountpoint -q "$ROOTFS/dev/shm" || mount -t tmpfs -o nosuid,nodev tmpfs "$ROOTFS/dev/shm"

# Montar workspace dentro del chroot
mkdir -p "$ROOTFS/workspace"
mountpoint -q "$ROOTFS/workspace" || mount --bind "$WORKSPACE" "$ROOTFS/workspace"

if [ "$INTERACTIVE" = true ]; then
    echo ""
    echo "=== Chroot listo ==="
    echo "El workspace está en /workspace"
    echo "Comandos útiles:"
    echo "  cd /workspace/SPECS"
    echo "  rpmbuild -ba bash.spec --define '_topdir /workspace'"
    echo ""
    echo "Escribí 'exit' para salir."
    echo ""
fi

# Entrar al chroot
if [ -n "$CMD" ]; then
    # Modo comando
    chroot "$ROOTFS" /usr/bin/env -i \
        HOME=/root \
        TERM="$TERM" \
        PATH=/usr/bin:/usr/sbin:/bin:/sbin \
        /bin/bash -c "$CMD"
else
    # Modo interactivo
    chroot "$ROOTFS" /usr/bin/env -i \
        HOME=/root \
        TERM="$TERM" \
        PS1='(maquilinux) \u:\w\$ ' \
        PATH=/usr/bin:/usr/sbin:/bin:/sbin \
        /bin/bash --login
fi

# Al salir, desmontar
echo ""
echo "Desmontando..."
umount "$ROOTFS/workspace" 2>/dev/null || true
umount "$ROOTFS/dev/shm"   2>/dev/null || true
umount "$ROOTFS/dev/pts"   2>/dev/null || true
umount "$ROOTFS/run"       2>/dev/null || true
umount "$ROOTFS/sys"       2>/dev/null || true
umount "$ROOTFS/proc"      2>/dev/null || true
umount "$ROOTFS/dev"       2>/dev/null || true

echo "Listo."
