Name:           expect
Version:        5.45.4
Release:        1.m264%{?dist}
Summary:        Automate interactive applications and testing

# Built inside a minimal LFS-style chroot; disable helpers not available here.
%define debug_package       %{nil}
%define __debug_install_post %{nil}
%define __os_install_post   %{nil}

License:        MIT
URL:            https://core.tcl-lang.org/expect/
Source0:        https://prdownloads.sourceforge.net/expect/expect%{version}.tar.gz
Patch0:         expect-%{version}-gcc15-1.patch

%description
Expect is a tool for automating interactive applications such as telnet,
ftp, passwd, fsck, rlogin, and tip. It is also useful for testing those
applications. The DejaGnu test framework is written in Expect.

%prep
%setup -q -n expect%{version}

# Fix build with gcc-15 and later, as per MLFS instructions
%patch 0 -p1

%build
./configure \
    --prefix=%{_prefix} \
    --with-tcl=/usr/lib \
    --enable-shared \
    --disable-rpath \
    --mandir=%{_mandir} \
    --with-tclinclude=/usr/include

make %{?_smp_mflags}

%check
make test || :

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

# Create the libexpect symlink as requested by MLFS
ln -svf expect5.45.4/libexpect5.45.4.so %{buildroot}/usr/lib/libexpect5.45.4.so

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/expect-files.list

%files -f %{_builddir}/expect-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 5.45.4-1.m264
- Initial RPM packaging for Expect following MLFS instructions.
