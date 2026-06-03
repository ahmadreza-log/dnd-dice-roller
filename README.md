# D&D Dice Roller

A desktop app for **Dungeons & Dragons** sessions on your local network (LAN). Host a campaign as the Dungeon Master, let players join with a room number, chat in real time, and roll polyhedral dice together — no Python required for the Windows `.exe` build.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## Features

- **LAN campaigns** — Host and players on the same Wi‑Fi / local network
- **Room discovery** — Players join with a room number; UDP discovery finds the host automatically
- **Campaign chat** — Live messages with Telegram-style rounded bubbles
- **Per-player colors** — Each adventurer gets a unique bubble color when they join
- **Dice roller** — D4, D6, D8, D10, D12, D20, and D100 from the chat window
- **Rich roll display** — Large readable values, totals, Nat 20 / Nat 1 highlights
- **Private DM rolls** — Dungeon Master dice rolls are visible only to the host
- **Username settings** — Saved locally in `settings.json`
- **Standalone Windows exe** — Built with PyInstaller; no Python install needed for end users

---

## Quick start (Windows exe)

1. Download **`DND-Dice-Roller.exe`** from the [Releases](https://github.com/ahmadreza-log/dnd-dice-roller/releases) page.
2. Run the file (allow through Windows Firewall if prompted for LAN play).
3. **Host:** `Start` → `As Host` → share the **Room Number** with players.
4. **Player:** `Settings` → set your username → `Start` → `As Player` → enter the room number.

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
2. Note the **Room Number** shown in chat (this is the TCP port on your LAN).
3. Tell players the room number (voice, chat, etc.).
4. Use chat and dice buttons during the session.
5. Your **dice rolls stay private** — only you see them; chat messages are public.

### Player

1. Set a username under **Settings → Set Username**.
2. Choose **Start → As Player**.
3. Enter the host’s **Room Number**.
4. Wait for discovery to find the room, then chat and roll dice.

### Dice in chat

- Click a die button (D4–D100), enter how many to roll, then **Send** or press **Enter**.
- Multi-dice rolls show individual values and a total.
- D20 Nat 20 / Nat 1 are highlighted in green / red.

---

## Build the exe yourself

```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-build.txt

pyinstaller --clean dnd_dice_roller.spec
```

Output: `dist\DND-Dice-Roller.exe` (~18 MB, single file, no console window).

---

## Project structure

| File / folder | Purpose |
|---------------|---------|
| `main.py` | Entry point; venv auto-switch |
| `app.py` | Application shell and menu routing |
| `ui.py` | Main window and dialogs (ttkbootstrap) |
| `chat.py` | Campaign chat window |
| `chat_bubbles.py` | Telegram-style bubble rendering |
| `player_colors.py` | Per-player color assignment |
| `dice.py` | Dice logic and wire format |
| `network.py` | TCP host/client and chat relay |
| `discovery.py` | UDP room discovery on LAN |
| `actions.py` | Menu actions (Host, Player, Settings) |
| `settings.py` | Username persistence |
| `gui_theme.py` | Colors, fonts, bubble theme |
| `dnd_dice_roller.spec` | PyInstaller build spec |

---

## Networking notes

| Port | Protocol | Use |
|------|----------|-----|
| Room number (dynamic) | TCP | Campaign chat and dice messages |
| `5554` | UDP | Room discovery (`FIND_ROOM` / `ROOM_REPLY`) |

If players cannot find a room:

- Confirm everyone is on the same LAN / Wi‑Fi.
- Check Windows Firewall allows the app on private networks.
- Verify the room number with the host.

---

## Configuration

User settings are stored next to the app:

```json
{
  "Username": "YourName",
  "HostIp": ""
}
```

`settings.json` is created automatically and is listed in `.gitignore`.

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
