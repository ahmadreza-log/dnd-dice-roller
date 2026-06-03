# D&D Dice Roller

A desktop app for **Dungeons & Dragons** sessions on your local network (LAN). Host a campaign as the Dungeon Master, let players join with a room number, chat in real time, and roll polyhedral dice together — no Python required for the Windows `.exe` build.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Version](https://img.shields.io/badge/version-1.2.0-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## Features

- **LAN campaigns** — Host and players on the same Wi‑Fi / local network
- **Player target Host IP** — Clients enter the DM's LAN IPv4 when joining
- **Campaign chat** — Live messages with Telegram-style rounded bubbles
- **Per-player colors** — Each adventurer gets a unique bubble color when they join
- **Dice roller** — D4, D6, D8, D10, D12, D20, and D100 from the chat window
- **Rich roll display** — Large readable values, totals, Nat 20 / Nat 1 highlights
- **Private DM rolls** — Dungeon Master dice rolls are visible only to the host
- **Whisper to DM** — Players send private messages via `/dm` or the **Whisper DM** button
- **Room log** — Timestamped session activity viewer from the campaign chat window
- **Username & target Host IP settings** — Saved locally under `%LOCALAPPDATA%\DND-Dice-Roller`
- **Standalone Windows exe** — Built with PyInstaller; no Python install needed for end users

---

## Quick start (Windows exe)

1. Download **`DND-Dice-Roller.exe`** from the [Releases](https://github.com/ahmadreza-log/dnd-dice-roller/releases) page.
2. Run the file (allow through Windows Firewall if prompted for LAN play).
3. **Host:** `Start` → `As Host` → share the **Room Number** with players (share your LAN IP separately).
4. **Player:** `Settings` → set username → `Start` → `As Player` → enter **Host IP**, then **Room Number**.

> Host and all players must be on the **same local network**.

---

## Run from source

### Requirements

- Python **3.11+**
- Windows (primary target; tkinter + LAN networking)

### Setup

```powershell
git clone https://github.com/ahmadreza-log/dnd-dice-roller.git
cd dnd-dice-roller

python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

python main.py
```

---

## How to play

### Dungeon Master (Host)

1. Open the app and choose **Start → As Host**.
2. Share the **Room Number** from the chat header with players (tell them your LAN IP separately, e.g. via `ipconfig`).
3. Use chat and dice buttons during the session.
4. Your **dice rolls stay private** — only you see them; chat messages are public.

### Player

1. Set a username under **Settings → Set Username**.
2. Optionally set **Settings → Set Target Host IP** (default when joining).
3. Choose **Start → As Player**.
4. Enter the **Host IP** (DM's LAN IPv4), then the **Room Number**.
5. Chat and roll dice.

### Dice in chat

- Click a die button (D4–D100), enter how many to roll, then **Send** or press **Enter**.
- Multi-dice rolls show individual values and a total.
- D20 Nat 20 / Nat 1 are highlighted in green / red.

---

## Build the exe yourself

```powershell
.\venv\Scripts\activate
pip install -r requirements.txt

pyinstaller --clean dnd_dice_roller.spec
```

Output: `dist\DND-Dice-Roller.exe` (~18 MB, single file, no console window).

---

## Project structure

| File | Purpose |
|------|---------|
| `paths.py` | AppData directory and settings file paths |
| `main.py` | Entry point; venv auto-switch |
| `app.py` | Application, menus, actions, and user settings |
| `ui.py` | Theme tokens, main window, dialogs |
| `chat.py` | Campaign chat, bubble feed, and player colors |
| `dice.py` | Dice logic and wire format |
| `network.py` | TCP host/client, chat relay, UDP discovery |
| `dnd_dice_roller.spec` | PyInstaller build spec |

---

## Networking notes

| Port | Protocol | Use |
|------|----------|-----|
| Room number (dynamic) | TCP | Campaign chat and dice messages |
| `5554` | UDP | Room advertisement while hosting (optional) |

If a player cannot connect:

- Confirm **Host IP** and **Room Number** with the DM.
- Confirm everyone is on the same LAN / Wi‑Fi.
- Check Windows Firewall allows the app on private networks.

---

## Configuration

User settings are stored in the per-user AppData folder:

`%LOCALAPPDATA%\DND-Dice-Roller\settings.json`

Example (Windows):

`C:\Users\<You>\AppData\Local\DND-Dice-Roller\settings.json`

```json
{
  "Username": "YourName",
  "HostIp": "192.168.1.42"
}
```

`HostIp` is the **target DM address** saved for joining as a player.

On first run after this change, an older `settings.json` next to the app or `.exe` is copied automatically if present.

---

## Tech stack

- **Python 3.11+**
- **tkinter** + **ttkbootstrap** (dark UI)
- **TCP** JSON line protocol for chat
- **UDP** broadcast for room discovery
- **PyInstaller** for the Windows executable

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

**Ahmadreza Ebrahimi** — [ahmadreza-log/dnd-dice-roller](https://github.com/ahmadreza-log/dnd-dice-roller)

Roll for initiative.
