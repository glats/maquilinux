#!/usr/bin/env bash
# build-spec.sh - Build Maquilinux RPMs inside chroot
#
# Usage:
#   ./build-spec.sh <spec-name> [--arch=x86_64|i686|noarch] [--both]
#
# This script ALWAYS runs rpmbuild inside the Maqui Linux chroot,
# following the LFS pattern. It works on any host distro (NixOS, Ubuntu, Arch).
#
# Prerequisites:
#   - Overlay mounted at $MQL_DISK/merged
#   - Workspace bind-mounted at $MQL_DISK/merged/workspace
#   - Virtual filesystems mounted (proc, dev, etc.)
#
# Examples:
#   ./build-spec.sh bash
#   ./build-spec.sh glibc --both
#   ./build-spec.sh python3 --arch x86_64

set -euo pipefail

# ============================================================================
# Argument parsing
# ============================================================================

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

# ============================================================================
# Configuration
# ============================================================================

# Workspace root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOPDIR="$(dirname "$SCRIPT_DIR")"

# Load config files
MQL_DISK="${MQL_DISK:-${MQL_LFS:-/run/media/glats/maquilinux}}"
if [[ -f "$TOPDIR/mql.local" ]]; then
  source "$TOPDIR/mql.local" 2>/dev/null || true
fi
if [[ -f "$TOPDIR/mql.conf" ]]; then
  source "$TOPDIR/mql.conf" 2>/dev/null || true
fi
MQL_DISK="${MQL_DISK:-${MQL_LFS:-/run/media/glats/maquilinux}}"

# Chroot target (overlay merged directory)
CHROOT_TARGET="$MQL_DISK/merged"

# Ensure RPM tree exists on host (for output)
mkdir -p "$TOPDIR"/{BUILD,BUILDROOT,RPMS/{noarch,x86_64,i686},SOURCES,SRPMS}

# ============================================================================
# Find sudo (NixOS-compatible)
# ============================================================================

find_sudo() {
  for path in /run/wrappers/bin/sudo /usr/bin/sudo /bin/sudo; do
    if [[ -x "$path" ]]; then
      echo "$path"
      return
    fi
  done
  if command -v sudo &> /dev/null; then
    echo "sudo"
  else
    echo ""
  fi
}
SUDO_CMD="$(find_sudo)"

# ============================================================================
# Verify chroot environment
# ============================================================================

verify_chroot() {
  # Check overlay mounted
  if ! mountpoint -q "$CHROOT_TARGET" 2>/dev/null; then
    echo "ERROR: Overlay not mounted at $CHROOT_TARGET" >&2
    echo "Run: sudo mount -t overlay overlay -o lowerdir=$MQL_DISK/base,upperdir=$MQL_DISK/layers/upper,workdir=$MQL_DISK/layers/work $CHROOT_TARGET" >&2
    exit 1
  fi

  # Check workspace bind-mounted
  if ! mountpoint -q "$CHROOT_TARGET/workspace" 2>/dev/null; then
    echo "ERROR: Workspace not bind-mounted at $CHROOT_TARGET/workspace" >&2
    echo "Run: sudo mount --bind $TOPDIR $CHROOT_TARGET/workspace" >&2
    exit 1
  fi

  # Check rpmbuild exists in chroot
  if [[ ! -x "$CHROOT_TARGET/usr/bin/rpmbuild" ]]; then
    echo "ERROR: rpmbuild not found in chroot at $CHROOT_TARGET/usr/bin/rpmbuild" >&2
    echo "The rootfs must have rpm package installed." >&2
    exit 1
  fi
}

# ============================================================================
# Resolve spec file
# ============================================================================

if [[ "$SPEC_INPUT" == *.spec ]]; then
  SPEC_NAME="$SPEC_INPUT"
else
  SPEC_NAME="${SPEC_INPUT}.spec"
fi
SPEC_FILE="$TOPDIR/SPECS/$SPEC_NAME"

