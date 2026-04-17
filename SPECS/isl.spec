%define isl_version 0.27

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global isl_multilibdir /usr/lib/i386-linux-gnu
%global isl_enable_devel 0
%else
%global isl_multilibdir /usr/lib/x86_64-linux-gnu
%global isl_enable_devel 1
%endif

Name:           isl
Version:        %{isl_version}
Release:        1.m264%{?dist}
Summary:        Integer set manipulation library

%if "%{_target_cpu}" == "x86_64"
Provides:       libisl.so.23()(64bit)
%endif

License:        MIT
URL:            https://libisl.sourceforge.io/
Source0:        https://libisl.sourceforge.io/isl-%{version}.tar.xz

%if %{isl_enable_devel}
%package devel
Summary:        Development files for isl
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlink
for developing against ISL.
%endif

%description
ISL (Integer Set Library) is a thread-safe C library for manipulating sets
and relations of integer points bounded by affine constraints. It is used
by compilers and other tools that need precise reasoning about integer
iteration domains and access patterns.

%prep
%setup -q -n isl-%{version}

%build
%if "%{_target_cpu}" == "i686"
CFLAGS="${CFLAGS:-} -m32" \
CXXFLAGS="${CXXFLAGS:-} -m32" \
CPPFLAGS="${CPPFLAGS:-} -I/usr/include/i386-linux-gnu" \
LDFLAGS="${LDFLAGS:-} -L/usr/lib/i386-linux-gnu" \
CC="gcc -m32" CXX="g++ -m32" \
export CFLAGS CXXFLAGS CPPFLAGS LDFLAGS
./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --host=i686-pc-linux-gnu \
    --libdir=/usr/lib/i386-linux-gnu
%else
./configure \
    --prefix=%{_prefix} \
    --disable-static \
    --docdir=%{_datadir}/doc/isl-%{version} \
    --libdir=/usr/lib/x86_64-linux-gnu
%endif

make %{?_smp_mflags}

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.a || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/*.la || :
%else
install -vd %{buildroot}%{_datadir}/doc/isl-%{version}
install -m644 doc/{CodingStyle,manual.pdf,SubmittingPatches,user.pod} \
    %{buildroot}%{_datadir}/doc/isl-%{version}

install -vd %{buildroot}%{_datadir}/gdb/auto-load/usr/lib
mv -v %{buildroot}%{_libdir}/libisl*gdb.py \
    %{buildroot}%{_datadir}/gdb/auto-load/usr/lib || :

rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/*.a || :
rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/*.la || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{isl_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/isl-files.list
%else
# Runtime: versioned shared libs, docs, gdb scripts
{
  find .%{isl_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
  if [ -d ./usr/share/gdb ]; then
    find ./usr/share/gdb -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/isl-runtime.list

%if %{isl_enable_devel}
# Development: headers, pkgconfig, unversioned .so symlink
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{isl_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -d .%{isl_multilibdir}/pkgconfig ]; then
    find .%{isl_multilibdir}/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/isl-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/isl-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/isl-runtime.list
%defattr(-,root,root,-)

%if %{isl_enable_devel}
%files devel -f %{_builddir}/isl-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 0.27-1.m264
- Initial RPM packaging for ISL.
