{
  description = "Maqui Linux - Development Environment with Runner Support";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      
      # Libraries needed for GitHub Actions runner (.NET Core)
      runnerLibs = with pkgs; [
        stdenv.cc.cc.lib    # libstdc++.so.6
        zlib                # libz.so.1
        icu                 # libicu*.so (i18n, uc, data)
        openssl             # libssl.so, libcrypto.so
      ];
      
      # Build LD_LIBRARY_PATH from runner libs
      runnerLibPath = pkgs.lib.makeLibraryPath runnerLibs;
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
            git
            jq
            gh

            # RPM tools (host side - for querying)
            rpm

            # Repository management
            createrepo_c

            # ISO generation
            libisoburn      # xorriso
            squashfsTools   # mksquashfs
            mtools

            # Testing
            qemu

            # Utilities
            file
            tree
            curl
            wget
            
            # Runner support libraries (in dev shell for testing)
            stdenv.cc.cc.lib
            zlib
            icu
            openssl
          ];

          shellHook = ''
            # Add mql to PATH
            export PATH="$PWD:$PATH"
            export MQL_PROJECT_ROOT="$PWD"

            # Set LD_LIBRARY_PATH for runner compatibility
            # This makes .NET Core (GitHub Actions runner) work without hardcoded paths
            export LD_LIBRARY_PATH="${runnerLibPath}:$LD_LIBRARY_PATH"

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
            echo "  LD_LIBRARY_PATH  = (set for runner support)"
            echo ""
            echo "Commands:"
            echo "  ./mql help                    Show all commands"
            echo "  ./mql status                  Check environment"
            echo "  ./mql chroot                  Enter Maqui Linux chroot"
            echo ""
            echo "Runner (in nix develop):"
            echo "  nix run .#runner              Start GitHub Actions runner"
            echo "  nix run .#runner-status       Check runner status"
            echo ""
            echo "Build flow:"
            echo "  sudo ./scripts/enter-chroot-build.sh -c 'cd /workspace && rpmbuild -ba SPECS/<pkg>.spec --define '_topdir /workspace''"
            echo ""
            echo "=========================================="
          '';
        };
        
      # GitHub Actions runner with proper library environment
      apps.x86_64-linux.runner = {
        type = "app";
        program = toString (pkgs.writeShellScriptBin "runner-start" ''
          export LD_LIBRARY_PATH="${runnerLibPath}"
          
          if [[ ! -f ~/bin/Runner.Listener ]]; then
            echo "ERROR: Runner not found at ~/bin/Runner.Listener"
            echo "Please download and configure the runner first:"
            echo "  cd ~"
            echo "  curl -o actions-runner-linux-x64-2.323.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.323.0/actions-runner-linux-x64-2.323.0.tar.gz"
            echo "  tar xzf actions-runner-linux-x64-2.323.0.tar.gz"
            exit 1
          fi
          
          cd ~
          exec ./bin/Runner.Listener run "$@"
        '').binPath;
      };
      
      # Check runner status
      apps.x86_64-linux.runner-status = {
        type = "app";
        program = toString (pkgs.writeShellScriptBin "runner-status" ''
          echo "Runner Library Environment:"
          echo "  LD_LIBRARY_PATH=${runnerLibPath}"
          echo ""
          echo "Checking libraries:"
          for lib in libstdc++ z libicu libssl; do
            found=$(ldconfig -p 2>/dev/null | grep -c "$lib" || echo "0")
            if [[ "$found" -gt 0 ]]; then
              echo "  ✓ $lib: found"
            else
              echo "  ✗ $lib: NOT FOUND"
            fi
          done
          echo ""
          echo "Runner process:"
          ps aux | grep -i "Runner.Listener" | grep -v grep || echo "  (not running)"
        '').binPath;
      };
    };
}
