# Python dev container (sysbox + systemd + sshd)

## Step 0 — What you need on the Windows side

* **WSL2** with an Ubuntu distro (`wsl --install -d Ubuntu` in PowerShell, then reboot).
* **OpenSSH client** on Windows. It ships with Windows 10/11; check with
  `ssh -V` in PowerShell.
* **VS Code** with the **Remote - SSH** extension (`ms-vscode-remote.remote-ssh`).

> Do **not** use Docker Desktop. Sysbox is incompatible with it. Docker Engine
> must be installed natively *inside* the WSL2 distro.

---

## Step 1 — SSH key on Windows

In **PowerShell** (not WSL):

```powershell
# 1. Generate a key if you don't already have one
ssh-keygen -t ed25519 -C "you@example.com"
#    Accept the default path: C:\Users\<you>\.ssh\id_ed25519

# 2. Start the Windows ssh-agent and have it start on every boot
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent

# 3. Load the key into the agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519

# 4. Confirm
ssh-add -l
```

The agent is what makes `ForwardAgent yes` work later, so the container can use
your key for `git push` without the private key ever being copied into it.

---

## Step 2 — Docker Engine + sysbox inside WSL2

Open the Ubuntu WSL2 shell.

```bash
# Docker Engine (official convenience script)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
```

Close and reopen the WSL shell (or `wsl --shutdown` from PowerShell) so the
`docker` group membership applies.

```bash
# sysbox-ce — check https://github.com/nestybox/sysbox/releases for the
# current release and match your Ubuntu version.
wget https://downloads.nestybox.com/sysbox/releases/v0.6.4/sysbox-ce_0.6.4-0.linux_amd64.deb
sudo apt-get install -y jq
sudo apt-get install -y ./sysbox-ce_0.6.4-0.linux_amd64.deb
```

Verify the runtime is registered:

```bash
docker info | grep -i runtimes
# Runtimes: sysbox-runc runc io.containerd.runc.v2
```

