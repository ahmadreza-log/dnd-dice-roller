from actions import MenuAction
from terminal import TerminalUI


class Menu:
    """Interactive menu powered by questionary (arrow keys + Enter)."""

    def __init__(self, Title: str, Actions: list[MenuAction], Subtitle: str = "") -> None:
        self._Title = Title
        self._Subtitle = Subtitle
        self._Actions = Actions

    @property
    def Actions(self) -> list[MenuAction]:
        """Ordered list of menu actions."""
        return self._Actions

    def PromptChoice(self) -> MenuAction | None:
        """Show header and return the action the user picked (None if cancelled)."""
        TerminalUI.PrintHeader(self._Title, self._Subtitle)
        Question = self._Subtitle if self._Subtitle else "Choose an option"
        return TerminalUI.SelectAction(Question, self._Actions)

    def RunUntilBack(self) -> bool:
        """Loop until Back is chosen. Return False to exit the entire application."""
        while True:
            Selected = self.PromptChoice()
            if Selected is None:
                return True

            if Selected.IsBack:
                return True

            if not Selected.Execute():
                return False

        return True
