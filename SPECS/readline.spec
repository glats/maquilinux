%define readline_version 8.3

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

%if "%{_target_cpu}" == "i686"
%global readline_multilibdir /usr/lib/i386-linux-gnu
%global readline_enable_devel 0
%else
%global readline_multilibdir /usr/lib/x86_64-linux-gnu
%global readline_enable_devel 1
%endif

Name:           readline
Version:        %{readline_version}
Release:        1.m264%{?dist}
Summary:        GNU readline library for command-line editing

%if "%{_target_cpu}" == "x86_64"
Provides:       libreadline.so.8()(64bit)
Provides:       libhistory.so.8()(64bit)
%endif

License:        GPLv3+
URL:            https://tiswww.case.edu/php/chet/readline/rltop.html
Source0:        https://ftp.gnu.org/gnu/readline/readline-%{version}.tar.gz

%if %{readline_enable_devel}
%package devel
Summary:        Development files for readline
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, pkg-config metadata, and the unversioned shared library symlinks
for developing against GNU readline.
%endif

%description
The GNU Readline library provides a set of functions for use by applications
that allow users to edit typed command lines with emacs or vi-like key
bindings, and to recall previously typed commands.

%prep
%setup -q -n readline-%{version}

# Follow MLFS instructions to avoid ldconfig bug and unwanted rpath,
# and to apply the upstream input.c fix for this version.
sed -i '/MV.*old/d' Makefile.in
sed -i '/{OLDSUFF}/c:' support/shlib-install
sed -i 's/-Wl,-rpath,[^ ]*//' support/shobj-conf
sed -e '270a\
     else\
       chars_avail = 1;'      \
    -e '288i\   result = -1;' \
    -i.orig input.c

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
    --libdir=%{readline_multilibdir} \
    --disable-static \
    --with-curses \
    --docdir=%{_datadir}/doc/readline-%{version} \
    ${CONFIG_HOST}

make SHLIB_LIBS="-lncursesw" %{?_smp_mflags}

%check
# No upstream test suite is provided for readline; nothing to run here.

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
%endif

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}

%if "%{_target_cpu}" == "i686"
{
  find .%{readline_multilibdir} -type f -o -type l
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/readline-files.list
%else
# Runtime: versioned shared libs, man pages, docs
{
  find .%{readline_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so.*'
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
  if [ -d ./usr/share/info ]; then
    find ./usr/share/info -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/readline-runtime.list

%if %{readline_enable_devel}
# Development: headers, unversioned .so symlinks
{
  if [ -d ./usr/include ]; then
    find ./usr/include -type f -o -type l
  fi
  find .%{readline_multilibdir} -maxdepth 1 \( -type f -o -type l \) -name '*.so' ! -name '*.so.*'
  if [ -d .%{readline_multilibdir}/pkgconfig ]; then
    find .%{readline_multilibdir}/pkgconfig -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/readline-devel.list
%endif
%endif

%if "%{_target_cpu}" == "i686"
%files -f %{_builddir}/readline-files.list
%defattr(-,root,root,-)
%else
%files -f %{_builddir}/readline-runtime.list
%defattr(-,root,root,-)

%if %{readline_enable_devel}
%files devel -f %{_builddir}/readline-devel.list
%defattr(-,root,root,-)
%endif
%endif

%post
%{_sbindir}/ldconfig

%postun
%{_sbindir}/ldconfig

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 8.3-1.m264
- Readline initial RPM packaging.
