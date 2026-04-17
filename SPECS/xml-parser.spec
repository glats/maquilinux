Name:           xml-parser
Version:        2.47
Release:        1.m264%{?dist}
Summary:        Perl interface to the Expat XML parser

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        Artistic 1.0 or GPLv1+
URL:            https://metacpan.org/release/XML-Parser
Source0:        https://www.cpan.org/authors/id/T/TO/TODDR/XML-Parser-%{version}.tar.gz

BuildRequires:  perl
BuildRequires:  expat-devel

%description
XML::Parser is a Perl module providing an interface to the Expat XML parser,
enabling Perl scripts to process XML content efficiently.

%prep
%setup -q -n XML-Parser-%{version}

%build
%if "%{_target_cpu}" == "i686"
EXPAT_LIBDIR=/usr/lib/i386-linux-gnu
%else
EXPAT_LIBDIR=/usr/lib/x86_64-linux-gnu
%endif

perl Makefile.PL \
    EXPATLIBPATH=${EXPAT_LIBDIR} \
    EXPATINCPATH=/usr/include
make %{?_smp_mflags}

%check
make test || :

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . -type f -o -type l | sed 's|^\.||' > %{_builddir}/xml-parser-files.list

%files -f %{_builddir}/xml-parser-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 2.47-1.m264
- Initial packaging aligned with MLFS 8.46 instructions.
