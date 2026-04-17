%define pcre2_version 10.47

%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}

Name:           pcre2
Version:        %{pcre2_version}
Release:        1.m264%{?dist}
Summary:        Perl-compatible regular expression library (PCRE2)

%if "%{_target_cpu}" == "x86_64"
Provides:       libpcre2-8.so.0()(64bit)
Provides:       libpcre2-16.so.0()(64bit)
Provides:       libpcre2-32.so.0()(64bit)
Provides:       libpcre2-posix.so.3()(64bit)
%endif

License:        BSD
URL:            https://www.pcre.org/
Source0:        pcre2-%{version}.tar.bz2

%description
The PCRE2 library is a reimplementation of the Perl Compatible Regular
Expressions (PCRE) library, which implements regular expression pattern
matching using the same syntax and semantics as Perl 5. This package
installs the shared PCRE2 libraries and associated tools in a multiarch
layout.

%prep
%setup -q -n pcre2-%{version}

%build
%if "%{_target_cpu}" == "i686"
CPPFLAGS="${CPPFLAGS:-} -I/usr/include"
LDFLAGS="${LDFLAGS:-} -L/usr/lib/i386-linux-gnu"
export CPPFLAGS LDFLAGS
CC="gcc -m32" CXX="g++ -m32" \
./configure \
    --prefix=%{_prefix} \
    --docdir=%{_datadir}/doc/pcre2-%{version} \
    --libdir=/usr/lib/i386-linux-gnu \
    --host=i686-pc-linux-gnu \
    --enable-unicode \
    --enable-jit \
    --enable-pcre2-16 \
    --enable-pcre2-32 \
    --disable-pcre2grep-libz \
    --disable-pcre2grep-libbz2 \
    --disable-pcre2test-libreadline \
    --disable-static
%else
CPPFLAGS="${CPPFLAGS:-} -I/usr/include"
LDFLAGS="${LDFLAGS:-} -L/usr/lib/x86_64-linux-gnu"
export CPPFLAGS LDFLAGS

PCRE2_LIBZ_OPT="--disable-pcre2grep-libz"
PCRE2_LIBBZ2_OPT="--disable-pcre2grep-libbz2"
PCRE2_READLINE_OPT="--disable-pcre2test-libreadline"

if [ -f /usr/include/zlib.h ]; then
  PCRE2_LIBZ_OPT="--enable-pcre2grep-libz"
fi

if [ -f /usr/include/bzlib.h ]; then
  PCRE2_LIBBZ2_OPT="--enable-pcre2grep-libbz2"
fi

if [ -f /usr/include/readline/readline.h ] && [ -f /usr/include/readline/history.h ]; then
  PCRE2_READLINE_OPT="--enable-pcre2test-libreadline"
fi

./configure \
    --prefix=%{_prefix} \
    --docdir=%{_datadir}/doc/pcre2-%{version} \
    --libdir=/usr/lib/x86_64-linux-gnu \
    --enable-unicode \
    --enable-jit \
    --enable-pcre2-16 \
    --enable-pcre2-32 \
    ${PCRE2_LIBZ_OPT} \
    ${PCRE2_LIBBZ2_OPT} \
    ${PCRE2_READLINE_OPT} \
    --disable-static
%endif

make %{?_smp_mflags}

%check
# Upstream tests; run only for the 64-bit build tree
make check || :

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install

# Remove static libraries we do not want to ship and prune i686 to libs-only
%if "%{_target_cpu}" == "i686"
rm -rf %{buildroot}%{_bindir} || :
rm -rf %{buildroot}%{_sbindir} || :
rm -rf %{buildroot}%{_mandir} || :
rm -rf %{buildroot}%{_datadir} || :
rm -rf %{buildroot}%{_includedir} || :
rm -fv %{buildroot}/usr/lib/i386-linux-gnu/libpcre2-*.a || :
%else
rm -fv %{buildroot}/usr/lib/x86_64-linux-gnu/libpcre2-*.a || :
%endif

%if "%{_target_cpu}" == "i686"
cd %{buildroot}
{
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu -type f -o -type l | sed 's|^\.||'
  fi
} > %{_builddir}/pcre2-files.list
%else
cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/pcre2-files.list
%endif

%files -f %{_builddir}/pcre2-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 10.47-1.m264
- Initial RPM packaging for pcre2 with multiarch layout.
