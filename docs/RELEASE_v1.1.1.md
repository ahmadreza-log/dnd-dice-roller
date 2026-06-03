# Release v1.1.1 — D&D Dice Roller

**Copy the section below into the GitHub Release description.**

---

## D&D Dice Roller v1.1.1

Bugfix release — **players specify the Host IP** to connect to; the DM no longer enters an IP when hosting.

### Download

| Asset | Description |
|-------|-------------|
| **DND-Dice-Roller.exe** | Single-file Windows app (~18 MB). Build with `pyinstaller --clean dnd_dice_roller.spec` and attach from `dist/`. |

### What's fixed in v1.1.1

- **Host (DM)** — no IP dialog when choosing **Start → As Host**; share only the **Room Number**
- **Player (Client)** — must enter the **DM's LAN IPv4** (Host IP), then the **Room Number**
- **Settings → Set Target Host IP** — save the default host address before joining

### Quick start

**Host (DM)**

1. Run `DND-Dice-Roller.exe`
2. **Start → As Host**
3. Share your **Room Number** and your machine's LAN IP (e.g. from `ipconfig`) with players
4. Roll and chat — your dice rolls stay private

**Player**

1. **Settings → Set Username** (and optionally **Set Target Host IP**)
2. **Start → As Player**
3. Enter the **Host IP** (DM's LAN IPv4, e.g. `192.168.1.42`)
4. Enter the **Room Number** from the DM
5. Chat and roll with the party

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

See [CHANGELOG.md](https://github.com/ahmadreza-log/dnd-dice-roller/blob/main/CHANGELOG.md#111---2026-06-03).

---

**Roll for initiative.**
