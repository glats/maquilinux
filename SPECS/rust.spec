%define pkg_version 1.84.0

# Disable debuginfo in bootstrap/minimal chroot
%global debug_package %{nil}
%global _enable_debug_packages 0
%global __debug_install_post %{nil}
%global __os_install_post %{nil}
%global _unpackaged_files_terminate_build 0

# Multiarch configuration
%if "%{_target_cpu}" == "i686"
%global pkg_multilibdir /usr/lib/i386-linux-gnu
%global pkg_enable_devel 0
%else
%global pkg_multilibdir /usr/lib/x86_64-linux-gnu
%global pkg_enable_devel 1
%endif

Name:           rust
Version:        %{pkg_version}
Release:        1.m264%{?dist}
Summary:        Rust compiler and standard library (self-hosted bootstrap)

License:        MIT OR Apache-2.0
URL:            https://rust-lang.org
Source0:        https://static.rust-lang.org/dist/rustc-%{version}-src.tar.xz
Source1:        https://static.rust-lang.org/dist/rust-1.83.0-x86_64-unknown-linux-gnu.tar.xz

# SHA256 checksums (verified in %%prep)
%define sha256_src bc2c1639f26814c7b17a323992f1e08c3b01fe88cdff9a27d951987d886e00b3
%define sha256_stage0 b6467a0e8a6c5dca35269785c994e4d80d89754d6c600162cc9146f90c87ee08

# Stage0 binary is x86_64 only; i686 builds will cross-compile using stage0 from x86_64
ExclusiveArch: x86_64 i686

# Bootstrap requires stage0 binaries
BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  cmake
BuildRequires:  ninja
BuildRequires:  python3
BuildRequires:  curl-devel
BuildRequires:  libssh2-devel
BuildRequires:  openssl-devel
BuildRequires:  zlib-devel
BuildRequires:  llvm-devel
BuildRequires:  libxml2-devel
BuildRequires:  perl

%description
Self-hosted Rust compiler toolchain bootstrapped from stage0.
Provides rustc, cargo, and standard library for x86_64 and i686 multilib.

%package rustc
Summary:        Rust compiler
Requires:       rust-std%{?_isa} = %{version}-%{release}

%description rustc
The Rust compiler (rustc).

%package cargo
Summary:        Rust package manager
Requires:       rustc%{?_isa} = %{version}-%{release}
Requires:       rust-std%{?_isa} = %{version}-%{release}

%description cargo
Cargo is the Rust package manager, used for building Rust crates and managing dependencies.

%package std
Summary:        Rust standard library

%description std
Standard library for Rust.

%package -n rust-toolchain
Summary:        Rust meta package
Requires:       rustc%{?_isa} = %{version}-%{release}
Requires:       cargo%{?_isa} = %{version}-%{release}
Requires:       rust-std%{?_isa} = %{version}-%{release}

%description -n rust-toolchain
Meta package that pulls in the complete Rust toolchain (rustc, cargo, rust-std).

%prep
# Verify checksums before unpacking
echo "%{sha256_src}  %{SOURCE0}" | sha256sum -c -
echo "%{sha256_stage0}  %{SOURCE1}" | sha256sum -c -

# Unpack source
%setup -q -n rustc-%{version}-src
# Unpack stage0 binary into bootstrap directory
mkdir -p bootstrap-stage0
pushd bootstrap-stage0
tar -xf %{SOURCE1}
popd

# Copy std library to rustc sysroot for cargo builds
if [ -d bootstrap-stage0/rust-1.83.0-x86_64-unknown-linux-gnu/rust-std-x86_64-unknown-linux-gnu ]; then
    mkdir -p bootstrap-stage0/rust-1.83.0-x86_64-unknown-linux-gnu/rustc/lib/rustlib/x86_64-unknown-linux-gnu
    cp -r bootstrap-stage0/rust-1.83.0-x86_64-unknown-linux-gnu/rust-std-x86_64-unknown-linux-gnu/lib/rustlib/x86_64-unknown-linux-gnu/lib \
        bootstrap-stage0/rust-1.83.0-x86_64-unknown-linux-gnu/rustc/lib/rustlib/x86_64-unknown-linux-gnu/
fi

# Create unified stage0 directory for --local-rust-root (expects bin/rustc and bin/cargo)
mkdir -p bootstrap-stage0/stage0/bin
ln -sf ../../rust-1.83.0-x86_64-unknown-linux-gnu/rustc/bin/rustc bootstrap-stage0/stage0/bin/rustc
ln -sf ../../rust-1.83.0-x86_64-unknown-linux-gnu/cargo/bin/cargo bootstrap-stage0/stage0/bin/cargo

