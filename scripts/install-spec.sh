#!/usr/bin/env bash
set -euo pipefail

# Install Maquilinux RPMs to the rootfs
# Usage:
#   ./install-spec.sh <package-name> [--arch=x86_64|i686] [--both]
#
# Examples:
#   ./install-spec.sh bash
#   ./install-spec.sh glibc --both
#   ./install-spec.sh linux --arch x86_64

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <package-name> [--arch=x86_64|i686] [--both] [--nodeps]" >&2
  exit 1
fi

PKG_NAME="$1"
shift

TARGET_ARCH=""
INSTALL_BOTH="false"
INSTALL_NODEPS="false"

while (( "$#" )); do
  case "$1" in
    --arch=*)
      TARGET_ARCH="${1#--arch=}"
      ;;
    --arch)
      shift
      TARGET_ARCH="${1:-}"
      ;;
    --both)
      INSTALL_BOTH="true"
      ;;
    --nodeps)
      INSTALL_NODEPS="true"
      ;;
    *)
      ;;
  esac
  shift || true
done

# Workspace root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOPDIR="$(dirname "$SCRIPT_DIR")"

# Rootfs paths
ROOTFS="${MQL_LFS:-/run/media/glats/maquilinux}"
RPM_DB="$ROOTFS/var/lib/rpm"

# Maquilinux RPM tools
RPM_CMD="$ROOTFS/usr/bin/rpm"
LD_PATH="$ROOTFS/usr/lib:$ROOTFS/usr/lib/x86_64-linux-gnu"
RPM_CONFIG="$ROOTFS/usr/lib/rpm"

if [ ! -x "$RPM_CMD" ]; then
  echo "ERROR: rpm not found at $RPM_CMD" >&2
  exit 1
fi

# Find RPMs for package
find_rpms() {
  local pkg="$1"
  local arch="$2"
  local rpms_dir="$TOPDIR/RPMS"
  
  local found=()
  
  # Check arch-specific
  if [ -d "$rpms_dir/$arch" ]; then
    for f in "$rpms_dir/$arch/$pkg"-*."$arch".rpm; do
      [ -f "$f" ] && found+=("$f")
    done
  fi
  
  # Check noarch
  if [ -d "$rpms_dir/noarch" ]; then
    for f in "$rpms_dir/noarch/$pkg"-*.noarch.rpm; do
      [ -f "$f" ] && found+=("$f")
    done
  fi
  
  if [ ${#found[@]} -eq 0 ]; then
    return 1
  fi
  
  # Return newest if multiple
  if [ ${#found[@]} -gt 1 ]; then
    stat -c '%Y %n' "${found[@]}" | sort -rn | head -1 | cut -d' ' -f2-
  else
    echo "${found[0]}"
  fi
}

# Install RPM
install_rpm() {
  local rpm_file="$1"
  local rpm_args=(--nosignature --dbpath "$RPM_DB")
  
  if [ "$INSTALL_NODEPS" = "true" ]; then
    rpm_args+=(--nodeps)
  fi
  
  echo "[install] Installing $(basename "$rpm_file")..."
  
  LD_LIBRARY_PATH="$LD_PATH" \
  RPM_CONFIGDIR="$RPM_CONFIG" \
  "$RPM_CMD" -Uvh "${rpm_args[@]}" "$rpm_file"
}

# Detect i686 support
supports_i686() {
  local spec="$TOPDIR/SPECS/${PKG_NAME}.spec"
  [ -f "$spec" ] || return 1
  grep -Eq '^ExclusiveArch:[[:space:]]*x86_64' "$spec" && return 1
  grep -Eq 'i686-pc-linux-gnu|/usr/lib/i386-linux-gnu|_target_cpu.*i686|gcc[[:space:]]+-m32' "$spec"
}

# Collect RPMs to install
declare -a TO_INSTALL

if [ "$INSTALL_BOTH" = "true" ] && supports_i686; then
  for arch in x86_64 i686; do
    rpm=$(find_rpms "$PKG_NAME" "$arch") && TO_INSTALL+=("$rpm")
  done
elif [ -n "$TARGET_ARCH" ]; then
  rpm=$(find_rpms "$PKG_NAME" "$TARGET_ARCH") && TO_INSTALL+=("$rpm")
else
  rpm=$(find_rpms "$PKG_NAME" "x86_64") && TO_INSTALL+=("$rpm")
  
  # Auto-install -devel for x86_64
  devel_rpm=$(find_rpms "${PKG_NAME}-devel" "x86_64" 2>/dev/null || true)
  [ -n "$devel_rpm" ] && TO_INSTALL+=("$devel_rpm")
fi

if [ ${#TO_INSTALL[@]} -eq 0 ]; then
  echo "ERROR: No RPMs found for '$PKG_NAME'" >&2
  echo "Run build-spec.sh first?" >&2
  exit 1
fi

# Install
for rpm in "${TO_INSTALL[@]}"; do
  install_rpm "$rpm"
done

echo "[install] Done."