if [[ ! -f "$SPEC_FILE" ]]; then
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

# ============================================================================
# Check sources exist
# ============================================================================

check_sources() {
  local spec="$1"
  local sources_dir="$TOPDIR/SOURCES"
  
  # Extract Source0 from spec (filename only)
  local source_file
  source_file=$(grep -E '^Source0:' "$spec" | awk '{print $2}' || true)
  
  if [[ -n "$source_file" ]]; then
    # Handle %{version} expansion
    local version
    version=$(grep '^Version:' "$spec" | awk '{print $2}')
    source_file=$(echo "$source_file" | sed "s/%{version}/$version/g")
    
    if [[ ! -f "$sources_dir/$source_file" ]]; then
      echo "ERROR: Source not found: $sources_dir/$source_file" >&2
      echo "Download it first: ./scripts/fetch-spec-sources.sh ${SPEC_INPUT%.spec}" >&2
      return 1
    fi
    echo "[build] Found source: $source_file"
  fi
}

# ============================================================================
# Run rpmbuild inside chroot
# ============================================================================

run_rpmbuild_in_chroot() {
  local target="$1"
  shift || true
  
  local target_args=()
  if [[ -n "$target" ]]; then
    target_args=("--target" "$target")
  fi
  
  echo "[build] Building $SPEC_NAME for ${target:-host} inside chroot..."
  
  # Build the rpmbuild command to run inside chroot
  # The workspace is mounted at /workspace inside chroot
  local rpmbuild_cmd=(
    /usr/bin/rpmbuild -ba "/workspace/SPECS/$SPEC_NAME"
    --define "_topdir /workspace"
    --define "_builddir /workspace/BUILD"
    --define "_buildrootdir /workspace/BUILDROOT"
    --define "_specdir /workspace/SPECS"
    --define "_sourcedir /workspace/SOURCES"
    --define "_rpmdir /workspace/RPMS"
    --define "_srcrpmdir /workspace/SRPMS"
    "${target_args[@]}"
    "${EXTRA_ARGS[@]}"
  )
  
  # Execute inside chroot using LFS pattern
  # -i clears environment, we set only what's needed
  local chroot_cmd=(
    /usr/bin/env -i
    HOME=/root
    TERM="${TERM:-xterm}"
    PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    "${rpmbuild_cmd[@]}"
  )
  
  # Run chroot (requires root)
  if [[ $EUID -eq 0 ]]; then
    exec chroot "$CHROOT_TARGET" "${chroot_cmd[@]}"
  else
    if [[ -z "$SUDO_CMD" ]]; then
      echo "ERROR: sudo not found (required for chroot)" >&2
      exit 1
    fi
    exec "$SUDO_CMD" chroot "$CHROOT_TARGET" "${chroot_cmd[@]}"
  fi
}

# ============================================================================
# Detect i686 support in spec
# ============================================================================

supports_i686() {
  if grep -Eq '^ExclusiveArch:[[:space:]]*x86_64' "$SPEC_FILE"; then
    return 1
  fi
  grep -Eq 'i686-pc-linux-gnu|/usr/lib/i386-linux-gnu|_target_cpu.*i686|%ifarch[[:space:]]+i686|gcc[[:space:]]+-m32' "$SPEC_FILE"
}

# ============================================================================
# Main
# ============================================================================

verify_chroot
check_sources "$SPEC_FILE" || exit 1

if [[ "$BUILD_BOTH" = "true" ]]; then
  run_rpmbuild_in_chroot x86_64
  # Note: for --both, we'd need to call twice but exec replaces process
  # For now, --both requires refactoring to not use exec
  echo "[build] Note: --both builds x86_64 only in this version. Re-run with --arch i686 for 32-bit."
elif [[ -n "$TARGET_CPU" ]]; then
  run_rpmbuild_in_chroot "$TARGET_CPU"
else
  run_rpmbuild_in_chroot ""
fi
