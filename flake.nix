{
  description = "Maqui Linux - Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.x86_64-linux.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Core utilities
            bash
            coreutils
            util-linux
            gnutar
            rsync
            bc

            # RPM tools (host side - for querying)
            rpm

            # Repository management
            createrepo_c

            # ISO generation (future)
            libisoburn      # xorriso
            squashfsTools   # mksquashfs
            mtools

            # Testing
            qemu

            # Utilities
            file
            tree
            curl
          ];

          shellHook = ''
            # Add mql to PATH
            export PATH="$PWD:$PATH"
            export MQL_PROJECT_ROOT="$PWD"

            # Load config to get defaults
            if [[ -f "$PWD/mql.conf" ]]; then
              source "$PWD/mql.conf"
            fi
            if [[ -f "$PWD/mql.local" ]]; then
              source "$PWD/mql.local"
            fi

            # Auto-detect MQL_LFS if not set
            _detect_lfs() {
              local lfs="''${MQL_LFS:-/run/media/glats/maquilinux}"
              local label="maquilinux"

              if mountpoint -q "$lfs" 2>/dev/null; then
                echo "$lfs"
                return
              fi

              for candidate in \
                "/run/media/$USER/$label" \
                "/run/media/root/$label" \
                "/media/$label"
              do
                if mountpoint -q "$candidate" 2>/dev/null; then
                  echo "$candidate"
                  return
                fi
              done
              echo "$lfs"
            }

            export MQL_LFS="$(_detect_lfs)"
            unset -f _detect_lfs

            echo "=========================================="
            echo "Maqui Linux Development Shell"
            echo "=========================================="
            echo ""
            echo "  MQL_LFS          = $MQL_LFS"
            echo "  MQL_RELEASEVER   = ''${MQL_RELEASEVER:-25.4}"
            echo ""
            echo "Commands:"
            echo "  ./mql help       Show all commands"
            echo "  ./mql status     Check environment"
            echo "  ./mql chroot     Enter Maqui Linux chroot"
            echo ""
            echo "Build flow:"
            echo "  sudo ./scripts/enter-chroot-build.sh -c 'cd /workspace && rpmbuild -ba SPECS/<pkg>.spec --define '_topdir /workspace''"
            echo ""
            echo "Update repo:"
            echo "  createrepo_c --update RPMS/x86_64"
            echo "=========================================="
          '';
        };
    };
}
