from abc import ABC, abstractmethod

import questionary

from terminal import TerminalUI


class MenuAction(ABC):
    """Base class for every menu option."""

    @property
    def IsBack(self) -> bool:
        """True when this option only returns to the parent menu."""
        return False

    @property
    @abstractmethod
    def Label(self) -> str:
        """Display text shown in the menu for this action."""
        pass

    @property
    def Icon(self) -> str:
        """Emoji icon shown beside the label in the menu."""
        return ""

    @abstractmethod
    def Execute(self) -> bool:
        """Run the action. Return False to quit the entire application."""
        pass


def _RequireUsername() -> str | None:
    """Return username or None after showing an error notice."""
    from settings import UserSettings

    Username = UserSettings.Get().Username
    if Username:
        return Username
    TerminalUI.ShowNotice("Set a username in Settings first.", "red")
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
            TerminalUI.ShowNotice(f"Could not create room: {Error}", "red")
        except Exception as Error:
            Host.Stop()
            TerminalUI.ShowNotice(f"Room error: {Error}", "red")

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

        RoomText = TerminalUI.AskText("Enter Room Number", "")
        if RoomText is None:
            return True

        RoomNumber = ParseRoomNumber(RoomText)
        if RoomNumber is None:
            TerminalUI.ShowNotice("Invalid room number. Example: 54321", "red")
            return True

        TerminalUI.ShowNotice("Searching for room on local network...", "cyan", 0.8)
        HostIp = FindRoomOnLan(RoomNumber)
        if not HostIp:
            TerminalUI.ShowNotice(
                f"Room {RoomNumber} not found. Check the number and Wi‑Fi/LAN.",
                "red",
            )
            return True

        Client = CampaignClient(HostIp, RoomNumber, PlayerUsername)
        Client.RunSession()
        return True


class BackAction(MenuAction):
    """Return to the parent menu without exiting the application."""

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
    """Ask the user to start as host or player."""

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
    """Prompt for and save the player's display name."""

    @property
    def Label(self) -> str:
        return "Set Username"

    @property
    def Icon(self) -> str:
        return "👤"

    def Execute(self) -> bool:
        from settings import UserSettings

        Current = UserSettings.Get()
        TerminalUI.Clear()
        questionary.print("")
        questionary.print("  Set Username", style="bold fg:magenta")
        questionary.print(
            f"  Current: {Current.UsernameDisplay}",
            style="fg:#888888 italic",
        )
        questionary.print("")

        NewName = TerminalUI.AskText("Enter your username", Current.Username)
        if NewName is None:
            return True

        NewName = NewName.strip()
        if not NewName:
            TerminalUI.ShowNotice("Username cannot be empty.", "red")
            return True

        Current.Username = NewName
        Current.Save()
        TerminalUI.ShowNotice(f"Username saved: {NewName}", "green")
        return True


class SettingsAction(MenuAction):
    """Application preferences submenu."""

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
    """Leaves the application."""

    @property
    def Label(self) -> str:
        return "Exit"

    @property
    def Icon(self) -> str:
        return "🚪"

    def Execute(self) -> bool:
        TerminalUI.PrintFarewell("Goodbye, adventurer!")
        return False
