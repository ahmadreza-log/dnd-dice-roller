from actions import ExitAction, MenuAction, SettingsAction, StartAction
from menu import Menu
from terminal import TerminalUI


class Application:
    """Main program loop: show menu, handle choice, repeat until Exit."""

    def __init__(self, Menu: Menu) -> None:
        self._Menu = Menu

    @classmethod
    def CreateDefault(cls) -> "Application":
        """Build the app with the standard D&D dice roller menu."""
        TerminalUI.Enable()
        Actions: list[MenuAction] = [
            StartAction(),
            SettingsAction(),
            ExitAction(),
        ]
        MainMenu = Menu("D&D Dice Roller", Actions, Subtitle="Roll for initiative")
        return cls(MainMenu)

    def Run(self) -> None:
        """Run until the user selects Exit, cancels, or closes the terminal."""
        while True:
            Selected = self._Menu.PromptChoice()
            if Selected is None:
                TerminalUI.PrintCancelled()
                break
            if not Selected.Execute():
                break
