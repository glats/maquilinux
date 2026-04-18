# CI/CD Self-Hosted Runner

**Host:** `thinkcentre.local` (172.16.0.11)  
**Runner Name:** `thinkcentre-builder`  
**Labels:** `self-hosted, Linux, X64, maquilinux`  
**Repository:** `glats/maquilinux`

---

## Quick Status

```bash
# Check GitHub runner status
gh api repos/glats/maquilinux/actions/runners | \
  jq -r '.runners[] | "\(.name): \(.status) (\(.labels | map(.name) | join(", ")))"'

# Check if runner process is running on host
ssh thinkcentre.local "ps aux | grep Runner.Listener | grep -v grep"

# View tmux session
tmux capture-pane -t github-runner -p | tail -20
```

---

## Two Ways to Run the Runner

### Option A: NixOS Way (Recommended)

**Requirements:** NixOS or Nix package manager installed

**Benefits:**
- No manual library management
- All dependencies via `flake.nix`
- Reproducible environment
- One command to start

**Start Runner:**

```bash
# Via SSH (one-liner)
ssh thinkcentre.local "cd ~/Work/maquilinux && \
  tmux kill-session -t github-runner 2>/dev/null; \
  sleep 1; \
  tmux new-session -d -s github-runner 'nix run .#runner'"

# Or manually on host
cd ~/Work/maquilinux
nix run .#runner
```

**Check Environment:**

```bash
nix run .#runner-status
```

**Configure (first time or re-register):**

```bash
# Get token from GitHub
TOKEN=$(gh api repos/glats/maquilinux/actions/runners/registration-token \
  --method POST | jq -r '.token')

# Configure via nix develop
ssh thinkcentre.local "cd ~/Work/maquilinux && \
  nix develop -c bash -c './bin/Runner.Listener configure \
    --url https://github.com/glats/maquilinux \
    --token $TOKEN --name thinkcentre-builder --work _work --unattended \
    --labels maquilinux'"
```

---

### Option B: Standalone Way (Any Linux)

**Requirements:** Standard Linux (Debian, Ubuntu, Fedora, etc.)

**Prerequisites:**
- GitHub Actions runner binary (`actions-runner-linux-x64-*.tar.gz`)
- Required libraries: `libstdc++6`, `zlib1g`, `libicu*`, `libssl`

**Install Dependencies:**

```bash
# Debian/Ubuntu
sudo apt-get install libstdc++6 zlib1g libicu-dev libssl3

# Fedora/RHEL
sudo dnf install libstdc++ zlib libicu openssl-libs

# Arch
sudo pacman -S libstdc++5 zlib icu openssl
```

**Setup Runner:**

```bash
# 1. Download runner (one time)
cd ~
curl -o actions-runner-linux-x64-2.323.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.323.0/actions-runner-linux-x64-2.323.0.tar.gz
tar xzf actions-runner-linux-x64-2.323.0.tar.gz

# 2. Get token from GitHub (on your local machine)
gh api repos/glats/maquilinux/actions/runners/registration-token \
  --method POST | jq -r '.token'

# 3. Configure on the host
./bin/Runner.Listener configure \
  --url https://github.com/glats/maquilinux \
  --token <TOKEN_FROM_STEP_2> \
  --name thinkcentre-builder \
  --work _work \
  --unattended \
  --labels maquilinux
```

**Start Runner:**

```bash
# Simple (foreground)
./bin/Runner.Listener run

# Via tmux (background, recommended)
tmux kill-session -t github-runner 2>/dev/null
tmux new-session -d -s github-runner './bin/Runner.Listener run'

# Check if running
tmux capture-pane -t github-runner -p | tail -10
```

---

## Common Operations (Both Ways)

### View Logs

```bash
ssh thinkcentre.local "tmux capture-pane -t github-runner -p | tail -30"
```

### Restart Runner

**NixOS:**
```bash
ssh thinkcentre.local "cd ~/Work/maquilinux && \
  tmux kill-session -t github-runner 2>/dev/null; sleep 1; \
  tmux new-session -d -s github-runner 'nix run .#runner'"
```

