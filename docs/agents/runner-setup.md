# Self-Hosted GitHub Actions Runner Setup

This guide explains how to set up a self-hosted GitHub Actions runner for building Maqui Linux packages. The runner can be on any Linux machine (your workstation, a dedicated server, a VM, etc.).

---

## Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | x86_64, 4 cores | 8+ cores (for faster builds) |
| RAM | 8 GB | 16+ GB (32 GB for Rust bootstrap) |
| Disk | 100 GB free | 200+ GB (for build artifacts) |
| Network | Outbound HTTPS | Stable connection to GitHub |

### Software Requirements

**Option A: NixOS or Nix package manager (Recommended)**
- Automatic dependency management
- Reproducible environment via `flake.nix`

**Option B: Any Linux Distribution**
- Debian/Ubuntu, Fedora, Arch, etc.
- Manual package installation required

### Required Access

- **GitHub repository access** (`glats/maquilinux` or your fork)
- **Shell access** to the runner host (SSH or local)
- **Root/sudo access** for installing packages and mounting overlays

---

## Configuration

### 1. Set Up Your Build Host

Choose any machine that meets the hardware requirements. Examples:
- Dedicated build server at home/office
- Cloud VM (Hetzner, DigitalOcean, AWS, etc.)
- Your daily workstation
- Old laptop repurposed as build slave

**Configure SSH access (recommended):**

From your development machine:
```bash
# Add to ~/.ssh/config
Host maqui-runner
    HostName <your-runner-ip-or-hostname>
    User <username>
    IdentityFile ~/.ssh/your-key

# Test connection
ssh maqui-runner "echo 'Runner accessible'"
```

### 2. Clone the Repository

On the runner host:

```bash
# Create workspace
mkdir -p ~/Work && cd ~/Work

# Clone Maqui Linux
git clone https://github.com/glats/maquilinux.git
cd maquilinux
```

### 3. Configure `mql.local`

The runner needs to know where the Maqui Linux rootfs disk is mounted.

```bash
# Detect where your disk is mounted
# Common auto-mount locations:
ls /run/media/$USER/       # GNOME/UDisks2
ls /media/                 # Traditional
ls /mnt/                   # Manual mounts

# Create local config
cat > ~/Work/maquilinux/mql.local << 'EOF'
# Path to Maqui Linux disk mount
# Adjust to your actual mount point:
MQL_LFS=/run/media/$USER/maquilinux
# or: MQL_LFS=/media/maquilinux
# or: MQL_LFS=/mnt/maquilinux
EOF
```

**Verify configuration:**
```bash
cd ~/Work/maquilinux
./mql status
# Should show: MQL_LFS=/run/media/.../maquilinux
```

### 4. Set Up Overlay Filesystem

The build system uses an overlay mount for the rootfs:

```bash
# Check current mount
mount | grep maquilinux

# If not mounted, create overlay structure:
sudo mkdir -p /mnt/maquilinux/base /mnt/maquilinux/layers/upper \
  /mnt/maquilinux/layers/work /mnt/maquilinux/merged

# Mount your disk to base (adjust device)
sudo mount /dev/sdX1 /mnt/maquilinux/base

# Mount overlay
sudo mount -t overlay overlay \
  -o lowerdir=/mnt/maquilinux/base,upperdir=/mnt/maquilinux/layers/upper,\
workdir=/mnt/maquilinux/layers/work \
  /mnt/maquilinux/merged

# Update mql.local with correct path
echo 'MQL_LFS=/mnt/maquilinux' >> ~/Work/maquilinux/mql.local
```

---

## Runner Installation

### Option A: NixOS/Nix Way (Recommended)

**Requirements:** NixOS or Nix package manager installed

**Step 1: Enter development shell**

```bash
cd ~/Work/maquilinux
nix develop
```

This provides all needed tools: `gh`, `git`, `createrepo_c`, etc.

**Step 2: Download GitHub Actions runner**

```bash
cd ~
RUNNER_VERSION="2.323.0"
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
  https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/\
actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
tar xzf actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
```

