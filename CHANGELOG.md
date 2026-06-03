# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.0]: https://github.com/ahmadreza-log/dnd-dice-roller/releases/tag/v1.0.0
