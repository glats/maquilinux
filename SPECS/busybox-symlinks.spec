Name:           busybox-symlinks
Version:        1.36.1
Release:        1.m264%{?dist}
Summary:        Symlinks for busybox applets

%define debug_package        %{nil}

License:        GPL-2.0-only
URL:            https://busybox.net/
Requires:       busybox

Provides:       cpio = %{version}
Provides:       /usr/bin/cpio

%description
This package creates a symlink from busybox cpio applet to /usr/bin/cpio,
allowing busybox to function as a drop-in replacement for GNU cpio.

%prep

%build

%install
mkdir -p %{buildroot}/usr/bin

# Create cpio symlink only
ln -sf /bin/busybox %{buildroot}/usr/bin/cpio

%files
%defattr(-,root,root)
/usr/bin/cpio

%changelog
* Thu Apr 09 2026 Maqui Linux Team <team@maqui-linux.org> - 1.36.1-1.m264
- Initial package: provides cpio via busybox for dracut
