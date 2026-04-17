%define glib2_version 2.86.3

# Built inside an LFS-style chroot with no debuginfo helpers available.
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global glib2_multilibdir /usr/lib/i386-linux-gnu
%global glib2_lib_subdir lib/i386-linux-gnu
%global glib2_enable_devel 0
%else
%global glib2_multilibdir /usr/lib/x86_64-linux-gnu
%global glib2_lib_subdir lib/x86_64-linux-gnu
%global glib2_enable_devel 1
%endif

Name:           glib2
Version:        %{glib2_version}
Release:        1.m264%{?dist}
Summary:        Core application library for C

%if "%{_target_cpu}" == "x86_64"
Provides:       libglib-2.0.so.0()(64bit)
Provides:       libgobject-2.0.so.0()(64bit)
Provides:       libgio-2.0.so.0()(64bit)
Provides:       libgmodule-2.0.so.0()(64bit)
Provides:       libgthread-2.0.so.0()(64bit)
%endif

License:        LGPL-2.1-or-later
URL:            https://gitlab.gnome.org/GNOME/glib
Source0:        https://download.gnome.org/sources/glib/2.86/glib-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  python3
BuildRequires:  meson
BuildRequires:  ninja
BuildRequires:  pkgconf

BuildRequires:  libffi
BuildRequires:  pcre2
BuildRequires:  zlib

%description
GLib provides the core application building blocks for libraries and applications
written in C. It provides data structures, portability wrappers, an event loop,
threading primitives, and other fundamental utilities.

%if %{glib2_enable_devel}
%package devel
Summary:        Development files for GLib
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlinks
for developing against GLib.
%endif

%prep
%setup -q -n glib-%{version}

%build
%if "%{_target_cpu}" == "i686"
export CC="gcc -m32"
export CXX="g++ -m32"
export PKG_CONFIG_LIBDIR="/usr/lib/i386-linux-gnu/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig"

# Create a meson cross-file for i686 to ensure correct library paths
cat > i686-cross.txt << 'CROSSEOF'
[binaries]
c = ['gcc', '-m32']
cpp = ['g++', '-m32']
ar = 'ar'
strip = 'strip'
pkg-config = 'pkg-config'

[built-in options]
c_args = ['-m32']
c_link_args = ['-m32', '-L/usr/lib/i386-linux-gnu']
cpp_args = ['-m32']
cpp_link_args = ['-m32', '-L/usr/lib/i386-linux-gnu']
pkg_config_path = '/usr/lib/i386-linux-gnu/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig'

[host_machine]
system = 'linux'
cpu_family = 'x86'
cpu = 'i686'
endian = 'little'
CROSSEOF

CROSS_FILE="--cross-file i686-cross.txt"
%else
export PKG_CONFIG_LIBDIR="/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/lib/pkgconfig:/usr/share/pkgconfig"
CROSS_FILE=""
%endif

meson setup build \
    ${CROSS_FILE} \
    --wrap-mode=nodownload \
    --prefix=%{_prefix} \
    --libdir=%{glib2_lib_subdir} \
    --buildtype=release \
    -Ddefault_library=shared \
    -Dtests=false \
    -Dinstalled_tests=false \
    -Dnls=disabled \
    -Dintrospection=disabled \
    -Dman-pages=disabled \
    -Ddocumentation=false \
    -Dselinux=disabled \
    -Dlibmount=disabled \
    -Ddtrace=disabled \
    -Dsystemtap=disabled \
    -Dsysprof=disabled \
    -Dlibelf=disabled

meson compile -C build

%check
:

%install
rm -rf %{buildroot}
meson install -C build --destdir %{buildroot}

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}/usr/libexec || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  if [ -d .%{glib2_multilibdir} ]; then
    find .%{glib2_multilibdir} -type f -o -type l
  fi
} | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/glib2-files.list

test -s %{_builddir}/glib2-files.list
%else
find . \( -type f -o -type l \) | sed 's|^\.||' | LC_ALL=C sort > %{_builddir}/glib2-all.list

test -s %{_builddir}/glib2-all.list

%if %{glib2_enable_devel}
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  if [ -d .%{glib2_multilibdir} ]; then
    if [ -d .%{glib2_multilibdir}/pkgconfig ]; then
      find .%{glib2_multilibdir}/pkgconfig -type f -o -type l
    fi
    if [ -d .%{glib2_multilibdir}/glib-2.0/include ]; then
      find .%{glib2_multilibdir}/glib-2.0/include -type f -o -type l
    fi
    find .%{glib2_multilibdir} -maxdepth 1 -type f -name 'lib*.so'
    find .%{glib2_multilibdir} -maxdepth 1 -type l -name 'lib*.so'
  fi
  if [ -d ./usr/share/aclocal ]; then
    find ./usr/share/aclocal -type f -o -type l
  fi
} | sed 's|^\.||' | LC_ALL=C sort -u > %{_builddir}/glib2-devel.list

test -s %{_builddir}/glib2-devel.list

grep -F -x -v -f %{_builddir}/glib2-devel.list %{_builddir}/glib2-all.list > %{_builddir}/glib2-runtime.list

test -s %{_builddir}/glib2-runtime.list
%else
cp %{_builddir}/glib2-all.list %{_builddir}/glib2-runtime.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/glib2-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/glib2-runtime.list
%defattr(-,root,root,-)

%if %{glib2_enable_devel}
%files devel -f %{_builddir}/glib2-devel.list
%defattr(-,root,root,-)
%endif
%endif

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.86.3-1.m264
- Initial GLib (glib2) packaging with runtime and -devel split.
