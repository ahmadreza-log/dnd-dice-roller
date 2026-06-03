from actions import MenuAction


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
        """Show this menu in the main window."""
        from app import Application

        Application.Instance().ShowMenu(self)

    def RunUntilBack(self) -> bool:
        """Open submenu; Back returns to parent without quitting the app."""
        self.Open()
        return True
