Name:           vim
Version:        9.1.1934
Release:        1.m264%{?dist}
Summary:        Vi IMproved text editor

%define debug_package        %{nil}
%define __debug_install_post %{nil}
%define __os_install_post    %{nil}

License:        Vim
URL:            https://www.vim.org
Source0:        https://github.com/vim/vim/archive/v%{version}/vim-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  ncurses-devel
BuildRequires:  perl

%description
Vim is a highly configurable text editor built to enable efficient text
editing, extending the classic vi with modern improvements.

%prep
%autosetup -n vim-%{version}
echo '#define SYS_VIMRC_FILE "/etc/vimrc"' >> src/feature.h

%build
./configure --prefix=%{_prefix}
make %{?_smp_mflags}

%check
# Test suite requires a non-root user and additional tools; skip in chroot.
:

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
make DESTDIR=%{buildroot} install

install -d %{buildroot}/usr/share/doc
ln -sf ../vim/vim91/doc %{buildroot}/usr/share/doc/vim-%{version}

install -d %{buildroot}/etc
cat > %{buildroot}/etc/vimrc <<'EOF'
" Begin /etc/vimrc
source $VIMRUNTIME/defaults.vim
let skip_defaults_vim=1
set nocompatible
set backspace=2
set mouse=
syntax on
if (&term == "xterm") || (&term == "putty")
  set background=dark
endif
" End /etc/vimrc
EOF

ln -sf vim %{buildroot}/usr/bin/vi
for manpage in %{buildroot}/usr/share/man/{,*/}man1/vim.1; do
  if [ -f "$manpage" ]; then
    ln -sf vim.1 "$(dirname "$manpage")"/vi.1
  fi
done

rm -f %{buildroot}/usr/share/info/dir || :

cd %{buildroot}
find . \( -type f -o -type l \) -printf '/%%P\n' > %{builddir}/vim-files.list
test -s %{builddir}/vim-files.list

%files -f %{builddir}/vim-files.list
%defattr(-,root,root)

%changelog
* Tue Dec 23 2025 Juan Cuzmar <juan.cuzmar.s@gmail.com> - 9.1.1934-1.m264
- Initial packaging aligned with MLFS 8.76 instructions (system vimrc, vi symlinks, doc link).
