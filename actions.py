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


class StartAsHostAction(MenuAction):
    """Start a campaign as the host (socket server — planned)."""

    @property
    def Label(self) -> str:
        return "As Host"

    @property
    def Icon(self) -> str:
        return "👑"

    def Execute(self) -> bool:
        TerminalUI.ShowNotice("Starting as host... (coming soon)", "yellow")
        return True


class StartAsPlayerAction(MenuAction):
    """Start a session as a player (socket client — planned)."""

    @property
    def Label(self) -> str:
        return "As Player"

    @property
    def Icon(self) -> str:
        return "🎲"

    def Execute(self) -> bool:
        TerminalUI.ShowNotice("Starting as player... (coming soon)", "cyan")
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
