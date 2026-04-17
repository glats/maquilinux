%define bzip2_version 1.0.8

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global bzip2_multilibdir /usr/lib/i386-linux-gnu
%global bzip2_enable_devel 0
%else
%global bzip2_multilibdir /usr/lib/x86_64-linux-gnu
%global bzip2_enable_devel 1
%endif

Name:           bzip2
Version:        %{bzip2_version}
Release:        1.m264%{?dist}
Summary:        High-quality block-sorting file compressor

%if "%{_target_cpu}" == "x86_64"
Provides:       libbz2.so.1.0()(64bit)
%endif

License:        BSD
URL:            https://sourceware.org/bzip2/
Source0:        https://sourceware.org/pub/bzip2/bzip2-%{version}.tar.gz
Patch0:         bzip2-%{version}-install_docs-1.patch

%if %{bzip2_enable_devel}
%package devel
Summary:        Development files for bzip2
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers and the unversioned shared library symlink for developing against bzip2.
%endif

%description
Bzip2 compresses files using the Burrows-Wheeler block-sorting text compression
algorithm with Huffman coding. It typically achieves better compression ratios
on text files than traditional gzip.

%prep
%setup -q -n bzip2-%{version}

patch -Np1 -i %{PATCH0}

# Make the installed symlinks relative and place man pages under share/man.
sed -i 's@\(ln -s -f \)$(PREFIX)/bin/@\1@' Makefile
sed -i 's@(PREFIX)/man@(PREFIX)/share/man@g' Makefile

%build
%if "%{_target_cpu}" == "i686"
sed -e 's/^CC=.*/CC=gcc -m32/' -i Makefile{,-libbz2_so}
%endif

make -f Makefile-libbz2_so
make clean
make %{?_smp_mflags}

%check
make check

%install
rm -rf %{buildroot}

%if "%{_target_cpu}" == "i686"
install -vdm 755 %{buildroot}%{bzip2_multilibdir}
install -vm755 libbz2.so.1.0.8 %{buildroot}%{bzip2_multilibdir}/libbz2.so.1.0.8
ln -sfv libbz2.so.1.0.8 %{buildroot}%{bzip2_multilibdir}/libbz2.so
ln -sfv libbz2.so.1.0.8 %{buildroot}%{bzip2_multilibdir}/libbz2.so.1
ln -sfv libbz2.so.1.0.8 %{buildroot}%{bzip2_multilibdir}/libbz2.so.1.0

rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
%else
make PREFIX=%{buildroot}%{_prefix} install
install -vm755 bzip2-shared %{buildroot}%{_bindir}/bzip2
for link in bunzip2 bzcat; do
    ln -sfv bzip2 %{buildroot}%{_bindir}/${link}
done

install -vdm 755 %{buildroot}%{bzip2_multilibdir}
cp -a libbz2.so.* %{buildroot}%{bzip2_multilibdir}/
ln -sfv libbz2.so.1.0.8 %{buildroot}%{bzip2_multilibdir}/libbz2.so

install -vdm 755 %{buildroot}%{_docdir}/bzip2-%{version}
cp -av manual* README* CHANGES %{buildroot}%{_docdir}/bzip2-%{version}/
%endif

rm -fv %{buildroot}%{bzip2_multilibdir}/libbz2.a || :
rm -fv %{buildroot}/usr/lib/libbz2.a || :
rm -fv %{buildroot}/usr/lib64/libbz2.a || :
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{bzip2_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/bzip2-files.list
%else
# Runtime: versioned shared libs, binaries, man pages, docs
{
  find .%{bzip2_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libbz2.so.*'
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/bzip2-runtime.list

%if %{bzip2_enable_devel}
# Development: headers, unversioned .so symlink
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{bzip2_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name 'libbz2.so'
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/bzip2-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/bzip2-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/bzip2-runtime.list
%defattr(-,root,root,-)

%if %{bzip2_enable_devel}
%files devel -f %{_builddir}/bzip2-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 1.0.8-1.m264
- Gen3 update: real -devel split, explicit Provides, normalized filelists, ldconfig.
