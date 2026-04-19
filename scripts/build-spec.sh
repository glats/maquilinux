#!/usr/bin/env bash
set -euo pipefail

# Build Maquilinux RPMs
# Usage:
#   ./build-spec.sh <spec-name> [--arch=x86_64|i686|noarch] [--both]
#
# Examples:
#   ./build-spec.sh bash
#   ./build-spec.sh glibc --both
#   ./build-spec.sh python3 --arch x86_64

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <spec-name> [--arch=x86_64|i686|noarch] [--both]" >&2
  exit 1
fi

SPEC_INPUT="$1"
shift

TARGET_CPU=""
BUILD_BOTH="false"
EXTRA_ARGS=()

while (( "$#" )); do
  case "$1" in
    --arch=*)
      TARGET_CPU="${1#--arch=}"
      ;;
    --arch)
      shift
      TARGET_CPU="${1:-}"
      ;;
    --both)
      BUILD_BOTH="true"
      ;;
    --)
      shift
      EXTRA_ARGS+=("$@")
      break
      ;;
    *)
      EXTRA_ARGS+=("$1")
      ;;
  esac
  shift || true
done

# Workspace root (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOPDIR="$(dirname "$SCRIPT_DIR")"

# Maquilinux rootfs (tools and libraries from overlay chroot)
MQL_DISK="${MQL_DISK:-${MQL_LFS:-/run/media/glats/maquilinux}}"
ROOTFS="${MQL_DISK}/merged"

# Ensure RPM tree exists
mkdir -p "$TOPDIR"/{BUILD,BUILDROOT,RPMS/{noarch,x86_64,i686},SOURCES,SRPMS}

# Resolve spec file
if [[ "$SPEC_INPUT" == *.spec ]]; then
  SPEC_NAME="$SPEC_INPUT"
else
  SPEC_NAME="${SPEC_INPUT}.spec"
fi
SPEC_FILE="$TOPDIR/SPECS/$SPEC_NAME"

if [ ! -f "$SPEC_FILE" ]; then
  echo "ERROR: Spec not found: $SPEC_FILE" >&2
  exit 1
fi

# Detect noarch
SPEC_IS_NOARCH=0
if grep -Eq '^[[:space:]]*BuildArch:[[:space:]]*noarch([[:space:]]|$)' "$SPEC_FILE"; then
  SPEC_IS_NOARCH=1
  TARGET_CPU="noarch"
  BUILD_BOTH="false"
fi

# Check if sources exist
check_sources() {
  local spec="$1"
  local sources_dir="$TOPDIR/SOURCES"
  
  # Extract Source0 from spec (filename only, no URL expansion)
  local source_file
  source_file=$(grep -E '^Source0:' "$spec" | awk '{print $2}' || true)
  
  if [ -n "$source_file" ]; then
    # Handle %{version} expansion
    source_file=$(echo "$source_file" | sed 's/%{version}/'"$(grep '^Version:' "$spec" | awk '{print $2}')"'/g')
    
    if [ ! -f "$sources_dir/$source_file" ]; then
      echo "ERROR: Source not found: $sources_dir/$source_file" >&2
      echo "Download it first or copy from another location." >&2
      return 1
    fi
    echo "[build] Found source: $source_file"
  fi
}

# Run rpmbuild using Maquilinux tools
run_rpmbuild() {
  local target="$1"
  shift || true
  
  local target_args=()
  if [ -n "$target" ]; then
    target_args=("--target" "$target")
  fi
  
  # Use Maquilinux RPM tools
  local RPM_CMD="$ROOTFS/usr/bin/rpmbuild"
  local LD_PATH="$ROOTFS/usr/lib:$ROOTFS/usr/lib/x86_64-linux-gnu"
  local RPM_CONFIG="$ROOTFS/usr/lib/rpm"
  
  if [ ! -x "$RPM_CMD" ]; then
    echo "ERROR: rpmbuild not found at $RPM_CMD" >&2
    exit 1
  fi
  
  # Override critical macros to use Maquilinux tools (not host paths)
  # This is needed when running rpmbuild from NixOS or other non-FHS systems
  local MACRO_OVERRIDES=(
    --define "_buildshell $ROOTFS/bin/bash"
    --define "__rm $ROOTFS/usr/bin/rm"
    --define "__cp $ROOTFS/usr/bin/cp"
    --define "__mv $ROOTFS/usr/bin/mv"
    --define "__mkdir $ROOTFS/usr/bin/mkdir"
    --define "__install $ROOTFS/usr/bin/install"
    --define "__chmod $ROOTFS/usr/bin/chmod"
    --define "__chown $ROOTFS/usr/bin/chown"
    --define "__sed $ROOTFS/usr/bin/sed"
    --define "__awk $ROOTFS/usr/bin/gawk"
    --define "__cat $ROOTFS/usr/bin/cat"
    --define "__ln_s ln -s"
    --define "__gzip $ROOTFS/usr/bin/gzip"
    --define "__bzip2 $ROOTFS/usr/bin/bzip2"
    --define "__xz $ROOTFS/usr/bin/xz"
    --define "__tar $ROOTFS/usr/bin/tar"
  )
  
  # Load custom macros that override tool paths for non-FHS hosts
  local CUSTOM_MACROS="$TOPDIR/SOURCES/maquilinux-macros"
  local LOAD_MACROS=()
  if [ -f "$CUSTOM_MACROS" ]; then
    LOAD_MACROS=("--load" "$CUSTOM_MACROS")
  fi
  
  # Put Maquilinux tools first in PATH so rpmuncompress finds gzip/tar
  local NEW_PATH="$ROOTFS/usr/bin:$ROOTFS/bin${PATH:+:$PATH}"
  
  PATH="$NEW_PATH" \
  LD_LIBRARY_PATH="$LD_PATH" \
  RPM_CONFIGDIR="$RPM_CONFIG" \
  "$RPM_CMD" -ba "$SPEC_FILE" \
    --define "_topdir $TOPDIR" \
    --define "_builddir $TOPDIR/BUILD" \
    --define "_buildrootdir $TOPDIR/BUILDROOT" \
    --define "_specdir $TOPDIR/SPECS" \
    --define "_sourcedir $TOPDIR/SOURCES" \
    --define "_rpmdir $TOPDIR/RPMS" \
    --define "_srcrpmdir $TOPDIR/SRPMS" \
    "${LOAD_MACROS[@]}" \
    "${MACRO_OVERRIDES[@]}" \
    "${target_args[@]}" \
    "${EXTRA_ARGS[@]}"
}

# Detect i686 support in spec
supports_i686() {
  if grep -Eq '^ExclusiveArch:[[:space:]]*x86_64' "$SPEC_FILE"; then
    return 1
  fi
  grep -Eq 'i686-pc-linux-gnu|/usr/lib/i386-linux-gnu|_target_cpu.*i686|%ifarch[[:space:]]+i686|gcc[[:space:]]+-m32' "$SPEC_FILE"
}

# Main
check_sources "$SPEC_FILE" || exit 1

if [ "$BUILD_BOTH" = "true" ]; then
  run_rpmbuild x86_64
  if supports_i686; then
    run_rpmbuild i686
  else
    echo "[build] Skipping i686 (no 32-bit support detected)" >&2
  fi
elif [ -n "$TARGET_CPU" ]; then
  run_rpmbuild "$TARGET_CPU"
else
  run_rpmbuild ""
fi

echo "[build] Done. RPMs in $TOPDIR/RPMS/"
