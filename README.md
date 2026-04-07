# AC Mitsubishi – Home Assistant Custom Integration

Controls a Mitsubishi Electric AC unit via **Modbus RTU over TCP** (RS-485 → Ethernet adapter such as Elfin EW11 or USR-TCP232).

Originally ported from a FIBARO HC3 Quick App by [Indome.ee / Kuuno](https://indome.ee).

## Features

| Capability | Detail |
|---|---|
| HVAC modes | Off / Heat / Cool / Dry / Fan only / Auto |
| Fan speeds | Auto / Quiet / Weak / Strong / Very Strong |
| Vane / swing | Auto / Position 1–5 / Swing |
| Temperature | Current room temp + settable target (16–31 °C, step 0.5) |
| Protocol | Modbus RTU over raw TCP – no MBAP header |
| Polling | Configurable interval (default 5 s, local\_polling) |

---

## GitHub repository settings (HACS / validation)

HACS’ **topics** check reads your repository metadata on GitHub (not files in this repo).  
In the repo **Settings → General → Topics**, add for example:

`home-assistant`, `hacs-custom`, `custom-integration`, `mitsubishi`, `modbus`, `climate`, `hvac`

Also ensure the repo has a **short description** and **Issues** enabled (other HACS checks).

**Public repository:** HACS and `hacs/action` load `hacs.json` and integration `manifest.json` from
public `raw.githubusercontent.com` URLs. On a **private** repo those requests return 404, so validation
often reports an invalid `hacs.json` and `integration_manifest … got None` even when the files are
committed. The integration must stay **public** for HACS users; use a public fork if you need private
collaboration elsewhere.

---

## Installation

### HACS (recommended)
1. In HACS, add this repository as a **custom integration** repository (category: Integration).
2. Install **AC Mitsubishi (Modbus RTU over TCP)**.
3. Restart Home Assistant.
4. **Settings → Devices & services → Add integration → AC Mitsubishi**.

### Manual
1. Copy `custom_components/ac_mitsubishi/` to `<config>/custom_components/ac_mitsubishi/`
2. Restart Home Assistant
3. **Settings → Devices & services → Add integration → AC Mitsubishi**

## Configuration

| Field | Default | Description |
|---|---|---|
| Host | — | IP address of the Modbus TCP adapter |
| Port | 4001 | TCP port of the adapter |
| Polling interval | 5 s | How often registers are read (seconds; change later under **Configure**) |

## Development

Open `ac-mitsubishi-ha.code-workspace` in Cursor or VS Code.

Workspace tasks (**Terminal → Run Task**) use the project `.venv` for tests and lint. **Clean caches** removes pytest/ruff/mypy caches, `__pycache__` under `custom_components` / `tests` / `scripts`, and build artifacts (not `.venv`; see `scripts/clean.ps1` / `scripts/clean.sh`).

**Creating `.venv`:** from the repo root, run `python -m venv .venv` on Windows, or `python3 -m venv .venv` on Linux/macOS/WSL. Then activate and install packages as in **PowerShell (Windows)** or **Bash (Linux / macOS)** below. In Cursor/VS Code, use **Python: Select Interpreter** and choose `.venv` once it exists.

Deploy scripts require **`.env.ha`** at the repo root (copy **`.env.ha.example`**). They read **`HA_HOST`** (required) and **`HA_USER`** (defaults to **`root`** when omitted, same pattern as KVent). Use **SSH keys** so `ssh` / `scp` / `rsync` over SSH never need an account password (see below). **Deploy to HA** runs `scripts/deploy-ha-rsync.sh` on Linux/macOS/WSL (`rsync -avz --delete`, plus a remote `rsync` precheck for HAOS) and **`scripts/deploy-ha-scp.ps1`** on Windows (`ssh mkdir -p`, then `scp` with **`-o StrictHostKeyChecking=no -o BatchMode=yes`** and **`-i`** to `ha_deploy` when present). Both print the integration **version** from `manifest.json` and **omit** **`__pycache__`**, **`*.pyc`**, and common tool caches. `scp` does not remove files on the host that you deleted locally.

Optional **`HA_HTTP_URL`** (e.g. `http://homeassistant.local:8123`) and **`HA_TOKEN`** (Profile → Security → **Long-lived access token**) call the **`homeassistant.restart`** service after a successful deploy so Core reloads custom components without using the UI.

**Deploy to HA (rsync via WSL)** is for Windows when you want `rsync --delete` and have **rsync on the SSH server** (often **not** on Home Assistant OS). It uses **`deploy-ha-wsl.ps1`** and **`deploy-ha-wsl-bootstrap.sh`** (copies your Windows private key into WSL `~/.ssh` with `chmod 600` because OpenSSH rejects keys on `/mnt/c` with mode 0777).

### SSH keys for deploy

You need **SSH login** to the machine (or add-on) where Home Assistant’s config lives - the same user and host you will put in **`.env.ha`** as **`HA_USER`** and **`HA_HOST`**.

**Why password login still appears:** OpenSSH only tries default private-key filenames (`id_ed25519`, `id_rsa`, …). A custom key named **`ha_deploy`** is **ignored** unless you pass **`-i`** or set **`IdentityFile`** for that host in **`%USERPROFILE%\.ssh\config`**. Deploy scripts pass **`-i`** when **`%USERPROFILE%\.ssh\ha_deploy`** exists (override with **`HA_SSH_IDENTITY`** in **`.env.ha`**).

#### Windows (PowerShell) - full sequence

If **`ssh`** is missing, add **OpenSSH Client** (Settings → Optional features or [OpenSSH on Windows](https://learn.microsoft.com/windows-server/administration/openssh/openssh_install_firstuse)).

1. **Confirm client**

   ```powershell
   ssh -V
   ```

2. **Key pair** (do not use `~` in `-f` on Windows)

   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
   ssh-keygen -t ed25519 -C "home-assistant-deploy" -f "$env:USERPROFILE\.ssh\ha_deploy"
   ```

3. **Install the public key on the server** (no `ssh-copy-id` on Windows; you enter the account password once)

   ```powershell
   Get-Content "$env:USERPROFILE\.ssh\ha_deploy.pub" | ssh root@192.168.116.55 "umask 077; mkdir -p .ssh; chmod 700 .ssh; cat >> .ssh/authorized_keys; chmod 600 .ssh/authorized_keys"
   ```

   Or set variables in the same window, then pipe:

   ```powershell
   $HA_USER = "root"; $HA_HOST = "192.168.116.55"
   Get-Content "$env:USERPROFILE\.ssh\ha_deploy.pub" | ssh "$HA_USER@$HA_HOST" "umask 077; mkdir -p .ssh; chmod 700 .ssh; cat >> .ssh/authorized_keys; chmod 600 .ssh/authorized_keys"
   ```

   If **`ssh`** prints **`usage:`**, `user@host` was empty; use the **`root@...`** line literally.

4. **Test with the deploy key** (include **`-i`** unless you added `config`)

   ```powershell
   ssh -i "$env:USERPROFILE\.ssh\ha_deploy" root@192.168.116.55
   ```

5. **Optional: `ssh` config** (`notepad "$env:USERPROFILE\.ssh\config"`)

   ```text
   Host my-ha
     HostName 192.168.116.55
     User root
     IdentityFile ~/.ssh/ha_deploy
   ```

   Use a full path with forward slashes if needed: `IdentityFile C:/Users/YourName/.ssh/ha_deploy`. Set **`HA_HOST=my-ha`** in **`.env.ha`** if you use a **`Host`** alias.

6. **Optional: passphrase + `ssh-agent`**

   ```powershell
   Get-Service ssh-agent | Set-Service -StartupType Manual
   Start-Service ssh-agent
   ssh-add "$env:USERPROFILE\.ssh\ha_deploy"
   ```

   If **`Start-Service`** is denied, run those lines once in **PowerShell as Administrator**, or set **OpenSSH Authentication Agent** to Manual/Automatic in **`services.msc`**.

7. **`.env.ha`** - copy **`.env.ha.example`**, set **`HA_USER`** / **`HA_HOST`**. Optional **`HA_SSH_IDENTITY`** if the key is not **`%USERPROFILE%\.ssh\ha_deploy`**.

#### Still prompted for a password?

- Run **`ssh -v -i "$env:USERPROFILE\.ssh\ha_deploy" root@192.168.116.55`** and inspect **`Offering public key`** / accept or refuse.

- On the server: **`~/.ssh`**, **`authorized_keys`**, permissions; use the same **user@host** as in **`.env.ha`**.

#### Linux / macOS / WSL

```bash
mkdir -p ~/.ssh
ssh-keygen -t ed25519 -C "home-assistant-deploy" -f ~/.ssh/ha_deploy
ssh-copy-id -i ~/.ssh/ha_deploy.pub HA_USER@HA_HOST
ssh -i ~/.ssh/ha_deploy HA_USER@HA_HOST
```

If **`~/.ssh/ha_deploy`** exists, deploy uses **`RSYNC_RSH` / `scp -i`** automatically; override with **`HA_SSH_IDENTITY`** in **`.env.ha`**.

With key auth working, deploy should not ask for an **account** password.

### WSL (optional: rsync deploy on Windows)

Install [WSL](https://learn.microsoft.com/windows/wsl/install), then in the distro:

```bash
sudo apt update && sudo apt install -y rsync openssh-client
```

**rsync must exist on the SSH server**, not only in WSL. Home Assistant OS often has **no rsync**; the deploy script then tells you to use the task **`Deploy to HA`** (**scp**). **`Deploy to HA (rsync via WSL)`** needs **`rsync` on the server** (e.g. generic Linux).

Open the repo from Windows so paths map under **`/mnt/...`** in WSL.

### PowerShell (Windows)

```powershell
git clone https://github.com/maxlarin63/ac-mitsubishi-ha.git
Set-Location ac-mitsubishi-ha
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pytest pytest-asyncio pytest-homeassistant-custom-component pytest-socket ruff
pytest tests/ -v
ruff check custom_components/
```

If script activation is blocked, run once for your user:

`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Bash (Linux / macOS)

```bash
git clone https://github.com/maxlarin63/ac-mitsubishi-ha.git
cd ac-mitsubishi-ha
python -m venv .venv && source .venv/bin/activate
pip install pytest pytest-asyncio pytest-homeassistant-custom-component pytest-socket ruff
pytest tests/ -v
ruff check custom_components/
```

On Linux/macOS, if the workspace points **`python.defaultInterpreterPath`** at **`Scripts/python.exe`**, use **Python: Select Interpreter** and pick **`.venv/bin/python`**.

## Modbus Register Map

| Register | FC | Address | Description |
|---|---|---|---|
| Mode | 0x03 | 0x0000 | HVAC operating mode |
| Setpoint | 0x03 | 0x0001 | Target temp × 10 |
| Fan | 0x03 | 0x0002 | Fan speed |
| Vane | 0x03 | 0x0003 | Vane/swing position |
| Power | 0x03 | 0x0007 | 0=off, 1=on |
| Room temp | 0x04 | 0x0000 | Current temp × 10 |

## License

MIT
