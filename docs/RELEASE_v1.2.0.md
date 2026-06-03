# Release v1.2.0 — D&D Dice Roller

**Copy the section below into the GitHub Release description.**

---

## D&D Dice Roller v1.2.0

Feature release — AppData settings, **Room Log**, and **private whispers to the DM**.

### Download

| Asset | Description |
|-------|-------------|
| **DND-Dice-Roller.exe** | Single-file Windows app (~18 MB). Build with `pyinstaller --clean dnd_dice_roller.spec` and attach from `dist/`. |

### What's new in v1.2.0

- **AppData settings** — Username and target Host IP saved under `%LOCALAPPDATA%\DND-Dice-Roller`
- **Room Log** — Open **Room Log** in campaign chat for a live timestamped session log
- **Whisper to DM** — Players use `/dm your message` or **Whisper DM**; only the DM sees it
- **Room Log fixes** — Reliable scrolling, live updates, readable dice and whisper lines

### Quick start

**Host (DM)**

1. Run `DND-Dice-Roller.exe`
2. **Start → As Host**
3. Share **Room Number** and your LAN IP with players
4. Use **Room Log** to review session activity; whispers from players appear with 🔒

**Player**

1. **Settings → Set Username** (and optionally **Set Target Host IP**)
2. **Start → As Player** → enter **Host IP** and **Room Number**
3. Chat publicly or whisper with `/dm` / **Whisper DM**

> Everyone must be on the **same local network**. Allow the app through Windows Firewall if prompted.

### From source

```powershell
git clone https://github.com/ahmadreza-log/dnd-dice-roller.git
cd dnd-dice-roller
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Full changelog

See [CHANGELOG.md](https://github.com/ahmadreza-log/dnd-dice-roller/blob/main/CHANGELOG.md#120---2026-06-03).

---

**Roll for initiative.**