**Standalone:**
```bash
ssh thinkcentre.local "tmux kill-session -t github-runner 2>/dev/null; sleep 1; \
  tmux new-session -d -s github-runner '/home/glats/bin/Runner.Listener run'"
```

### Re-register After Session Conflict

**For both approaches:**

```bash
# 1. Delete from GitHub
RUNNER_ID=$(gh api repos/glats/maquilinux/actions/runners | \
  jq -r '.runners[] | select(.name == "thinkcentre-builder") | .id')
gh api repos/glats/maquilinux/actions/runners/$RUNNER_ID --method DELETE

# 2. Clean local
tmux kill-session -t github-runner 2>/dev/null
pkill -9 -f Runner.Listener 2>/dev/null
rm -rf ~/.credentials* ~/.runner ~/.credentials_rsaparams _diag _work .env

# 3. Get new token
TOKEN=$(gh api repos/glats/maquilinux/actions/runners/registration-token \
  --method POST | jq -r '.token')

# 4. Reconfigure
# NixOS way:
ssh thinkcentre.local "cd ~/Work/maquilinux && \
  nix develop -c bash -c './bin/Runner.Listener configure \
    --url https://github.com/glats/maquilinux --token $TOKEN \
    --name thinkcentre-builder --work _work --unattended --labels maquilinux'"

# Standalone way:
ssh thinkcentre.local "cd ~ && ./bin/Runner.Listener configure \
  --url https://github.com/glats/maquilinux --token $TOKEN \
  --name thinkcentre-builder --work _work --unattended --labels maquilinux"

# 5. Start runner (use method A or B above)
```

---

## Key Workflows

| Workflow | Trigger | Duration | Purpose |
|----------|---------|----------|---------|
| `build.yml` | Push to SPECS/ | 5-30 min | Build changed RPMs |
| `bootstrap-rust.yml` | Push to rust specs | 2-6 hours | Bootstrap Rust + Sequoia |

### Workflow Labels

The runner uses label `maquilinux` (in addition to default `self-hosted, Linux, X64`).

Workflows that need this runner must include:
```yaml
jobs:
  build:
    runs-on: [self-hosted, maquilinux]
```

---

## Troubleshooting

### Runner Shows Offline

1. Check tmux session: `tmux ls`
2. Check process: `ps aux | grep Runner`
3. Try restart (see above)
4. If still offline, re-register (see above)

### Session Conflict Error

Error: `A session for this runner already exists`

- Wait 30 minutes for GitHub to expire the session, OR
- Re-register immediately (see "Re-register" above)

### Library Errors (Standalone Only)

**Error:** `libstdc++.so.6: version 'GLIBCXX_3.4.32' not found`

Solution: Install/upgrade libstdc++6:
```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install libstdc++6

# Or newer GCC
sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt-get install gcc-13 g++-13
```

**Error:** `libicu*.so not found`

Solution: Install ICU libraries:
```bash
# Debian/Ubuntu
sudo apt-get install libicu-dev

# Fedora
sudo dnf install libicu
```

### GitHub API Rate Limits

If you see `403 rate limit exceeded` when checking runner status:

```bash
# Use authenticated requests
gh api repos/glats/maquilinux/actions/runners

# Instead of unauthenticated:
curl https://api.github.com/repos/glats/maquilinux/actions/runners
```

---

## Directory Structure on Host

```
~/                          # Runner runs from home
├── bin/Runner.Listener     # Main runner binary
├── _work/                  # Job working directory
├── _diag/                  # Runner diagnostic logs
├── .credentials            # GitHub credentials
├── .runner                 # Runner configuration
└── Work/maquilinux/        # Git repo (cloned)
    ├── .github/workflows/  # Workflow definitions
    ├── SPECS/              # RPM specs
    └── ...
```

---

## Security Notes

1. **Token expiration:** Runner registration tokens expire after 1 hour
2. **Credentials:** `.credentials*` files contain sensitive data - never commit
3. **SSH access:** The host (`thinkcentre.local`) must be reachable via SSH
4. **Network:** Runner needs outbound HTTPS to GitHub (github.com, *.actions.githubusercontent.com)
