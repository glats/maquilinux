Name:           linux-api-headers
Version:        6.17.9
Release:        1.m264%{?dist}
Summary:        Linux kernel API headers for userspace programs

# These are sanitized headers from the kernel source via make headers_install.
# They provide the Linux kernel API for glibc and other userspace programs.
ExclusiveArch:  x86_64

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        GPL-2.0-only
URL:            https://www.kernel.org/
Source0:        https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-%{version}.tar.xz
Provides:       kernel-headers

# No BuildRequires needed - this package extracts headers from the kernel source.
# The kernel source tarball (Source0) contains everything needed.

%description
The Linux API Headers expose the kernel's system call interface and the
kernel API used by glibc and other user-space programs. These are the
sanitized headers produced by "make headers_install" from the kernel source.

%prep
%autosetup -n linux-%{version}

%build
# Prepare the source for header extraction.
# make mrproper ensures a clean build environment.
make mrproper

# Run the headers_install target to extract sanitized user-space headers.
# This is the standard way to produce the Linux API headers.
make headers

# Sanitize the extracted headers:
# - Remove hidden files (.*) that may have been created
# - Remove the Makefile as it's only for kernel build use
# - No other cleaning is needed for user-space headers
find usr/include -name '.*' -delete
rm -f usr/include/Makefile

%install
rm -rf %{buildroot}
install -vdm 755 %{buildroot}/usr/include

# Install the sanitized headers into the build root.
# The headers are placed in /usr/include/ in the standard user-space layout.
# This includes:
# - /usr/include/linux/ (Linux-specific APIs)
# - /usr/include/asm/ (arch-specific syscall numbers)
# - /usr/include/asm-generic/ (generic arch definitions)
# - /usr/include/mtd/ (memory technology devices)
# - /usr/include/rdma/ (RDMA verbs)
# - /usr/include/scsi/ (SCSI specific APIs)
# - /usr/include/video/ (video4linux APIs)
# - /usr/include/xen/ (Xen hypervisor APIs)
cp -rv usr/include/* %{buildroot}/usr/include/

%files
# List all installed header files dynamically.
# This captures everything under /usr/include/ from the headers_install output.
%defattr(-,root,root)
%{_includedir}/*

%changelog
* Sun May 03 2026 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 6.17.9-1.m264
- Initial RPM packaging of Linux API headers for Maquilinux.