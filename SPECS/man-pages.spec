Name:           man-pages
Version:        6.16
Release:        1.m264%{?dist}
Summary:        Linux Manual Pages
 
# Built inside a minimal LFS-style chroot without find-debuginfo or brp helpers.
# Disable those automatic steps so rpmbuild does not expect the missing tools.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}
License:        Various
URL:            https://www.kernel.org/pub/linux/docs/man-pages/
Source0:        https://www.kernel.org/pub/linux/docs/man-pages/man-pages-%{version}.tar.xz
BuildArch:      noarch

%description
The Man-pages package contains core Linux manual pages. These pages provide essential
documentation for system commands, library functions, system calls, file formats,
and kernel interfaces.

%prep
# This section prepares the source code for building.
# %setup -q unpacks the source tarball (Source0) quietly.
# It also changes the current directory to the top-level directory of the unpacked sources.
%setup -q

# Remove man pages for password hashing functions, as per LFS instructions.
# Libxcrypt will provide better versions.
rm -v man3/crypt*

%build
# This section would normally contain commands to compile the software.
# For man-pages, there isn't a traditional compilation step.
# The LFS instructions directly use 'make install' which is handled in the %install section.
# So, this section is intentionally left empty.

%install
# This section contains commands to install the built software into a temporary
# build root, which RPM uses to package the files.
# RPM_BUILD_ROOT (or %{buildroot}) is the path to this temporary root.
# We first ensure the build root is clean.
rm -rf %{buildroot}

# The LFS command is 'make prefix=/usr install'.
# In RPM, %{_prefix} usually expands to /usr.
# We prepend %{buildroot} to install into the staging area.
make -R GIT=false prefix=%{buildroot}%{_prefix} install

%files
# This section lists all the files that will be included in the RPM package.
# %doc is used for documentation files. RPM will place them in a standard
# documentation directory for the package. README.md and the LICENSES
# directory are included from the source tarball.
%doc README LICENSES/*

# This line includes all files and subdirectories under all man* directories
# (e.g., man1, man2, ..., man8, manl, mann, manp).
%{_mandir}/man*/*

# Helper scripts installed by man-pages 6.16
%{_bindir}/diffman-git
%{_bindir}/mansect
%{_bindir}/pdfman
%{_bindir}/sortman

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 6.16-1.m264
- Initial RPM packaging for LFS.
