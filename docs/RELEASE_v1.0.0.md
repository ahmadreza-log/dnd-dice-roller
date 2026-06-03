# Release v1.0.0 — D&D Dice Roller

**Copy the section below into the GitHub Release description.**

---

## D&D Dice Roller v1.0.0

First public release — a **Windows desktop app** for D&D sessions on your **local network**. No Python install required when using the bundled executable.

### Download

| Asset | Description |
|-------|-------------|
| **DND-Dice-Roller.exe** | Single-file Windows app (~18 MB). Attach this file from `dist/` when publishing the release. |

### Highlights

- **Host a LAN campaign** as Dungeon Master — share a room number with your party
- **Join as a player** — enter the room number; UDP discovery finds the host on Wi‑Fi/LAN
- **Live campaign chat** with **Telegram-style bubbles**
- **Roll dice in chat** — D4, D6, D8, D10, D12, D20, D100
- **Each player gets a unique bubble color** when they join; username sits above the bubble
- **DM secret rolls** — host dice results stay private; player rolls are shared with everyone
- **Readable dice UI** — large values, totals, Nat 20 / Nat 1 highlights

### Quick start

**Host (DM)**

1. Run `DND-Dice-Roller.exe`
2. **Start → As Host**
3. Share the **Room Number** from the chat header
4. Roll and chat — your dice rolls are only visible to you

**Player**

1. **Settings → Set Username**
2. **Start → As Player**
3. Enter the host’s room number
4. Chat and roll with the party

> Everyone must be on the **same local network**. Allow the app through Windows Firewall if prompted.

### System requirements

- **OS:** Windows 10/11 (64-bit)
- **Python:** Not required for the `.exe`
- **Network:** Same LAN / Wi‑Fi as the host

### From source

```powershell
git clone https://github.com/ahmadreza-log/dnd-dice-roller.git
cd dnd-dice-roller
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Build the exe:

```powershell
pip install -r requirements-build.txt
pyinstaller --clean dnd_dice_roller.spec
```

### Known limitations

- Windows is the primary target platform
- LAN-only — not designed for internet-wide play without port forwarding
- Room discovery uses UDP broadcast; some guest networks may block it

### Full changelog

See [CHANGELOG.md](https://github.com/ahmadreza-log/dnd-dice-roller/blob/main/CHANGELOG.md#100---2026-06-03).

---

**Roll for initiative.**
