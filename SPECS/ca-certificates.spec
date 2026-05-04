%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%define blddir cacert

Name:           ca-certificates
Version:        20260319
Release:        1.m264%{?dist}
Summary:        Mozilla CA Certificate Bundle
BuildArch:      noarch

# Disable automatic debuginfo and BRP post scripts for noarch data package.

License:        MPL-2.0
URL:            https://curl.se/docs/caextract.html
Source0:        https://curl.se/ca/cacert-2026-03-19.pem

%description
The Mozilla CA Certificate Bundle. This package contains the CA root
certificates trusted by Mozilla and used by TLS clients (curl, openssl,
wget, dnf5, python3, etc.) for HTTPS verification.

%prep
cp -v %{SOURCE0} cacert.pem

%build

%install
rm -rf %{buildroot}

install -vdm 755 %{buildroot}/etc/ssl/certs
install -vdm 755 %{buildroot}/etc/pki/tls/certs

install -vm 644 cacert.pem %{buildroot}/etc/ssl/certs/ca-certificates.crt

# Compatibility symlinks for Fedora/RHEL path conventions
ln -sv /etc/ssl/certs/ca-certificates.crt %{buildroot}/etc/pki/tls/certs/ca-bundle.crt
ln -sv /etc/ssl/certs/ca-certificates.crt %{buildroot}/etc/pki/tls/certs/ca-bundle.trust.crt

%files
%defattr(-,root,root)
%dir /etc/ssl
%dir /etc/ssl/certs
%dir /etc/pki
%dir /etc/pki/tls
%dir /etc/pki/tls/certs
/etc/ssl/certs/ca-certificates.crt
/etc/pki/tls/certs/ca-bundle.crt
/etc/pki/tls/certs/ca-bundle.trust.crt

%changelog
* Tue Mar 24 2026 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 20260319-1.m264
- Initial RPM packaging from Mozilla CA bundle extracted by curl.se