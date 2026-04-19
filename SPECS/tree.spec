%define pkg_version 2.2.1

# Disable debuginfo
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

Name:           tree
Version:        %{pkg_version}
Release:        1.m264%{?dist}
Summary:        List directory contents in a tree-like format

License:        GPL-2.0-or-later
URL:            http://mama.indstate.edu/users/ice/tree/
Source0:        https://github.com/Old-Man-Programmer/tree/archive/refs/tags/2.2.1.tar.gz

BuildRequires:  gcc
BuildRequires:  make

%description
tree is a recursive directory listing program that produces a depth
indented listing of files. With no arguments, tree lists the files in
the current directory. When directory arguments are given, tree lists
all the files and/or directories found in the given directories each in
turn. Upon completion of listing all files/directories found, tree
returns the total number of files and/or directories listed.

%prep
%setup -q -n tree-%{version}

%build
make \
  CFLAGS="$RPM_OPT_FLAGS -DLINUX -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64" \
  LDFLAGS="$RPM_LD_FLAGS"

%install
install -D -m 0755 tree %{buildroot}%{_bindir}/tree
install -D -m 0644 doc/tree.1 %{buildroot}%{_mandir}/man1/tree.1
install -D -m 0644 doc/tree.1.fr %{buildroot}%{_mandir}/fr/man1/tree.1
install -D -m 0644 doc/tree.1.es %{buildroot}%{_mandir}/es/man1/tree.1

%files
%license LICENSE
%doc README CHANGES
%{_bindir}/tree
%{_mandir}/man1/tree.1*

%changelog
* Sat Apr 19 2026 Maqui Linux <security@maqui-linux.org> - 2.2.1-1.m264
- Initial build for Maqui Linux 26.4