**Step 3: Get registration token**

From any machine with GitHub CLI access:

```bash
# Get token (valid for 1 hour)
gh api repos/glats/maquilinux/actions/runners/registration-token \
  --method POST | jq -r '.token'
# Copy the token (starts with A...)
```

**Step 4: Configure runner**

On the runner host (in nix develop shell):

```bash
cd ~
nix develop ~/Work/maquilinux -c bash -c \
  './bin/Runner.Listener configure \
    --url https://github.com/glats/maquilinux \
    --token <TOKEN_FROM_STEP_3> \
    --name <your-runner-name> \
    --work _work \
    --unattended \
    --labels maquilinux'
```

**Step 5: Start runner**

```bash
# Simple foreground (for testing)
nix run ~/Work/maquilinux#runner

# Or via tmux (recommended for persistence)
tmux new-session -d -s github-runner \
  'nix run ~/Work/maquilinux#runner'

# Check status
nix run ~/Work/maquilinux#runner-status
```

---

### Option B: Standalone Way (Any Linux)

**Step 1: Install dependencies**

Choose your distribution:

**Debian/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install -y \
  git curl jq gh \
  libstdc++6 zlib1g libicu-dev libssl3 \
  createrepo_c squashfs-tools xorriso mtools qemu-system-x86
```

**Fedora/RHEL:**
```bash
sudo dnf install -y \
  git curl jq gh \
  libstdc++ zlib libicu openssl-libs \
  createrepo_c squashfs-tools xorriso mtools qemu-system-x86
```

**Arch Linux:**
```bash
sudo pacman -S --needed \
  git curl jq github-cli \
  libstdc++5 zlib icu openssl \
  createrepo_c squashfs-tools libisoburn mtools qemu-system-x86
```

**Step 2: Download runner**

```bash
cd ~
RUNNER_VERSION="2.323.0"
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
  https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/\
actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
tar xzf actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
```

**Step 3: Get token and configure**

Same as Option A for token. Then configure:

```bash
cd ~
./bin/Runner.Listener configure \
  --url https://github.com/glats/maquilinux \
  --token <TOKEN> \
  --name <your-runner-name> \
  --work _work \
  --unattended \
  --labels maquilinux
```

**Step 4: Start runner**

```bash
# Foreground (testing)
./bin/Runner.Listener run

# Background with tmux
tmux new-session -d -s github-runner './bin/Runner.Listener run'
```

---

## Operations

### Check Runner Status

From GitHub (any machine):
```bash
gh api repos/glats/maquilinux/actions/runners | \
  jq -r '.runners[] | "\(.name): \(.status)"'
```

On the runner host:
```bash
# Check process
ps aux | grep Runner.Listener | grep -v grep

# Check tmux session
tmux ls

# View logs
tmux capture-pane -t github-runner -p | tail -30
```

### Restart Runner

**Nix way:**
```bash
tmux kill-session -t github-runner 2>/dev/null; sleep 1
tmux new-session -d -s github-runner \
  'cd ~/Work/maquilinux && nix run .#runner'
```

**Standalone way:**
```bash
tmux kill-session -t github-runner 2>/dev/null; sleep 1
tmux new-session -d -s github-runner '~/bin/Runner.Listener run'
```

### Re-register After Problems

If you see "session conflict" or runner shows offline:

**From any machine with GitHub CLI:**
```bash
# 1. Find and delete old runner
RUNNER_ID=$(gh api repos/glats/maquilinux/actions/runners | \
  jq -r '.runners[] | select(.name == "<your-runner-name>") | .id')
gh api repos/glats/maquilinux/actions/runners/$RUNNER_ID --method DELETE
```

**On the runner host:**
```bash
# 2. Stop and clean
tmux kill-session -t github-runner
pkill -9 -f Runner.Listener
rm -rf ~/.credentials* ~/.runner ~/.credentials_rsaparams _diag _work .env

