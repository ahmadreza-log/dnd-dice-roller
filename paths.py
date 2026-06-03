"""Per-user data directory (Windows AppData, with fallbacks elsewhere)."""

import os
import shutil
from pathlib import Path

APP_NAME = "DND-Dice-Roller"


def GetAppDataDir() -> Path:
    """Return the app data folder and ensure it exists."""
    Base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if not Base:
        Base = str(Path.home() / ".local" / "share")

    DataDir = Path(Base) / APP_NAME
    DataDir.mkdir(parents=True, exist_ok=True)
    return DataDir


def GetSettingsPath() -> Path:
    return GetAppDataDir() / "settings.json"


def MigrateLegacySettings(LegacyPath: Path, TargetPath: Path) -> None:
    """Copy settings.json from the app folder on first run after upgrade."""
    if TargetPath.is_file() or not LegacyPath.is_file():
        return

    TargetPath.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LegacyPath, TargetPath)
