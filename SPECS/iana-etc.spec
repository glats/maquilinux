Name:           iana-etc
Version:        20251120
Release:        1.m264%{?dist}
Summary:        Provides data for network services and protocols
 
# Built inside a minimal LFS-style chroot without find-debuginfo or brp helpers.
# Disable those automatic steps so rpmbuild does not expect the missing tools.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}
License:        MIT
URL:            https://github.com/Mic92/iana-etc
Source0:        https://github.com/Mic92/iana-etc/releases/download/%{version}/%{name}-%{version}.tar.gz
BuildArch:      noarch

%description
The Iana-Etc package provides data for network services and protocols.
It includes the /etc/protocols and /etc/services files, which map
textual names for services and protocols to their assigned port numbers
and protocol types.

%prep
# %setup -q unpacks the source tarball quietly.
# The -n option is used if the tarball extracts to a directory
# with a different name than %{name}-%{version}.
# Based on the Source0 URL, the tarball is iana-etc-%{version}.tar.gz
# and it should extract to iana-etc-%{version}.
%setup -q -n %{name}-%{version}

%build
# This package does not require a build step.
# The files are copied directly in the %install section.

%install
# Create the target directory in the build root.
mkdir -pv %{buildroot}/etc

# Copy the files into the build root, as per LFS instructions.
# The LFS command is: cp services protocols /etc
# We need to copy from the source directory (which is the current directory
# after %setup) to %{buildroot}/etc/
cp -v services protocols %{buildroot}/etc/

%files
# %config(noreplace) ensures that user-modified versions of these
# configuration files are not overwritten during package upgrades.
%config(noreplace) /etc/protocols
%config(noreplace) /etc/services

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 20251120-1.m264
- Initial RPM packaging for LFS.