# 3. Get new token (from GitHub CLI machine)
# 4. Reconfigure (see Step 4 in installation)
```

---

## Key Workflows

The runner will automatically pick up jobs from GitHub Actions:

| Workflow | Trigger | Duration | Resources |
|----------|---------|----------|-----------|
| `build.yml` | Push to `SPECS/*` | 5-30 min | Standard |
| `bootstrap-rust.yml` | Push to rust specs | 2-6 hours | High CPU/RAM |

All workflows require the runner to have label `maquilinux`.

---

## Troubleshooting

### Session Conflict Error

Error: `A session for this runner already exists`

- Wait 30 minutes for session to expire, OR
- Re-register (see above)

### Runner Shows Offline

1. Check tmux: `tmux ls`
2. Check process: `ps aux | grep Runner`
3. Check network: `curl -I https://github.com`
4. Restart runner

### Library Errors (Standalone)

**`libstdc++.so.6 not found`:**
```bash
# Debian/Ubuntu
sudo apt-get install libstdc++6

# Fedora
sudo dnf install libstdc++

# Arch
sudo pacman -S libstdc++5
```

**`libicu*.so not found`:**
```bash
# Debian/Ubuntu
sudo apt-get install libicu-dev

# Fedora
sudo dnf install libicu

# Arch
sudo pacman -S icu
```

### Disk Full During Build

```bash
# Check space
df -h $MQL_LFS

# Clean old build artifacts
cd ~/Work/maquilinux
rm -rf RPMS/BUILD/* RPMS/BUILDROOT/*

# Archive old backups
./mql backup archive 30  # Move backups older than 30 days
```

### Overlay Not Mounted

```bash
# Check
mount | grep overlay

# Remount
sudo umount -l $MQL_LFS/merged 2>/dev/null || true
sudo mount -t overlay overlay \
  -o lowerdir=$MQL_LFS/base,upperdir=$MQL_LFS/layers/upper,\
workdir=$MQL_LFS/layers/work \
  $MQL_LFS/merged
```

---

## Security Notes

1. **Runner token expires** after 1 hour (get new one if needed)
2. **Credentials stored** in `~/.credentials*` - never share these
3. **Root access required** for overlay mounts and chroot operations
4. **Network:** Runner needs outbound HTTPS to `github.com` and `*.actions.githubusercontent.com`

---

## Example: Full Setup Checklist

```bash
# 1. Prepare host
ssh my-runner "mkdir -p ~/Work && cd ~/Work && \
  git clone https://github.com/glats/maquilinux.git"

# 2. Configure paths
ssh my-runner "echo 'MQL_LFS=/mnt/maquilinux' > ~/Work/maquilinux/mql.local"

# 3. Mount disk (if not auto-mounted)
ssh my-runner "sudo mkdir -p /mnt/maquilinux/base && \
  sudo mount /dev/sdb1 /mnt/maquilinux/base && \
  sudo mount -t overlay overlay -o lowerdir=/mnt/maquilinux/base,\
upperdir=/mnt/maquilinux/layers/upper,workdir=/mnt/maquilinux/layers/work \
    /mnt/maquilinux/merged"

# 4. Install runner
cd ~/Work/maquilinux
nix develop  # or install packages manually

# 5. Get token
TOKEN=$(gh api repos/glats/maquilinux/actions/runners/registration-token \
  --method POST | jq -r '.token')

# 6. Configure
ssh my-runner "cd ~ && nix develop ~/Work/maquilinux -c bash -c \
  './bin/Runner.Listener configure --url https://github.com/glats/maquilinux \
   --token $TOKEN --name my-runner --work _work --unattended --labels maquilinux'"

# 7. Start
ssh my-runner "tmux new-session -d -s github-runner \
  'nix run ~/Work/maquilinux#runner'"

# 8. Verify
gh api repos/glats/maquilinux/actions/runners | jq '.runners[] | \
  {name, status, labels: [.labels[].name]}'
```

---

## Next Steps

- See `docs/DEVELOPMENT.md` for contribution workflow
- See `docs/GETTING-STARTED.md` for first build instructions
- See `docs/agents/backup-system.md` for rootfs backup procedures
