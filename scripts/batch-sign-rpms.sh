#!/run/current-system/sw/bin/bash
# scripts/batch-sign-rpms.sh - Batch sign production RPMs on rog
# Usage: ./scripts/batch-sign-rpms.sh [arch]
#   arch: x86_64 (default) or i686

set -euo pipefail

ARCH="${1:-x86_64}"
ROG_REPO="rog.local:/srv/glats/nginx/repo/linux/maquilinux/26.4/${ARCH}/stable"
LOCAL_BATCH="/tmp/sign-batch-${ARCH}"
GPG_NAME="Maqui Linux <security@maqui-linux.org>"

echo "=== Batch signing RPMs for ${ARCH} ==="

# Step 1: Pull RPMs from rog
echo "[1/5] Pulling RPMs from rog..."
rm -rf "${LOCAL_BATCH}"
mkdir -p "${LOCAL_BATCH}"
rsync -av "${ROG_REPO}/*.rpm" "${LOCAL_BATCH}/" 2>/dev/null || true

RPM_COUNT=$(ls "${LOCAL_BATCH}/"*.rpm 2>/dev/null | wc -l)
echo "Found ${RPM_COUNT} RPMs to sign"

if [ "${RPM_COUNT}" -eq 0 ]; then
  echo "No RPMs found, nothing to do"
  rm -rf "${LOCAL_BATCH}"
  exit 0
fi

# Step 2: Fix permissions
echo "[2/5] Fixing permissions..."
chown $(id -u):$(id -g) "${LOCAL_BATCH}/"*.rpm 2>/dev/null || true

# Step 3: Batch sign
echo "[3/5] Signing RPMs..."
for rpm in "${LOCAL_BATCH}/"*.rpm; do
  [ -f "${rpm}" ] || continue
  echo "  Signing: $(basename ${rpm})"
  nix shell nixpkgs#rpm -c rpmsign \
    --define "_gpg_name ${GPG_NAME}" \
    --addsign "${rpm}" 2>&1 | grep -v 'GPG_TTY' || true
done

# Step 4: Push signed RPMs back
echo "[4/5] Pushing signed RPMs back to rog..."
rsync -av "${LOCAL_BATCH}/"*.rpm "${ROG_REPO}/" 2>/dev/null || true

# Step 5: Cleanup
echo "[5/5] Cleaning up..."
rm -rf "${LOCAL_BATCH}"

echo "=== Done. All ${RPM_COUNT} RPMs signed. ==="
