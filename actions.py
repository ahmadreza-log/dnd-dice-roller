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


def _RequireHostIp() -> str | None:
    """Return LAN host IP from settings, or prompt once and save."""
    from settings import UserSettings

    Current = UserSettings.Get()
    if Current.HostIp:
        return Current.HostIp

    from network import GetLanIp

    Prompted = TerminalUI.AskText(
        "Host IP on your network (Settings → Set Host IP)",
        GetLanIp(),
    )
    if Prompted is None:
        return None

    Prompted = Prompted.strip()
    if not Prompted:
        TerminalUI.ShowNotice("Host IP cannot be empty.", "red")
        return None

    Current.HostIp = Prompted
    Current.Save()
    return Current.HostIp


class StartAsHostAction(MenuAction):
    """Start a TCP campaign server and wait for players to connect."""

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
            from settings import UserSettings

            Settings = UserSettings.Get()
            Settings.HostIp = Host.LanIp
            Settings.Save()
            Host.RunSession()
        except OSError as Error:
            TerminalUI.ShowNotice(f"Could not start host: {Error}", "red")

        return True


class StartAsPlayerAction(MenuAction):
    """Connect to a host campaign on the LAN."""

    @property
    def Label(self) -> str:
        return "As Player"

    @property
    def Icon(self) -> str:
        return "🎲"

    def Execute(self) -> bool:
        from network import CampaignClient, ResolveCampaignConnection

        PlayerUsername = _RequireUsername()
        if not PlayerUsername:
            return True

        HostIp = _RequireHostIp()
        if not HostIp:
            return True

        PortText = TerminalUI.AskText(
            "Campaign port (from host)",
            "",
        )
        if PortText is None:
            return True

        Parsed = ResolveCampaignConnection(PortText, HostIp)
        if Parsed is None:
            TerminalUI.ShowNotice(
                "Invalid port. Example: 54321",
                "red",
            )
            return True

        HostIp, Port = Parsed
        Client = CampaignClient(HostIp, Port, PlayerUsername)
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


class SetHostIpAction(MenuAction):
    """Save the campaign host IPv4 address for port-only joins."""

    @property
    def Label(self) -> str:
        return "Set Host IP"

    @property
    def Icon(self) -> str:
        return "🌐"

    def Execute(self) -> bool:
        from network import GetLanIp
        from settings import UserSettings

        Current = UserSettings.Get()
        TerminalUI.Clear()
        questionary.print("")
        questionary.print("  Set Host IP", style="bold fg:magenta")
        questionary.print(
            f"  Current: {Current.HostIpDisplay}",
            style="fg:#888888 italic",
        )
        questionary.print("")

        NewIp = TerminalUI.AskText("Host IP on your network", Current.HostIp or GetLanIp())
        if NewIp is None:
            return True

        NewIp = NewIp.strip()
        if not NewIp:
            TerminalUI.ShowNotice("Host IP cannot be empty.", "red")
            return True

        Current.HostIp = NewIp
        Current.Save()
        TerminalUI.ShowNotice(f"Host IP saved: {NewIp}", "green")
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
                SetHostIpAction(),
                BackAction(),
            ],
            Subtitle=f"User: {Current.UsernameDisplay}  |  Host: {Current.HostIpDisplay}",
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