If `sysbox-runc` is missing, restart Docker (`sudo systemctl restart docker`,
or `sudo service docker restart` if systemd isn't enabled in your distro) and
check again.

> **WSL2 caveat:** sysbox needs systemd in the distro. If `systemctl` errors
> out, add this to `/etc/wsl.conf` and run `wsl --shutdown` from PowerShell:
> ```ini
> [boot]
> systemd=true
> ```

---

## Step 3 — Get the project onto the Linux filesystem

Keep the repo inside WSL's ext4, **not** under `/mnt/c/...` — bind-mount
performance across the 9P boundary is bad enough to be noticeable on every
file save and every `pytest` run.

```bash
mkdir -p ~/projects && cd ~/projects
git clone <your-repo-url> anything-helps
cd anything-helps/docker-python
```

---

## Step 4 — Authorize your Windows key in the container

The compose file mounts `./authorized_keys` read-only at
`/home/dev/.ssh/authorized_keys`. Create it as a **file** (if it doesn't exist,
Docker silently creates a *directory* there and SSH auth fails in a confusing
way):

```bash
cd ~/projects/anything-helps/docker-python
cp /mnt/c/Users/<YourWindowsUser>/.ssh/id_ed25519.pub ./authorized_keys
chmod 600 ./authorized_keys
```

Sanity check — one line, starting with `ssh-ed25519`:

```bash
cat ./authorized_keys
```

The file must be owned by UID 1000 (the `dev` user inside the container). The
default WSL2 user is UID 1000, so creating it as yourself is correct — verify
with `id -u`.

### Optional: git identity

`.gitconfig` and `.git-credentials` next to this README are mounted into the
container. They start empty; fill them in if you want git to be preconfigured:

```bash
cat > .gitconfig <<'EOF'
[user]
    name = Your Name
    email = you@example.com
[init]
    defaultBranch = main
EOF
```

---

## Step 5 — Build and start the container

```bash
cd ~/projects/anything-helps/docker-python
docker compose build          # first build takes a few minutes
docker compose up -d
```

Check it came up and that systemd booted properly inside:

```bash
docker compose ps
docker compose exec dev systemctl is-system-running     # "running" or "degraded" is fine
docker compose exec dev systemctl status ssh --no-pager
```

Smoke-test SSH **from WSL2 first** — this isolates container problems from
Windows-side problems:

```bash
ssh -p 2223 dev@localhost
```

Inside, confirm the Python environment:

```bash
python --version          # Python 3.12.x
which python              # /opt/venv/bin/python
pip --version
uv --version
ls /workspace             # your project tree
exit
```

---

## Step 6 — SSH from Windows into the container

WSL2 forwards `localhost` from Windows, and the container publishes on
`127.0.0.1:2223` inside WSL, so from PowerShell:

```powershell
ssh -p 2223 dev@localhost
```

Accept the host-key fingerprint on first connect.

If that hangs or is refused, `localhost` forwarding isn't working. Get the
WSL IP from the Ubuntu shell:

```bash
hostname -I | awk '{print $1}'      # e.g. 172.24.112.3
```

and use that IP instead of `localhost` in the config below. Note it changes on
every WSL restart, which is why `localhost` is preferred when it works.

### Persist it in your SSH config

Create or edit `C:\Users\<you>\.ssh\config` (no extension):

```sshconfig
Host py-dev
    HostName localhost
    Port 2223
    User dev
    IdentityFile ~/.ssh/id_ed25519
    ForwardAgent yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

Then:

```powershell
ssh py-dev
```

---

## Step 7 — Connect VS Code

1. Open VS Code on **Windows**.
2. `F1` → **Remote-SSH: Connect to Host…** → pick **py-dev**.
   (It reads the same `~/.ssh/config` you just edited.)
3. When asked for the platform, choose **Linux**.
4. VS Code installs its server into `/home/dev/.vscode-server`. This is on the
   `dev-home` volume, so it survives `docker compose down` and is only
   downloaded once.
5. **File → Open Folder…** → `/workspace`.

### Select the interpreter

1. Install the **Python** extension — in the Extensions pane, click
   *Install in SSH: py-dev*. Extensions install into the container,
   not Windows.
2. `F1` → **Python: Select Interpreter** → `/opt/venv/bin/python`.

Optional per-project settings (`.vscode/settings.json` in `/workspace`):

```json
{
    "python.defaultInterpreterPath": "/opt/venv/bin/python",
    "python.terminal.activateEnvironment": false
}
```

`activateEnvironment: false` is right here because `/opt/venv/bin` is already
first on `PATH` for every login shell — see `/etc/profile.d/10-python-venv.sh`.

---

## Working with Python in the container

`/opt/venv` is the default environment and it's writable by `dev`, so
`pip install requests` just works without sudo. It lives outside `/home/dev`
deliberately: that path is a named volume and would shadow anything baked into
the image there.

For per-project isolation, create a venv inside the project:

```bash
cd /workspace/your-project
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

Or keep it out of the source tree on the persisted `dev-venvs` volume:

```bash
python -m venv /opt/venvs/myproject
source /opt/venvs/myproject/bin/activate
```

Preinstalled in `/opt/venv`: `uv`, `pipx`, `ipython`, `pytest`, `ruff`,
`black`, `mypy`.

---

## Everyday commands

```bash
docker compose up -d          # start
docker compose stop           # stop, keep the container
docker compose down           # remove container (named volumes survive)
docker compose down -v        # remove volumes too — wipes /home/dev
docker compose build          # rebuild after editing the Dockerfile
docker compose up -d --build  # rebuild and restart
docker compose logs -f        # systemd journal from PID 1
docker compose exec dev bash  # shell in as root, bypassing SSH
```

To change the Python version, edit `PYTHON_VERSION` (or export it) and rebuild:

```bash
PYTHON_VERSION=3.13 docker compose build --no-cache
```

---

## Security model and known limitations

This container is meant to be an isolation boundary for AI agents. It has two
layers:

* **sysbox** isolates the container from the host — container-root is remapped
  to an unprivileged host UID, so even an in-container root compromise is *not*
  host root.
* **Two Unix accounts** split trust *inside* the container:
  * `dev` — you. Passwordless sudo; use it to install packages and manage the box.
  * `agent` — the account AI agents run under. **No sudo, on purpose.** SSH in as
    `agent` to run them. Starting an agent from a `dev` shell hands it dev's sudo
    and defeats the separation.

### ⚠️ Accepted risk: the agent can edit the files that define its own sandbox

The build files (`docker/Dockerfile`, `docker/docker-compose.yml`) live **inside
the bind-mounted `/workspace`** and are writable by the `agent` account. A
compromised or misbehaving agent could edit the Dockerfile — add a sudoers line,
inject an SSH key, plant a backdoor — and that payload would run the next time
you `docker compose build && up`.

This is **knowingly left open for now**: the `docker/` config is part of this
repo and the `agent` account is currently expected to help work on it. The
compensating control is process, not permissions — **treat every change under
`docker/` as agent-influenced and review the diff before any rebuild**, exactly
as you would a merge request from an untrusted contributor.

To close it when the agent no longer needs to touch these files, either:

* **Lock it** (quick) — on the WSL2 host, make the config root-owned and
  inaccessible to `agent`:
  ```bash
  sudo chown -R root:root docker && sudo chmod 700 docker
  ```
* **Move it out** (durable) — relocate the build files to a sibling directory
  that is *not* bind-mounted, and mount only the project subtree as `/workspace`.
  Then the path simply doesn't exist for the agent, and there's no permission bit
  to misconfigure or revert.

---

## Troubleshooting

**`docker: unknown runtime specified sysbox-runc`**
Sysbox isn't registered. Re-run its install, restart Docker, and re-check
`docker info | grep -i runtimes`.

**`Permission denied (publickey)`**
1. `docker compose exec dev cat /home/dev/.ssh/authorized_keys` — if this
   errors with "Is a directory", delete the stray directory, create the file
   properly (Step 4) and `docker compose up -d --force-recreate`.
2. Confirm it matches your Windows key: `ssh-keygen -lf $env:USERPROFILE\.ssh\id_ed25519.pub`.
3. Verbose client: `ssh -vvv -p 2223 dev@localhost`.
4. Server side: `docker compose exec dev journalctl -u ssh -n 50 --no-pager`.

**Connection works from WSL but not from Windows**
`localhost` forwarding is broken. Use the WSL IP (Step 6), or `wsl --shutdown`
from PowerShell and restart.

**Port 2223 already in use**
Change the host side of the mapping in `docker-compose.yml`
(`"127.0.0.1:2224:22"`) and update `Port` in your Windows SSH config.

**`systemctl` fails inside the container**
The container is running under `runc`, not sysbox. Confirm with
`docker inspect py-dev --format '{{.HostConfig.Runtime}}'`.

**VS Code hangs on "Setting up SSH host"**
Usually a stale server install. From WSL:
`docker compose exec dev rm -rf /home/dev/.vscode-server`, then reconnect.

**`git push` asks for credentials**
Agent forwarding isn't reaching the container. Check `ForwardAgent yes` is in
your Windows SSH config, that `ssh-add -l` lists your key on Windows, and that
`echo $SSH_AUTH_SOCK` is non-empty inside the container.