%build
# Bootstrap: use stage0 binary tarball as seed
export PATH="%{_builddir}/rustc-%{version}-src/bootstrap-stage0/stage0/bin:$PATH"
export RUST_BOOTSTRAP_ROOT="%{_builddir}/rustc-%{version}-src/bootstrap-stage0/stage0"
export RUSTFLAGS="-C linker=gcc"
export CARGO_HOME="%{_builddir}/cargo-home"
export RUSTC_BOOTSTRAP=1
export LD_LIBRARY_PATH="%{_builddir}/rustc-%{version}-src/bootstrap-stage0/rust-1.83.0-x86_64-unknown-linux-gnu/rustc/lib:$LD_LIBRARY_PATH"
export LC_ALL=C
export LANG=C

# Configure build (configure is a bash script, not python)
# Use system LLVM 19 instead of bundled LLVM to avoid GCC 15 compatibility issues
./configure \
    --prefix=%{_prefix} \
    --libdir=%{pkg_multilibdir} \
    --enable-extended \
    --tools=cargo \
    --disable-docs \
    --llvm-root=/usr \
    --enable-llvm-link-shared \
    --disable-lld \
    --local-rust-root=%{_builddir}/rustc-%{version}-src/bootstrap-stage0/stage0

# Build stage1 using stage0
python3 ./x.py build --stage 1 rustc cargo

# Build stage2 using stage1 (self-hosted)
python3 ./x.py build --stage 2 rustc cargo

%install
rm -rf %{buildroot}
DESTDIR=%{buildroot} python3 ./x.py install --stage 2

# Remove static libraries
rm -fv %{buildroot}%{pkg_multilibdir}/*.a || :
rm -fv %{buildroot}%{pkg_multilibdir}/rustlib/*/*/lib/*.a || :

# Generate file lists
cd %{buildroot}
%if "%{_target_cpu}" == "i686"
{
  if [ -d ./usr/lib/i386-linux-gnu ]; then
    find ./usr/lib/i386-linux-gnu -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/rust-files.list
%else
find . \( -type f -o -type l \) | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/rust-all.list

# rustc binary
{
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -name 'rustc'
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/rustc-files.list

# cargo binary
{
  if [ -d ./usr/bin ]; then
    find ./usr/bin -type f -name 'cargo'
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/cargo-files.list

# runtime shared libs (none for rust)
{
  if [ -d ./usr/lib/x86_64-linux-gnu ]; then
    find ./usr/lib/x86_64-linux-gnu -maxdepth 1 \( -type f -o -type l \) -name '*.so'
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/rust-libs.list

# Std library files (rust-std subpackage)
{
  if [ -d ./usr/lib/x86_64-linux-gnu/rustlib ]; then
    find ./usr/lib/x86_64-linux-gnu/rustlib -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/rust-std-files.list

# Documentation and man pages (optional)
{
  if [ -d ./usr/share/doc ]; then
    find ./usr/share/doc -type f -o -type l
  fi
  if [ -d ./usr/share/man ]; then
    find ./usr/share/man -type f -o -type l
  fi
} | sed 's|^\.||' | sed -e 's|//\+|/|g' -e 's|/\+$||' | LC_ALL=C sort -u > %{_builddir}/rust-doc.list
%endif

%check
# Quick smoke test
%{buildroot}/usr/bin/rustc --version | grep %{version}
%{buildroot}/usr/bin/cargo --version | grep cargo

%post
%{_sbindir}/ldconfig || :

%postun
%{_sbindir}/ldconfig || :

%files rustc -f %{_builddir}/rustc-files.list
%defattr(-,root,root)
%{pkg_multilibdir}/librustc_driver*.so

%files cargo -f %{_builddir}/cargo-files.list
%defattr(-,root,root)

%files std -f %{_builddir}/rust-std-files.list
%defattr(-,root,root)

%files -n rust-toolchain
# meta package has no files
%defattr(-,root,root)

%files
# meta package has no files
%defattr(-,root,root)

%changelog
* Fri Apr 18 2026 Maqui Linux <dev@maquilinux.org> - 1.84.0-1.m264
- Updated to Rust 1.84.0
- Use system LLVM 19 instead of bundled LLVM to avoid GCC 15 compatibility issues
- Updated stage0 to Rust 1.83.0

* Fri Apr 18 2026 Maqui Linux <dev@maquilinux.org> - 1.75.0-1.m264
- Unified Rust spec with subpackages rustc, cargo, rust-std, rust-toolchain
- Bootstrap using stage0 binary tarball as Source1
- Self-hosted bootstrap (stage0 → stage1 → stage2)
- Fixed configure script invocation (bash, not python3)
