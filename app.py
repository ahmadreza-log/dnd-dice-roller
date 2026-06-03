from actions import ExitAction, MenuAction, SettingsAction, StartAction
from menu import Menu
from ui import AppUI


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
