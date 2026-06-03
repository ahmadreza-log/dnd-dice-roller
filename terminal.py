import sys
import time

import questionary
from questionary import Style


class TerminalUI:
    """Questionary-based interactive terminal UI."""

    _Style: Style | None = None

    @classmethod
    def Enable(cls) -> None:
        """Load custom styles and UTF-8 output for emoji icons."""
        for Stream in (sys.stdout, sys.stderr):
            if hasattr(Stream, "reconfigure"):
                try:
                    Stream.reconfigure(encoding="utf-8")
                except Exception:
                    pass
        cls.GetStyle()

    @classmethod
    def GetStyle(cls) -> Style:
        """D&D-themed colors for questionary prompts."""
        if cls._Style is None:
            cls._Style = Style(
                [
                    ("qmark", "fg:cyan bold"),
                    ("question", "bold fg:cyan"),
                    ("answer", "fg:green bold"),
                    ("pointer", "fg:yellow bold"),
                    ("highlighted", "fg:yellow bold"),
                    ("selected", "fg:green bold"),
                    ("separator", "fg:#666666"),
                    ("instruction", "fg:#888888 italic"),
                    ("text", "fg:white"),
                ]
            )
        return cls._Style

    @classmethod
    def Clear(cls) -> None:
        """Clear the terminal so menus do not stack vertically."""
        if sys.platform == "win32":
            import os

            os.system("cls")
        else:
            print("\033[2J\033[H", end="")

    @classmethod
    def PrintHeader(cls, Title: str, Subtitle: str = "") -> None:
        """Simple title block above the selection list."""
        cls.Clear()
        questionary.print("")
        questionary.print(f"  {Title}", style="bold fg:cyan")
        if Subtitle:
            questionary.print(f"  {Subtitle}", style="fg:#888888 italic")
        questionary.print("")

    @classmethod
    def SelectAction(cls, Question: str, Actions: list) -> object | None:
        """Arrow-key menu; returns the chosen action object, or None on cancel."""
        Choices = []
        for Action in Actions:
            if Action.Icon:
                Title = f"  {Action.Icon}  {Action.Label}"
            else:
                Title = f"  {Action.Label}"
            Choices.append(questionary.Choice(title=Title, value=Action))

        return questionary.select(
            Question,
            choices=Choices,
            style=cls.GetStyle(),
            qmark=">",
            pointer=">",
            use_indicator=True,
            use_shortcuts=False,
        ).ask()

    @classmethod
    def ShowNotice(cls, Message: str, Color: str = "cyan", Seconds: float = 1.2) -> None:
        """Brief message before the next menu redraw."""
        cls.Clear()
        questionary.print("")
        questionary.print(f"  {Message}", style=f"bold fg:{Color}")
        questionary.print("")
        time.sleep(Seconds)

    @classmethod
    def PrintFarewell(cls, Message: str) -> None:
        cls.Clear()
        questionary.print("")
        questionary.print(f"  {Message}", style="bold fg:red")
        questionary.print("")

    @classmethod
    def PrintCancelled(cls) -> None:
        questionary.print("  Cancelled.", style="fg:#888888 italic")
