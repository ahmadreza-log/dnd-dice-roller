import json
from pathlib import Path


class UserSettings:
    """Persistent user preferences stored in settings.json."""

    _Instance: "UserSettings | None" = None

    def __init__(self, FilePath: Path) -> None:
        self._FilePath = FilePath
        self._Username: str = ""
        self._HostIp: str = ""
        self.Load()

    @classmethod
    def Get(cls) -> "UserSettings":
        """Shared settings instance for the application."""
        if cls._Instance is None:
            ProjectRoot = Path(__file__).resolve().parent
            cls._Instance = cls(ProjectRoot / "settings.json")
        return cls._Instance

    @property
    def Username(self) -> str:
        return self._Username

    @Username.setter
    def Username(self, Value: str) -> None:
        self._Username = Value.strip()

    @property
    def UsernameDisplay(self) -> str:
        """Label-friendly username for menus."""
        return self._Username if self._Username else "(not set)"

    @property
    def HostIp(self) -> str:
        return self._HostIp

    @HostIp.setter
    def HostIp(self, Value: str) -> None:
        self._HostIp = Value.strip()

    @property
    def HostIpDisplay(self) -> str:
        return self._HostIp if self._HostIp else "(not set)"

    def Load(self) -> None:
        """Read settings from disk if the file exists."""
        if not self._FilePath.is_file():
            return

        try:
            Data = json.loads(self._FilePath.read_text(encoding="utf-8"))
            self._Username = str(Data.get("Username", "")).strip()
            self._HostIp = str(Data.get("HostIp", "")).strip()
        except (json.JSONDecodeError, OSError):
            self._Username = ""
            self._HostIp = ""

    def Save(self) -> None:
        """Write settings to disk."""
        Data = {"Username": self._Username, "HostIp": self._HostIp}
        self._FilePath.write_text(
            json.dumps(Data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
