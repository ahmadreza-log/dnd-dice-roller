# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-06-03

AppData settings, room session log, and private whispers to the DM.

### Added

- **AppData storage** — Settings saved under `%LOCALAPPDATA%\DND-Dice-Roller` (legacy `settings.json` migrated automatically)
- **Room Log** — Live timestamped session log from the campaign chat window
- **Whisper to DM** — Players send private messages with `/dm your message` or **Whisper DM**
- **`paths.py`** — Central per-user data directory helpers

### Fixed

- Room Log window layout, live updates, and readable dice/whisper formatting

## [1.1.2] - 2026-06-03

Hotfix — restore missing `CampaignHost` class so **Start → As Host** works again.

### Fixed

- `ImportError: cannot import name 'CampaignHost' from 'network'` when starting as Host (class header accidentally removed in v1.1.1)

## [1.1.1] - 2026-06-03

Fix host/player IP flow — players choose the target host IP to connect to.

### Fixed

- Removed Host IP prompt when starting as Host (regression from v1.1.0)
- Host session again only shares the **Room Number**; no IP configuration on the DM side

### Added

- **Host IP prompt for players** when joining — enter the DM's LAN IPv4, then the room number
- **Settings → Set Target Host IP** — save the default host address for player connections

### Changed

- Player join connects directly to `Host IP` + room number (no UDP room search on join)
- Settings `HostIp` field is the **client target host IP**, not the DM's advertised address

## [1.1.0] - 2026-06-03

Cleaner codebase, explicit host LAN IP, and simplified dependencies.

### Added

- **Host LAN IP** prompt when starting as Host (default: saved or auto-detected network IP)
- **Settings → Set Host IP** to configure the advertised IPv4 before hosting
- **Host IP** shown in campaign chat headers (host and players)
- IPv4 validation (`ParseIpv4`) with fallback to detected LAN address

### Changed

- Consolidated Python modules from 13 files to **6** (`app`, `ui`, `chat`, `network`, `dice`, `main`)
- Merged theme into `ui.py`, chat bubbles/colors into `chat.py`, discovery into `network.py`
- Single **`requirements.txt`** for runtime and PyInstaller build
- README project structure and build instructions updated

### Removed

- Standalone modules: `actions.py`, `menu.py`, `settings.py`, `gui_theme.py`, `discovery.py`, `chat_bubbles.py`, `player_colors.py`
- `requirements-build.txt` (merged into `requirements.txt`)

## [1.0.0] - 2026-06-03

First stable release — LAN D&D dice roller with campaign chat.

### Added

- Desktop GUI with ttkbootstrap dark theme
- Host campaign mode (Dungeon Master) with automatic LAN port
- Player join by room number with UDP discovery
- Real-time campaign chat over TCP
- In-chat polyhedral dice (D4–D100) with count prompt
- Telegram-style rounded chat bubbles
- Per-player bubble colors assigned on join
- Username label above each bubble (outside the fill)
- Rich dice roll rendering (Nat 20 / Nat 1, totals, multi-dice rows)
- Private DM dice rolls (host-only, not broadcast to players)
- Username settings persisted to `settings.json`
- Windows standalone executable via PyInstaller (`DND-Dice-Roller.exe`)
- Build spec and `requirements-build.txt`

### Changed

- Replaced plain text chat log with scrollable bubble feed
- Structured dice wire format (`🎲ROLL|…`) for cross-client rendering

[1.2.0]: https://github.com/ahmadreza-log/dnd-dice-roller/releases/tag/v1.2.0
[1.1.2]: https://github.com/ahmadreza-log/dnd-dice-roller/releases/tag/v1.1.2
[1.1.1]: https://github.com/ahmadreza-log/dnd-dice-roller/releases/tag/v1.1.1
[1.1.0]: https://github.com/ahmadreza-log/dnd-dice-roller/releases/tag/v1.1.0
[1.0.0]: https://github.com/ahmadreza-log/dnd-dice-roller/releases/tag/v1.0.0
