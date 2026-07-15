# SPECS/maquilinux-release.spec
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

Name:           maquilinux-release
Version:        26.4
Release:        1.m264%{?dist}
Summary:        Maqui Linux release configuration
BuildArch:      noarch
License:        MIT
URL:            https://maquilinux.org
Source0:        maquilinux.repo
Source1:        RPM-GPG-KEY-maquilinux
Source2:        maquilinux-resolv.conf

Requires:       ca-certificates
Requires:       dhcpcd

%description
Maqui Linux release package. Ships the production DNF repository
configuration with GPG verification, the Maqui Linux GPG public key,
and a static DNS resolver configuration. Enables dhcpcd for automatic
network configuration at boot.

%prep
# Nothing to prep — all sources are static files

%build
# Nothing to build — static file package

%install
rm -rf %{buildroot}

install -Dm644 %{SOURCE0} %{buildroot}/etc/yum.repos.d/maquilinux.repo
install -Dm644 %{SOURCE1} %{buildroot}/etc/pki/rpm-gpg/RPM-GPG-KEY-maquilinux
install -Dm644 %{SOURCE2} %{buildroot}/etc/resolv.conf

# Create global curl config to point to CA bundle
install -vdm 755 %{buildroot}/etc
cat > %{buildroot}/etc/curlrc << 'EOF'
cacert = /etc/ssl/certs/ca-certificates.crt
EOF

# Create SSL cert environment profile script
install -vdm 755 %{buildroot}/etc/profile.d
cat > %{buildroot}/etc/profile.d/ssl-cert.sh << 'EOF'
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
EOF

%post
# Import GPG key into RPM database
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-maquilinux 2>/dev/null || true

# Enable dhcpcd at boot (OpenRC)
if command -v rc-update >/dev/null 2>&1; then
    rc-update add dhcpcd default 2>/dev/null || true
fi

# Create cert.pem symlink for OpenSSL default path
ln -sf /etc/ssl/certs/ca-certificates.crt /etc/ssl/cert.pem 2>/dev/null || true

# Create .curlrc symlink so curl finds CA certs
ln -sf /etc/curlrc /root/.curlrc 2>/dev/null || true

%files
%defattr(-,root,root)
/etc/yum.repos.d/maquilinux.repo
/etc/pki/rpm-gpg/RPM-GPG-KEY-maquilinux
/etc/resolv.conf
/etc/curlrc
/etc/profile.d/ssl-cert.sh

%changelog
* Fri May 29 2026 Maqui Linux <info@maquilinux.org> - 26.4-1.m264
- Production repo file with gpgcheck=1 and GPG key path
- Static DNS configuration (Cloudflare + Google fallback)
- GPG key import in %post
- dhcpcd OpenRC service enabled in %post
- Global curl config with CA bundle path
- SSL_CERT_FILE environment variable in profile.d
