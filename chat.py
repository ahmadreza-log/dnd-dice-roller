import queue
from collections.abc import Callable
from dataclasses import dataclass

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, E, END, EW, NSEW, W, X

from chat_bubbles import ChatBubbleFeed
from dice import DICE_TYPES, MAX_DICE_PER_ROLL, DiceRollResult, DiceRoller
from network import JOIN_ANNOUNCEMENT_SUFFIX
from gui_theme import (
    BOOT_CHAT_META,
    BOOT_CHAT_TITLE,
    BOOT_CHAT_USER,
    FONT_CHAT_HEADER,
    FONT_UI,
    FONT_UI_BOLD,
)


@dataclass
class ChatLine:
    """One row in the chat log."""

    Kind: str
    Body: str
    Roll: DiceRollResult | None = None
    Username: str = ""


class CampaignChatWindow:
    """LAN chat in a themed window; messages update live."""

    _PollMs = 200

    def __init__(
        self,
        Parent: ttk.Window,
        Title: str,
        Username: str,
        EventQueue: queue.Queue[str],
        SendMessage: Callable[[str], None],
        HeaderLines: list[str] | None = None,
        OnLeave: Callable[[], None] | None = None,
        ShouldContinue: Callable[[], bool] | None = None,
        ShowLocalEcho: bool = True,
        PrivateDiceRolls: bool = False,
    ) -> None:
        self._Parent = Parent
        self._Title = Title
        self._Username = Username
        self._EventQueue = EventQueue
        self._SendMessage = SendMessage
        self._HeaderLines = HeaderLines or []
        self._OnLeave = OnLeave
        self._ShouldContinue = ShouldContinue
        self._ShowLocalEcho = ShowLocalEcho
        self._PrivateDiceRolls = PrivateDiceRolls
        self._Lines: list[ChatLine] = []
        self._RenderedCount = 0
        self._Window: ttk.Toplevel | None = None
        self._Feed: ChatBubbleFeed | None = None
        self._Entry: ttk.Entry | None = None

    def _ParseBracketChat(self, Text: str) -> ChatLine | None:
        if not Text.startswith("[") or "]" not in Text:
            return None

        BracketEnd = Text.index("]")
        Username = Text[1:BracketEnd].strip()
        Body = Text[BracketEnd + 1 :].strip()
        if not Username:
            return None

        return ChatLine("chat", Body, Username=Username)

    def _ParseJoinUsername(self, Text: str) -> str:
        Marker = f": {JOIN_ANNOUNCEMENT_SUFFIX}"
        if Marker in Text:
            return Text.split(":", 1)[0].strip()
        return ""

    def _ParseLeaveUsername(self, Text: str) -> str:
        Suffix = " left the campaign."
        if Text.endswith(Suffix):
            return Text[: -len(Suffix)].strip()
        return ""

    def _ClassifyIncoming(self, Raw: str) -> ChatLine:
        Text = Raw.strip()
        Lower = Text.lower()

        ParsedRoll = DiceRoller.ParseBracketedMessage(Text)
        if ParsedRoll is not None:
            Username, Roll = ParsedRoll
            return ChatLine("dice_roll", "", Roll=Roll, Username=Username)

        ParsedChat = self._ParseBracketChat(Text)
        if ParsedChat is not None:
            return ParsedChat

        if "adventurer joined" in Lower or "player joined" in Lower:
            return ChatLine("join", Text, Username=self._ParseJoinUsername(Text))
        if "left the campaign" in Lower or "player left" in Lower:
            return ChatLine("leave", Text, Username=self._ParseLeaveUsername(Text))
        if "disconnected" in Lower or "connection lost" in Lower:
            return ChatLine("error", Text)
        return ChatLine("system", Text)

    def _DrainNetworkEvents(self) -> None:
        while True:
            try:
                Raw = self._EventQueue.get_nowait()
            except queue.Empty:
                break
            self._Lines.append(self._ClassifyIncoming(Raw))

    def _AppendNewLines(self) -> None:
        if not self._Feed:
            return

        while self._RenderedCount < len(self._Lines):
            self._Feed.Append(self._Lines[self._RenderedCount])
            self._RenderedCount += 1

    def _PublishDiceRoll(self, Roll: DiceRollResult, Private: bool = False) -> None:
        if not Private:
            self._SendMessage(DiceRoller.FormatWireMessage(Roll))
        Kind = "private_dice_roll" if Private else "dice_roll"
        if Private or self._ShowLocalEcho:
            self._Lines.append(
                ChatLine(Kind, "", Roll=Roll, Username=self._Username)
            )
        self._AppendNewLines()

    def _PublishOutgoing(self, Text: str) -> None:
        """Send to the network; players echo locally as chat bubbles."""
        self._SendMessage(Text)
        if self._ShowLocalEcho:
            self._Lines.append(ChatLine("chat", Text, Username=self._Username))
        self._AppendNewLines()

    def _PromptDiceCount(self, DiceLabel: str) -> int | None:
        """Ask how many dice to roll; None if cancelled."""
        if not self._Window:
            return None

        Dialog = ttk.Toplevel(self._Window)
        Dialog.title(f"Roll {DiceLabel}")
        Dialog.transient(self._Window)
        Dialog.resizable(False, False)
        Dialog.minsize(340, 220)

        Result: list[int | None] = [None]

        Frame = ttk.Frame(Dialog, padding=20)
        Frame.pack(fill=BOTH, expand=True)
        Frame.grid_columnconfigure(0, weight=1)

        Row = 0
        ttk.Label(
            Frame,
            text=f"How many {DiceLabel} dice?",
            font=FONT_UI_BOLD,
            bootstyle=BOOT_CHAT_TITLE,
        ).grid(row=Row, column=0, sticky=W, pady=(0, 8))
        Row += 1

        InputRow = ttk.Frame(Frame)
        InputRow.grid(row=Row, column=0, sticky=EW)
        InputRow.grid_columnconfigure(0, weight=1)
        InputRow.grid_columnconfigure(1, weight=1)
        Row += 1

        Entry = ttk.Entry(InputRow, font=FONT_UI, bootstyle="light")
        Entry.grid(row=0, column=0, sticky=EW, padx=(0, 6), ipady=8)
        Entry.insert(0, "1")

        def Submit(_event=None) -> str:
            Raw = Entry.get().strip()
            if not Raw.isdigit():
                Hint.configure(text="Please enter a whole number.", bootstyle="danger")
                return "break"
            Count = int(Raw)
            if Count < 1 or Count > MAX_DICE_PER_ROLL:
                Hint.configure(
                    text=f"Use a number between 1 and {MAX_DICE_PER_ROLL}.",
                    bootstyle="danger",
                )
                return "break"
            Result[0] = Count
            Dialog.destroy()
            return "break"

        def Cancel(_event=None) -> None:
            Result[0] = None
            Dialog.destroy()

        SendBtn = ttk.Button(
            InputRow,
            text="Send",
            bootstyle="success",
            command=Submit,
        )
        SendBtn.grid(row=0, column=1, sticky=EW, ipady=8)

        Hint = ttk.Label(
            Frame,
            text=f"Count 1–{MAX_DICE_PER_ROLL} · Enter or Send",
            font=FONT_UI,
            bootstyle=BOOT_CHAT_META,
        )
        Hint.grid(row=Row, column=0, sticky=W, pady=(8, 0))
        Row += 1

        ttk.Button(
            Frame,
            text="Cancel",
            bootstyle="secondary",
            command=Cancel,
        ).grid(row=Row, column=0, sticky=EW, pady=(14, 0), ipady=6)

        Entry.bind("<Return>", Submit)
        Entry.bind("<KP_Enter>", Submit)
        Dialog.bind("<Return>", Submit)
        Dialog.bind("<KP_Enter>", Submit)
        Dialog.bind("<Escape>", lambda _e: Cancel())
        Dialog.protocol("WM_DELETE_WINDOW", Cancel)

        Dialog.update_idletasks()
        PosX = self._Window.winfo_rootx() + 80
        PosY = self._Window.winfo_rooty() + 120
        Dialog.geometry(f"340x220+{PosX}+{PosY}")
        Dialog.grab_set()
        Entry.focus_force()
        Entry.icursor(END)
        Entry.select_range(0, END)

        Dialog.wait_window()
        return Result[0]

    def _RollDice(self, DiceLabel: str, Sides: int) -> None:
        Count = self._PromptDiceCount(DiceLabel)
        if Count is None:
            return

        Result = DiceRoller.RollDice(DiceLabel, Sides, Count)
        self._PublishDiceRoll(Result, Private=self._PrivateDiceRolls)

    def _SendCurrent(self) -> None:
        if not self._Entry:
            return
        Text = self._Entry.get().strip()
        self._Entry.delete(0, END)
        if not Text:
            return
        if Text.lower() in ("/quit", "/exit", "/back", "/leave"):
            self._Close()
            return
        self._PublishOutgoing(Text)

    def _Poll(self) -> None:
        if not self._Window or not self._Window.winfo_exists():
            return

        if self._ShouldContinue is not None and not self._ShouldContinue():
            self._Close()
            return

        self._DrainNetworkEvents()
        self._AppendNewLines()
        self._Window.after(self._PollMs, self._Poll)

    def _Close(self) -> None:
        if self._Window and self._Window.winfo_exists():
            self._Window.destroy()
        self._Window = None
        self._Feed = None

    def _AutoSizeWindow(self) -> None:
        """Fit chat window to screen so input and send stay visible."""
        if not self._Window:
            return

        Win = self._Window
        Win.update_idletasks()

        ScreenW = Win.winfo_screenwidth()
        ScreenH = Win.winfo_screenheight()
        ParentW = max(self._Parent.winfo_width(), 480)
        ParentH = max(self._Parent.winfo_height(), 520)

        Width = min(max(ParentW, 520), int(ScreenW * 0.92))
        Height = min(max(ParentH + 100, 620), int(ScreenH * 0.88))

        PosX = max(0, self._Parent.winfo_rootx() + (self._Parent.winfo_width() - Width) // 2)
        PosY = max(0, self._Parent.winfo_rooty() + (self._Parent.winfo_height() - Height) // 2)

        if PosY + Height > ScreenH:
            PosY = max(0, ScreenH - Height - 24)
        if PosX + Width > ScreenW:
            PosX = max(0, ScreenW - Width - 24)

        Win.geometry(f"{Width}x{Height}+{PosX}+{PosY}")
        Win.minsize(480, 420)

    def _BuildWindow(self) -> None:
        Win = ttk.Toplevel(self._Parent)
        Win.title(self._Title)
        Win.transient(self._Parent)
        self._Window = Win

        Win.grid_columnconfigure(0, weight=1)
        Win.grid_rowconfigure(3, weight=1)

        TopBar = ttk.Frame(Win, padding=(14, 12, 14, 6))
        TopBar.grid(row=0, column=0, sticky=EW)
        TopBar.grid_columnconfigure(0, weight=1)

        ttk.Label(
            TopBar,
            text="Campaign Chat",
            font=FONT_CHAT_HEADER,
            bootstyle=BOOT_CHAT_TITLE,
        ).grid(row=0, column=0, sticky=W)

        ttk.Button(
            TopBar,
            text="Leave chat",
            bootstyle="danger-outline",
            command=self._Close,
            width=12,
        ).grid(row=0, column=1, sticky=E, padx=(12, 0))

        Header = ttk.Frame(Win, padding=(14, 0, 14, 8))
        Header.grid(row=1, column=0, sticky=EW)
        ttk.Label(
            Header,
            text=f"You: {self._Username}",
            font=FONT_UI_BOLD,
            bootstyle=BOOT_CHAT_USER,
        ).pack(anchor=W)
        for Line in self._HeaderLines:
            ttk.Label(
                Header,
                text=Line,
                font=FONT_UI,
                bootstyle=BOOT_CHAT_META,
            ).pack(anchor=W, pady=(3, 0))

        ttk.Separator(Win, bootstyle="light").grid(
            row=2, column=0, sticky=EW, padx=12, pady=(0, 4)
        )

        LogFrame = ttk.Frame(Win, padding=(4, 4, 4, 6))
        LogFrame.grid(row=3, column=0, sticky=NSEW)
        LogFrame.grid_rowconfigure(0, weight=1)
        LogFrame.grid_columnconfigure(0, weight=1)

        self._Feed = ChatBubbleFeed(LogFrame)
        self._Feed.SetSelfUsername(self._Username)

        DiceRow = ttk.Frame(Win, padding=(12, 6, 12, 4))
        DiceRow.grid(row=4, column=0, sticky=EW)
        for Column, (DiceLabel, Sides) in enumerate(DICE_TYPES):
            ttk.Button(
                DiceRow,
                text=DiceLabel,
                bootstyle="warning-outline",
                width=6,
                command=lambda L=DiceLabel, S=Sides: self._RollDice(L, S),
            ).grid(row=0, column=Column, padx=3, pady=2, sticky=EW)
            DiceRow.grid_columnconfigure(Column, weight=1)

        InputRow = ttk.Frame(Win, padding=(12, 8, 12, 14))
        InputRow.grid(row=5, column=0, sticky=EW)
        InputRow.grid_columnconfigure(0, weight=1)
        InputRow.grid_columnconfigure(1, weight=1)

        self._Entry = ttk.Entry(InputRow, font=FONT_UI, bootstyle="light")
        self._Entry.grid(row=0, column=0, sticky=EW, padx=(0, 6), ipady=8)
        self._Entry.bind("<Return>", lambda _e: self._SendCurrent())

        ttk.Button(
            InputRow,
            text="Send",
            bootstyle="success",
            command=self._SendCurrent,
        ).grid(row=0, column=1, sticky=EW, ipady=8)

        Win.protocol("WM_DELETE_WINDOW", self._Close)
        self._AutoSizeWindow()

    def Run(self) -> None:
        """Open chat and block until the window closes."""
        self._DrainNetworkEvents()
        self._BuildWindow()
        self._Lines.append(ChatLine("system", "You joined the chat."))
        self._AppendNewLines()

        assert self._Window is not None
        self._Window.after(80, self._AutoSizeWindow)
        self._Window.after(self._PollMs, self._Poll)
        self._Entry.focus_set()
        self._Parent.wait_window(self._Window)

        self._DrainNetworkEvents()
        if self._OnLeave:
            self._OnLeave()
