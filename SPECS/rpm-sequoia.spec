%define pkg_version 1.10.1

# Disable debuginfo in bootstrap/minimal chroot
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

# Multiarch configuration
%if "%{_target_cpu}" == "i686"
%global pkg_multilibdir /usr/lib/i386-linux-gnu
%global pkg_enable_devel 0
%else
%global pkg_multilibdir /usr/lib/x86_64-linux-gnu
%global pkg_enable_devel 1
%endif

Name:           rpm-sequoia
Version:        %{pkg_version}
Release:        1.m264%{?dist}
Summary:        Sequoia OpenPGP library for RPM

License:        LGPL-2.0-or-later
URL:            https://github.com/rpm-software-management/rpm-sequoia
Source0:        https://crates.io/api/v1/crates/rpm-sequoia/%{version}/download -> rpm-sequoia-%{version}.crate

# SHA256 checksum (verified in %%prep)
%define sha256_crate bad6b67c55606b3d0c3101ad2870fc75613286e95d71fc4c8aa29d5f4d616a39

BuildRequires:  cargo
BuildRequires:  rust >= 1.75
BuildRequires:  rust-std
BuildRequires:  pkgconf
BuildRequires:  nettle-devel
BuildRequires:  gpgme-devel

ExclusiveArch:  x86_64 i686

# Explicit Provides for shared library sonames (required for bootstrap)
%if "%{_target_cpu}" == "x86_64"
Provides:       librpm_sequoia.so.1()(64bit)
%endif

%description
RPM Sequoia provides an implementation of the RPM PGP interface using the
Sequoia OpenPGP library. This library enables RPM to verify package
signatures using modern OpenPGP backends.

%package devel
Summary:        Development files for rpm-sequoia
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers and pkg-config files for developing applications that use rpm-sequoia.

%prep
# Verify crate checksum
echo "%{sha256_crate}  %{SOURCE0}" | sha256sum -c -

%setup -q -n rpm-sequoia-%{version}

%build
# Build with cargo, produce cdylib
export CARGO_HOME="%{_builddir}/cargo-home"
export CARGO_TARGET_DIR="%{_builddir}/target"
cargo build --release --features crypto-nettle

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{pkg_multilibdir}
mkdir -p %{buildroot}/usr/include
mkdir -p %{buildroot}%{_libdir}/pkgconfig

# Install shared library
install -m 755 %{_builddir}/target/release/librpm_sequoia.so \
    %{buildroot}%{pkg_multilibdir}/librpm_sequoia.so.%{version}
ln -sf librpm_sequoia.so.%{version} %{buildroot}%{pkg_multilibdir}/librpm_sequoia.so

# Install header (if any)
if [ -f include/rpm_sequoia.h ]; then
    install -m 644 include/rpm_sequoia.h %{buildroot}/usr/include/
fi

# Generate pkg-config file
cat > %{buildroot}%{_libdir}/pkgconfig/rpm-sequoia.pc << EOF
prefix=%{_prefix}
libdir=%{pkg_multilibdir}
includedir=%{_includedir}

Name: rpm-sequoia
Description: Sequoia OpenPGP library for RPM
Version: %{version}
Libs: -L\${libdir} -lrpm_sequoia
Cflags: -I\${includedir}
EOF

# Remove static libraries
rm -fv %{buildroot}%{pkg_multilibdir}/*.a || :
rm -fv %{buildroot}%{pkg_multilibdir}/*.la || :

# Generate file lists
cd %{buildroot}
%if "%{_target_cpu}" == "i686"
{
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/rpm-sequoia-files.list
%else
find . \( -type f -o -type l \) | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/rpm-sequoia-all.list

# Runtime files (shared library)
{
  if [ -d ./usr/lib/x86_64-linux-gnu ]; then
    find ./usr/lib/x86_64-linux-gnu -maxdepth 1 \( -type f -o -type l \) -name 'librpm_sequoia.so*'
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/rpm-sequoia-runtime.list

# Development files
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d ./usr/lib/x86_64-linux-gnu/pkgconfig ]; then
    find ./usr/lib/x86_64-linux-gnu/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/rpm-sequoia-devel.list
%endif

%post
%{_sbindir}/ldconfig || :

%postun
%{_sbindir}/ldconfig || :

%files -f %{_builddir}/rpm-sequoia-runtime.list
%defattr(-,root,root)

%files devel -f %{_builddir}/rpm-sequoia-devel.list
%defattr(-,root,root)

%changelog
* Fri Apr 18 2026 Your Name <email@example.com> - 1.10.1-1.m264
- Initial package of rpm-sequoia.