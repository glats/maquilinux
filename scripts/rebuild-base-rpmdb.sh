#!/usr/bin/env bash
# Rebuild RPM database in base rootfs

BASE="/run/media/glats/maquilinux/base"
RPMS="/home/glats/Work/maquilinux/RPMS/x86_64"

echo "Installing RPMs from $RPMS to $BASE..."
echo ""

# Initialize RPM database
sudo mkdir -p "$BASE/var/lib/rpm"

# Count RPMs
count=$(ls "$RPMS"/*.rpm 2>/dev/null | wc -l)
echo "Found $count RPM files"
echo ""

# Install each RPM (ignore deps for now, just register them)
for rpm_file in "$RPMS"/*.rpm; do
    [ -f "$rpm_file" ] || continue
    echo "Installing: $(basename "$rpm_file")"
    sudo rpm --nodeps --root "$BASE" -Uvh "$rpm_file" 2>/dev/null || {
        echo "  (already installed or error, continuing...)"
    }
done

echo ""
echo "Verification:"
sudo chroot "$BASE" /usr/bin/rpm -qa 2>/dev/null | wc -l | xargs echo " packages in database"
