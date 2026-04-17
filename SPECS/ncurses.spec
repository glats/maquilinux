%define ncurses_version 6.5

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global ncurses_multilibdir /usr/lib/i386-linux-gnu
%global ncurses_enable_devel 0
%else
%global ncurses_multilibdir /usr/lib/x86_64-linux-gnu
%global ncurses_enable_devel 1
%endif

Name:           ncurses
Version:        %{ncurses_version}
Release:        1.m264%{?dist}
Summary:        Libraries for terminal-independent character screens

%if "%{_target_cpu}" == "x86_64"
Provides:       libncursesw.so.6()(64bit)
Provides:       libformw.so.6()(64bit)
Provides:       libpanelw.so.6()(64bit)
Provides:       libmenuw.so.6()(64bit)
%endif

License:        MIT
URL:            https://invisible-island.net/ncurses/
Source0:        ncurses-%{version}-20250809.tgz

%if %{ncurses_enable_devel}
%package devel
Summary:        Development files for ncurses
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and shared library symlinks for developing
against ncurses.
%endif

%description
The Ncurses package contains libraries for terminal-independent handling of
character screens.

%prep
%setup -q -n ncurses-%{version}-20250809

# Avoid an unnecessary libtool install helper in the C++ makefile.
sed -i '/LIBTOOL_INSTALL/d' c++/Makefile.in || :

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
CONFIG_HOST=--host=i686-pc-linux-gnu
%else
CONFIG_HOST=""
%endif

./configure \
    --prefix=%{_prefix} \
    --libdir=%{ncurses_multilibdir} \
    --mandir=%{_mandir} \
    --with-shared \
    --without-debug \
    --without-normal \
    --with-cxx-shared \
    --enable-pc-files \
    --enable-widec \
    --with-pkg-config-libdir=%{ncurses_multilibdir}/pkgconfig \
    ${CONFIG_HOST}

make %{?_smp_mflags}

%check
# The Ncurses test suite expects the package to be installed system-wide.
# Tests can be run manually from the test/ directory if desired.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
make DESTDIR=%{buildroot} install

# Edit curses.h so that the wide-character ABI is always used.
sed -e 's/^#if.*XOPEN.*$/#if 1/' \
    -i %{buildroot}/usr/include/curses.h || :

%if "%{_target_cpu}" == "i686"
# i686: provide INPUT() stubs and pkg-config links under the 32-bit libdir and prune other content.
mkdir -pv %{buildroot}/usr/lib/i386-linux-gnu/pkgconfig
for lib in ncurses form panel menu ; do
    rm -vf %{buildroot}/usr/lib/i386-linux-gnu/lib${lib}.so || :
    echo "INPUT(-l${lib}w)" > %{buildroot}/usr/lib/i386-linux-gnu/lib${lib}.so
    ln -svf ${lib}w.pc %{buildroot}/usr/lib/i386-linux-gnu/pkgconfig/${lib}.pc
done
rm -vf %{buildroot}/usr/lib/i386-linux-gnu/libcursesw.so || :
echo "INPUT(-lncursesw)" > %{buildroot}/usr/lib/i386-linux-gnu/libcursesw.so
ln -sfv libncurses.so %{buildroot}/usr/lib/i386-linux-gnu/libcurses.so

# Prune non-library content for 32-bit package
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}/usr/lib/terminfo || :
rm -rf %{buildroot}/usr/share/terminfo || :
%else
# x86_64: Provide non-wide-character compatibility symlinks using the wide libraries and pkgconfig alias
mkdir -pv %{buildroot}/usr/lib/x86_64-linux-gnu
mkdir -pv %{buildroot}/usr/lib/x86_64-linux-gnu/pkgconfig
mkdir -pv %{buildroot}/usr/lib/pkgconfig
for lib in ncurses form panel menu ; do
    ln -sfv lib${lib}w.so %{buildroot}/usr/lib/x86_64-linux-gnu/lib${lib}.so
    ln -sfv ../x86_64-linux-gnu/pkgconfig/${lib}w.pc %{buildroot}/usr/lib/pkgconfig/${lib}.pc
done
ln -sfv libncursesw.so %{buildroot}/usr/lib/x86_64-linux-gnu/libcurses.so

# Install documentation
mkdir -pv %{buildroot}/usr/share/doc/ncurses-%{version}-20250809
cp -v -R doc/* %{buildroot}/usr/share/doc/ncurses-%{version}-20250809
%endif

# Remove legacy /usr/lib/terminfo symlink (terminfo lives in /usr/share/terminfo)
rm -rf %{buildroot}/usr/lib/terminfo || :

# Avoid owning the shared Info directory file to prevent conflicts with glibc
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{ncurses_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/ncurses-files.list
%else
# Runtime: versioned shared libs, terminfo, binaries, man pages, docs
{
  find .%{ncurses_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
  if [ -d ./usr/share/tabset ]; then
    find ./usr/share/tabset -type f -o -type l
  fi
  if [ -d ./usr/share/terminfo ]; then
    find ./usr/share/terminfo -type f -o -type l
  fi
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/ncurses-runtime.list

%if %{ncurses_enable_devel}
# Development: headers, pkgconfig, INPUT() stubs, unversioned .so symlinks
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{ncurses_multilibdir} -maxdepth 1 \( -type f -o -type l \) ! -name '*.so.*'
  if [ -d .%{ncurses_multilibdir}/pkgconfig ]; then
    find .%{ncurses_multilibdir}/pkgconfig -type f -o -type l
  fi
  if [ -d ./usr/lib/pkgconfig ]; then
    find ./usr/lib/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/ncurses-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/ncurses-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/ncurses-runtime.list
%defattr(-,root,root,-)

%if %{ncurses_enable_devel}
%files devel -f %{_builddir}/ncurses-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 6.5-1.m264
- Ncurses initial RPM packaging.
