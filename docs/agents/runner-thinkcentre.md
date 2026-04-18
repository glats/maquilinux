# CI/CD Self-Hosted Runner

**Host:** `thinkcentre.local` (172.16.0.11)  
**Runner Name:** `thinkcentre-builder`  
**Labels:** `self-hosted, Linux, X64, maquilinux`

## Quick Status

```bash
# Check runner status
gh api repos/glats/maquilinux/actions/runners | \
  jq -r '.runners[] | "\(.name): \(.status) (\(.labels | map(.name) | join(", ")))"'
```

## Restart Runner

```bash
ssh thinkcentre.local "tmux kill-session -t github-runner; \
  sleep 1; \
  tmux new-session -d -s github-runner \"\\\"bash -c 'export LD_LIBRARY_PATH=\$(nix eval --raw nixpkgs#stdenv.cc.cc.lib)/lib:\$(nix eval --raw nixpkgs#zlib)/lib:\$(nix eval --raw nixpkgs#icu)/lib; cd ~ && ./bin/Runner.Listener run'\\\"\""
```

## View Logs

```bash
ssh thinkcentre.local "tmux capture-pane -t github-runner -p | tail -30"
```

## Re-register (Session Conflict)

```bash
# 1. Delete from GitHub
RUNNER_ID=$(gh api repos/glats/maquilinux/actions/runners | jq -r '.runners[] | select(.name == "thinkcentre-builder") | .id')
gh api repos/glats/maquilinux/actions/runners/$RUNNER_ID --method DELETE

# 2. Clean local
ssh thinkcentre.local "tmux kill-session -t github-runner; \
  pkill -9 -f Runner.Listener; \
  rm -rf ~/.credentials* ~/.runner ~/.credentials_rsaparams _diag _work .env"

# 3. New token
TOKEN=$(gh api repos/glats/maquilinux/actions/runners/registration-token --method POST | jq -r '.token')

# 4. Configure
ssh thinkcentre.local "cd ~ && nix shell nixpkgs#stdenv.cc.cc.lib \
  nixpkgs#zlib nixpkgs#openssl nixpkgs#icu nixpkgs#bash --command bash -c \
  'export LD_LIBRARY_PATH=\$(nix eval --raw nixpkgs#stdenv.cc.cc.lib)/lib:\
\$(nix eval --raw nixpkgs#zlib)/lib:\$(nix eval --raw nixpkgs#icu)/lib; \
  ./bin/Runner.Listener configure --url https://github.com/glats/maquilinux \
  --token $TOKEN --name thinkcentre-builder --work _work --unattended \
  --labels maquilinux'"
```

## Key Workflows

| Workflow | Trigger | Duration | Purpose |
|----------|---------|----------|---------|
| `build.yml` | Push to SPECS/ | 5-30 min | Build changed RPMs |
| `bootstrap-rust.yml` | Push to rust specs | 2-6 hours | Bootstrap Rust + Sequoia |

## Troubleshooting

**Session conflict error:**
- Wait 30 min for session to expire, or
- Re-register runner (see above)

**Runner shows offline:**
- Check tmux session is running
- Verify network connectivity from thinkcentre
- Re-register if needed

**GLIBC errors in runner:**
- NixOS requires LD_LIBRARY_PATH with gcc, zlib, icu
- Use nix shell wrapper before starting runner
