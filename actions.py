from abc import ABC, abstractmethod

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


class SettingsAction(MenuAction):
    """Application preferences (planned)."""

    @property
    def Label(self) -> str:
        return "Settings"

    @property
    def Icon(self) -> str:
        return "⚙️"

    def Execute(self) -> bool:
        TerminalUI.ShowNotice("Settings... (coming soon)", "magenta")
        return True


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
