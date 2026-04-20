Name:           nettle
Version:        3.10
Release:        1.m264%{?dist}
Summary:        A low-level cryptographic library

%define debug_package %{nil}
%define __os_install_post %{nil}

License:        LGPL-3.0-or-later AND GPL-2.0-or-later
URL:            https://www.lysator.liu.se/~nisse/nettle/
# Download URL: https://ftp.gnu.org/gnu/nettle/nettle-3.10.tar.gz
Source0:        nettle-3.10.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  gmp-devel

Requires:       gmp

%description
Nettle is a cryptographic library that is designed to fit easily in more or less
any context: In crypto toolkits for object-oriented languages (C++, Python, Pike,
etc.), in applications like LSH or GnuPG, or even in kernel space. It is written
in an object-oriented manner with many objects and flexible functions.

%package devel
Summary:        Development files for nettle
Requires:       %{name} = %{version}-%{release}
Requires:       gmp-devel

%description devel
The nettle-devel package contains libraries and header files for developing
applications that use nettle.

%prep
%setup -q

%build
./configure \
    --prefix=%{_prefix} \
    --libdir=%{_libdir} \
    --enable-shared \
    --disable-static

make %{?_smp_mflags}

%install
make DESTDIR=%{buildroot} install

# Remove static libraries
rm -f %{buildroot}%{_libdir}/*.a

# Move documentation
mkdir -p %{buildroot}%{_docdir}/%{name}-%{version}
cp -a ChangeLog COPYING* NEWS README %{buildroot}%{_docdir}/%{name}-%{version}/ 2>/dev/null || true

# Remove /usr/share/info/dir (generated file, not packaged)
rm -f %{buildroot}%{_infodir}/dir

%files
%license COPYING* AUTHORS
%doc %{_docdir}/%{name}-%{version}
%{_libdir}/libnettle.so.8*
%{_libdir}/libhogweed.so.6*
%{_bindir}/nettle-hash
%{_bindir}/nettle-lfib-stream
%{_bindir}/nettle-pbkdf2
%{_bindir}/pkcs1-conv
%{_bindir}/sexp-conv

%files devel
%{_includedir}/nettle
%{_libdir}/libnettle.so
%{_libdir}/libhogweed.so
%{_libdir}/pkgconfig/nettle.pc
%{_libdir}/pkgconfig/hogweed.pc
%{_infodir}/nettle.info*

%changelog
* Sun Apr 19 2026 Maqui Linux <security@maqui-linux.org> - 3.10-1.m264
- Initial build for Maqui Linux 26.4
