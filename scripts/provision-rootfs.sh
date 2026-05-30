#!/bin/bash
# scripts/provision-rootfs.sh — Run inside chroot after RPM install
# Verifies all Capa 1 requirements are met
set -e

echo "=== Capa 1 Verification ==="

PASS=0
FAIL=0

check() {
    local desc="$1"
    shift
    if "$@" >/dev/null 2>&1; then
        echo "  PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $desc"
        FAIL=$((FAIL + 1))
    fi
}

# 1. DNS
echo "[1/6] Checking /etc/resolv.conf..."
check "resolv.conf exists" test -f /etc/resolv.conf
check "resolv.conf has nameservers" grep -q nameserver /etc/resolv.conf

# 2. CA certs
echo "[2/6] Checking CA certificates..."
check "ca-certificates.crt exists" test -f /etc/ssl/certs/ca-certificates.crt
check "ca-bundle.crt symlink" test -L /etc/pki/tls/certs/ca-bundle.crt
check "cert.pem exists" test -f /etc/ssl/cert.pem

# 3. Repo file
echo "[3/6] Checking repo configuration..."
check "maquilinux.repo exists" test -f /etc/yum.repos.d/maquilinux.repo
check "gpgcheck=1 in repo" grep -q 'gpgcheck=1' /etc/yum.repos.d/maquilinux.repo
check "gpgkey in repo" grep -q 'gpgkey=' /etc/yum.repos.d/maquilinux.repo

# 4. GPG key
echo "[4/6] Checking GPG key..."
check "GPG key file exists" test -f /etc/pki/rpm-gpg/RPM-GPG-KEY-maquilinux
check "GPG key in RPM DB" rpm -qa gpg-pubkey* | grep -q gpg-pubkey

# 5. dhcpcd
echo "[5/6] Checking dhcpcd service..."
check "dhcpcd init script exists" test -f /etc/init.d/dhcpcd
check "dhcpcd in default runlevel" rc-update show default | grep -q dhcpcd

# 6. curl/SSL config
echo "[6/6] Checking SSL/curl configuration..."
check "curlrc exists" test -f /etc/curlrc
check "SSL cert profile script" test -f /etc/profile.d/ssl-cert.sh

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    echo "SOME CHECKS FAILED"
    exit 1
fi
echo "All checks passed"
