"""Application shell: settings, menus, actions, and main loop."""

import json
from abc import ABC, abstractmethod
from pathlib import Path

from ui import AppUI


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


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
        return self._Username if self._Username else "(not set)"

    @property
    def HostIp(self) -> str:
        return self._HostIp

    @HostIp.setter
    def HostIp(self, Value: str) -> None:
        self._HostIp = Value.strip()

    @property
    def HostIpDisplay(self) -> str:
        """Saved target host IPv4 used when joining as a player."""
        return self._HostIp if self._HostIp else "(not set)"

    def Load(self) -> None:
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
        Data = {"Username": self._Username, "HostIp": self._HostIp}
        self._FilePath.write_text(
            json.dumps(Data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------


class MenuAction(ABC):
    """Base class for every menu option."""

    @property
    def IsBack(self) -> bool:
        return False

    @property
    @abstractmethod
    def Label(self) -> str:
        pass

    @property
    def Icon(self) -> str:
        return ""

    @abstractmethod
    def Execute(self) -> bool:
        pass


def _RequireUsername() -> str | None:
    Username = UserSettings.Get().Username
    if Username:
        return Username
    AppUI.ShowError("Set a username in Settings first.")
    return None


def _ParseTargetHostIp(Text: str) -> str | None:
    """Validate the DM LAN IPv4 a player connects to."""
    from network import ParseIpv4

    Parsed = ParseIpv4(Text.strip())
    if not Parsed or Parsed == "127.0.0.1":
        return None
    return Parsed


def _PromptTargetHostIp() -> str | None:
    """Ask which host IPv4 the player should connect to."""
    Settings = UserSettings.Get()
    IpText = AppUI.AskString(
        "Host IP",
        "Enter the Dungeon Master's LAN IPv4 to connect to.\nExample: 192.168.1.42",
        Settings.HostIp,
    )
    if IpText is None:
        return None

    Resolved = _ParseTargetHostIp(IpText)
    if not Resolved:
        AppUI.ShowError("Invalid Host IP. Enter a LAN IPv4 like 192.168.1.42")
        return None

    Settings.HostIp = Resolved
    Settings.Save()
    return Resolved


class StartAsHostAction(MenuAction):
    @property
    def Label(self) -> str:
        return "As Host"

    @property
    def Icon(self) -> str:
        return "👑"

    def Execute(self) -> bool:
        from network import AUTO_PORT, CampaignHost

        Host = CampaignHost(AUTO_PORT)
        try:
            Host.Start()
            Host.RunSession()
        except OSError as Error:
            AppUI.ShowError(f"Could not create room: {Error}")
        except Exception as Error:
            Host.Stop()
            AppUI.ShowError(f"Room error: {Error}")
        return True


class StartAsPlayerAction(MenuAction):
    @property
    def Label(self) -> str:
        return "As Player"

    @property
    def Icon(self) -> str:
        return "🎲"

    def Execute(self) -> bool:
        from network import CampaignClient, ParseRoomNumber

        PlayerUsername = _RequireUsername()
        if not PlayerUsername:
            return True

        HostIp = _PromptTargetHostIp()
        if not HostIp:
            return True

        RoomText = AppUI.AskString("Join Room", "Enter Room Number", "")
        if RoomText is None:
            return True

        RoomNumber = ParseRoomNumber(RoomText)
        if RoomNumber is None:
            AppUI.ShowError("Invalid room number. Example: 54321")
            return True

        CampaignClient(HostIp, RoomNumber, PlayerUsername).RunSession()
        return True


class BackAction(MenuAction):
    @property
    def IsBack(self) -> bool:
        return True

    @property
    def Label(self) -> str:
        return "Back"

    @property
    def Icon(self) -> str:
        return "↩️"

    def Execute(self) -> bool:
        return True


class StartAction(MenuAction):
    @property
    def Label(self) -> str:
        return "Start"

    @property
    def Icon(self) -> str:
        return "▶️"

    def Execute(self) -> bool:
        RoleMenu = Menu(
            "Start",
            [StartAsHostAction(), StartAsPlayerAction(), BackAction()],
            Subtitle="Host or Player?",
        )
        return RoleMenu.RunUntilBack()


class SetUsernameAction(MenuAction):
    @property
    def Label(self) -> str:
        return "Set Username"

    @property
    def Icon(self) -> str:
        return "👤"

    def Execute(self) -> bool:
        Current = UserSettings.Get()
        NewName = AppUI.AskString(
            "Set Username",
            f"Current: {Current.UsernameDisplay}\n\nEnter your username",
            Current.Username,
        )
        if NewName is None:
            return True

        NewName = NewName.strip()
        if not NewName:
            AppUI.ShowError("Username cannot be empty.")
            return True

        Current.Username = NewName
        Current.Save()
        AppUI.ShowNotice(f"Username saved: {NewName}", "success")
        return True


class SetHostIpAction(MenuAction):
    @property
    def Label(self) -> str:
        return "Set Target Host IP"

    @property
    def Icon(self) -> str:
        return "🌐"

    def Execute(self) -> bool:
        Current = UserSettings.Get()
        NewIp = AppUI.AskString(
            "Target Host IP",
            f"Current: {Current.HostIpDisplay}\n\n"
            "DM LAN IPv4 to connect to when joining as a player.\n"
            "Example: 192.168.1.42",
            Current.HostIp,
        )
        if NewIp is None:
            return True

        Resolved = _ParseTargetHostIp(NewIp)
        if not Resolved:
            AppUI.ShowError("Invalid Host IP. Enter a LAN IPv4 like 192.168.1.42")
            return True

        Current.HostIp = Resolved
        Current.Save()
        AppUI.ShowNotice(f"Target Host IP saved: {Resolved}", "success")
        return True


class SettingsAction(MenuAction):
    @property
    def Label(self) -> str:
        return "Settings"

    @property
    def Icon(self) -> str:
        return "⚙️"

    def Execute(self) -> bool:
        Current = UserSettings.Get()
        SettingsMenu = Menu(
            "Settings",
            [SetUsernameAction(), SetHostIpAction(), BackAction()],
            Subtitle=f"User: {Current.UsernameDisplay} · Target Host IP: {Current.HostIpDisplay}",
        )
        return SettingsMenu.RunUntilBack()


class ExitAction(MenuAction):
    @property
    def Label(self) -> str:
        return "Exit"

    @property
    def Icon(self) -> str:
        return "🚪"

    def Execute(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------


class Menu:
    """Menu definition; rendered as buttons by AppUI."""

    def __init__(self, Title: str, Actions: list[MenuAction], Subtitle: str = "") -> None:
        self._Title = Title
        self._Subtitle = Subtitle
        self._Actions = Actions

    @property
    def Title(self) -> str:
        return self._Title

    @property
    def Subtitle(self) -> str:
        return self._Subtitle

    @property
    def Actions(self) -> list[MenuAction]:
        return self._Actions

    def Open(self) -> None:
        Application.Instance().ShowMenu(self)

    def RunUntilBack(self) -> bool:
        self.Open()
        return True


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


class Application:
    """Main program: tkinter window with menu navigation."""

    _Instance: "Application | None" = None

    def __init__(self, MainMenu: Menu) -> None:
        self._MainMenu = MainMenu
        self._CurrentMenu = MainMenu
        Application._Instance = self

    @classmethod
    def Instance(cls) -> "Application":
        assert cls._Instance is not None
        return cls._Instance

    @classmethod
    def CreateDefault(cls) -> "Application":
        Actions: list[MenuAction] = [
            StartAction(),
            SettingsAction(),
            ExitAction(),
        ]
        MainMenu = Menu("D&D Dice Roller", Actions, Subtitle="Roll for initiative")
        return cls(MainMenu)

    def ShowMenu(self, Menu: Menu) -> None:
        self._CurrentMenu = Menu
        AppUI.ShowMenu(
            Menu.Title,
            Menu.Subtitle,
            Menu.Actions,
            self._HandleAction,
        )

    def _HandleAction(self, Action: MenuAction) -> None:
        if Action.IsBack:
            self.ShowMenu(self._MainMenu)
            return
        if not Action.Execute():
            AppUI.Root().quit()

    def Run(self) -> None:
        AppUI.Initialize("D&D Dice Roller")
        self.ShowMenu(self._MainMenu)
        AppUI.Root().mainloop()
