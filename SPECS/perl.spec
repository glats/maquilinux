Name:           perl
Version:        5.42.0
Release:        1.m264%{?dist}
Summary:        Practical Extraction and Report Language

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        Artistic 1.0 or GPLv1+
URL:            https://www.perl.org/
Source0:        https://www.cpan.org/src/5.0/perl-%{version}.tar.xz

%if "%{_target_cpu}" != "i686"
Provides:       perl-devel = %{version}-%{release}
%endif

%description
Perl is a high-level programming language capable of processing text, system
administration tasks, and many other functions, combining the best features of
C, sed, awk, and shell scripting.

%prep
%setup -q -n perl-%{version}

%build
export BUILD_ZLIB=False
export BUILD_BZIP2=0

sh Configure -des \
    -D prefix=%{_prefix} \
    -D vendorprefix=%{_prefix} \
    -D privlib=/usr/lib/perl5/5.42/core_perl \
    -D archlib=/usr/lib/perl5/5.42/core_perl \
    -D sitelib=/usr/lib/perl5/5.42/site_perl \
    -D sitearch=/usr/lib/perl5/5.42/site_perl \
    -D vendorlib=/usr/lib/perl5/5.42/vendor_perl \
    -D vendorarch=/usr/lib/perl5/5.42/vendor_perl \
    -D man1dir=/usr/share/man/man1 \
    -D man3dir=/usr/share/man/man3 \
    -D pager="/usr/bin/less -isR" \
    -D useshrplib \
    -D usethreads

make %{?_smp_mflags}

%check
TEST_JOBS=%{?_smp_build_ncpus} make test_harness || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
unset BUILD_ZLIB BUILD_BZIP2
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/perl-files.list

%files -f %{_builddir}/perl-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 5.42.0-1.m264
- Initial packaging aligned with MLFS 8.45 instructions.
