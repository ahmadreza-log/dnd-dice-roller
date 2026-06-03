import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

import questionary


@dataclass
class ChatLine:
    """One row in the chat log."""

    Kind: str
    Body: str


class CampaignChatRoom:
    """LAN chat: messages appear live while you type at the bottom."""

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
        self._Lines: list[ChatLine] = []
        self._PrintedCount = 0
        self._InputQueue: queue.Queue[str | None] = queue.Queue()
        self._OutputLock = threading.Lock()

    def _ClassifyIncoming(self, Raw: str) -> tuple[str, str]:
        Text = Raw.strip()
        Lower = Text.lower()

        if "adventurer joined" in Lower or "player joined" in Lower:
            return "join", Text
        if "left the campaign" in Lower or "player left" in Lower:
            return "leave", Text
        if Text.startswith("[") and "]" in Text:
            return "chat", Text
        if "disconnected" in Lower or "connection lost" in Lower:
            return "error", Text
        return "system", Text

    def _DrainNetworkEvents(self) -> None:
        while True:
            try:
                Raw = self._EventQueue.get_nowait()
            except queue.Empty:
                break
            Kind, Body = self._ClassifyIncoming(Raw)
            self._Lines.append(ChatLine(Kind, Body))

    def _AddSelfMessage(self, Text: str) -> None:
        self._Lines.append(ChatLine("self", Text))

    def _PrintLine(self, Line: ChatLine) -> None:
        with self._OutputLock:
            if Line.Kind == "join":
                questionary.print(f"  ● {Line.Body}", style="bold fg:green")
            elif Line.Kind == "leave":
                questionary.print(f"  ◌ {Line.Body}", style="fg:yellow")
            elif Line.Kind == "chat":
                questionary.print(f"  {Line.Body}", style="fg:white")
            elif Line.Kind == "self":
                questionary.print(f"  › You: {Line.Body}", style="bold fg:magenta")
            elif Line.Kind == "error":
                questionary.print(f"  ! {Line.Body}", style="bold fg:red")
            else:
                questionary.print(f"  {Line.Body}", style="fg:#888888 italic")

    def _PrintNewLines(self) -> None:
        while self._PrintedCount < len(self._Lines):
            self._PrintLine(self._Lines[self._PrintedCount])
            self._PrintedCount += 1

    def _PrintHeader(self) -> None:
        from terminal import TerminalUI

        TerminalUI.Clear()
        with self._OutputLock:
            questionary.print("")
            questionary.print("  ─── Campaign Chat ───", style="bold fg:cyan")
            questionary.print(f"  {self._Title}", style="fg:cyan")
            questionary.print(f"  You: {self._Username}", style="fg:white")
            for Line in self._HeaderLines:
                questionary.print(f"  {Line}", style="fg:#888888 italic")
            questionary.print(
                "  Messages appear automatically.  /leave = exit",
                style="fg:#888888 italic",
            )
            questionary.print("")

    def _InputLoop(self) -> None:
        """Read lines in the background so the network can still print."""
        while self._Running:
            if self._ShouldContinue is not None and not self._ShouldContinue():
                self._InputQueue.put(None)
                return

            try:
                with self._OutputLock:
                    questionary.print("", style="")
                Line = input("  Message: ")
            except (EOFError, KeyboardInterrupt):
                self._InputQueue.put(None)
                return

            self._InputQueue.put(Line)

    def _HandleSubmittedLine(self, Text: str | None) -> None:
        if Text is None:
            self._Running = False
            return

        Text = Text.strip()
        if Text.lower() in ("/quit", "/exit", "/back", "/leave"):
            self._Running = False
            return

        if not Text:
            return

        self._SendMessage(Text)
        self._AddSelfMessage(Text)
        self._PrintNewLines()

    def Run(self) -> None:
        """Poll network messages while waiting for input at the bottom."""
        self._DrainNetworkEvents()
        self._PrintHeader()
        self._AddSelfMessage("You joined the chat.")
        self._PrintNewLines()

        InputThread = threading.Thread(target=self._InputLoop, daemon=True)
        InputThread.start()

        try:
            while self._Running:
                if self._ShouldContinue is not None and not self._ShouldContinue():
                    self._Running = False
                    break

                self._DrainNetworkEvents()
                self._PrintNewLines()

                try:
                    Submitted = self._InputQueue.get(timeout=0.2)
                except queue.Empty:
                    continue

                self._HandleSubmittedLine(Submitted)
        except KeyboardInterrupt:
            self._Running = False

        self._DrainNetworkEvents()
        self._PrintNewLines()

        with self._OutputLock:
            questionary.print("")
            questionary.print("  Left the chat.", style="fg:#888888 italic")
            questionary.print("")

        if self._OnLeave:
            self._OnLeave()
