# Release v1.1.0 — D&D Dice Roller

**Copy the section below into the GitHub Release description.**

---

## D&D Dice Roller v1.1.0

Maintenance and UX release — **explicit host LAN IP**, a **leaner codebase**, and a **single requirements file**.

### Download

| Asset | Description |
|-------|-------------|
| **DND-Dice-Roller.exe** | Single-file Windows app (~18 MB). Build with `pyinstaller --clean dnd_dice_roller.spec` and attach from `dist/`. |

### What's new in v1.1.0

- **Host LAN IP dialog** when you choose **Start → As Host**
  - Defaults to your saved IP or auto-detected network address
  - Leave empty to use the detected LAN IPv4
  - Invalid addresses are rejected; loopback-only detection prompts manual entry
- **Settings → Set Host IP** — set the IP advertised to players before hosting
- **Host IP + Room Number** shown in campaign chat headers (host and players)
- **Simpler project layout** — 6 Python modules instead of 13
- **One `requirements.txt`** — runtime + PyInstaller in a single file

### Quick start

**Host (DM)**

1. Run `DND-Dice-Roller.exe`
2. **Start → As Host**
3. Confirm or enter your **LAN IPv4** (e.g. `192.168.1.42`)
4. Share **Host IP** and **Room Number** from the chat header with your party
5. Roll and chat — your dice rolls stay private

**Player**

1. **Settings → Set Username**
2. **Start → As Player**
3. Enter the host’s **Room Number**
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
pip install -r requirements.txt
pyinstaller --clean dnd_dice_roller.spec
```

### Full changelog

See [CHANGELOG.md](https://github.com/ahmadreza-log/dnd-dice-roller/blob/main/CHANGELOG.md#110---2026-06-03).

---

**Roll for initiative.**
