import queue
import threading
import time
from collections.abc import Callable

import questionary


class CampaignChatRoom:
    """Live chat UI: prints events while the user types (no disconnect)."""

    def __init__(
        self,
        Title: str,
        Username: str,
        EventQueue: queue.Queue[str],
        SendMessage: Callable[[str], None],
        HeaderLines: list[str] | None = None,
        OnLeave: Callable[[], None] | None = None,
        ShouldContinue: Callable[[], bool] | None = None,
    ) -> None:
        self._Title = Title
        self._Username = Username
        self._EventQueue = EventQueue
        self._SendMessage = SendMessage
        self._HeaderLines = HeaderLines or []
        self._OnLeave = OnLeave
        self._ShouldContinue = ShouldContinue
        self._Running = True

    def _PrintHeader(self) -> None:
        questionary.print("")
        questionary.print(f"  {self._Title}", style="bold fg:cyan")
        questionary.print(f"  You: {self._Username}", style="fg:white")
        for Line in self._HeaderLines:
            questionary.print(f"  {Line}", style="fg:#888888 italic")
        questionary.print("  Type a message and press Enter.", style="fg:#888888 italic")
        questionary.print("  Commands: /quit or /leave to exit chat.", style="fg:#888888 italic")
        questionary.print("")

    def _DrainEvents(self) -> None:
        while True:
            try:
                Event = self._EventQueue.get_nowait()
            except queue.Empty:
                break
            questionary.print(f"  {Event}", style="fg:cyan")

    def _InputLoop(self) -> None:
        while self._Running:
            try:
                Line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                self._Running = False
                break

            if not Line:
                continue

            if Line.lower() in ("/quit", "/exit", "/back", "/leave"):
                self._Running = False
                break

            self._SendMessage(Line)

    def Run(self) -> None:
        """Run chat until the user leaves or the connection ends."""
        self._PrintHeader()
        self._DrainEvents()

        InputThread = threading.Thread(target=self._InputLoop, daemon=True)
        InputThread.start()

        try:
            while self._Running:
                if self._ShouldContinue is not None and not self._ShouldContinue():
                    self._Running = False
                    break
                self._DrainEvents()
                time.sleep(0.15)
        except KeyboardInterrupt:
            self._Running = False

        self._DrainEvents()
        questionary.print("")
        questionary.print("  Left the chat.", style="fg:#888888 italic")
        questionary.print("")

        if self._OnLeave:
            self._OnLeave()
