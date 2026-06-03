from abc import ABC, abstractmethod

from ui import AppUI


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
    from settings import UserSettings

    Username = UserSettings.Get().Username
    if Username:
        return Username
    AppUI.ShowError("Set a username in Settings first.")
    return None


class StartAsHostAction(MenuAction):
    """Create a room on the LAN and wait for adventurers."""

    @property
    def Label(self) -> str:
        return "As Host"

    @property
    def Icon(self) -> str:
        return "👑"

    def Execute(self) -> bool:
        from network import AUTO_PORT, CampaignHost

        HostUsername = _RequireUsername()
        if not HostUsername:
            return True

        Host = CampaignHost(AUTO_PORT, HostUsername)
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
    """Join a room on the local network using its room number."""

    @property
    def Label(self) -> str:
        return "As Player"

    @property
    def Icon(self) -> str:
        return "🎲"

    def Execute(self) -> bool:
        from discovery import FindRoomOnLan, ParseRoomNumber
        from network import CampaignClient

        PlayerUsername = _RequireUsername()
        if not PlayerUsername:
            return True

        RoomText = AppUI.AskString("Join Room", "Enter Room Number", "")
        if RoomText is None:
            return True

        RoomNumber = ParseRoomNumber(RoomText)
        if RoomNumber is None:
            AppUI.ShowError("Invalid room number. Example: 54321")
            return True

        State: dict[str, str | None] = {"HostIp": None}

        CloseProgress = AppUI.ShowProgress("Searching for room on local network...")

        def Search() -> None:
            State["HostIp"] = FindRoomOnLan(RoomNumber)

        def OnFound() -> None:
            CloseProgress()
            HostIp = State["HostIp"]
            if not HostIp:
                AppUI.ShowError(
                    f"Room {RoomNumber} not found. Check the number and Wi‑Fi/LAN."
                )
                return
            Client = CampaignClient(HostIp, RoomNumber, PlayerUsername)
            Client.RunSession()

        AppUI.RunInBackground(Search, OnFound)
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
        from menu import Menu

        RoleMenu = Menu(
            "Start",
            [
                StartAsHostAction(),
                StartAsPlayerAction(),
                BackAction(),
            ],
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
        from settings import UserSettings

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


class SettingsAction(MenuAction):
    @property
    def Label(self) -> str:
        return "Settings"

    @property
    def Icon(self) -> str:
        return "⚙️"

    def Execute(self) -> bool:
        from menu import Menu
        from settings import UserSettings

        Current = UserSettings.Get()
        SettingsMenu = Menu(
            "Settings",
            [
                SetUsernameAction(),
                BackAction(),
            ],
            Subtitle=f"User: {Current.UsernameDisplay}",
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
