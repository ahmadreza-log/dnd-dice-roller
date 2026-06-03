import queue
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, E, END, EW, NSEW, NS, W, X

from dice import DICE_TYPES, MAX_DICE_PER_ROLL, DiceRoller
from gui_theme import (
    BG_CHAT_LOG,
    BOOT_CHAT_META,
    BOOT_CHAT_TITLE,
    BOOT_CHAT_USER,
    COLOR_CHAT,
    COLOR_ERROR,
    COLOR_JOIN,
    COLOR_LEAVE,
    COLOR_SYSTEM,
    FG_CHAT_DEFAULT,
    FONT_CHAT,
    FONT_CHAT_HEADER,
    FONT_UI,
    FONT_UI_BOLD,
)


@dataclass
class ChatLine:
    """One row in the chat log."""

    Kind: str
    Body: str


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
        self._Lines: list[ChatLine] = []
        self._RenderedCount = 0
        self._Window: ttk.Toplevel | None = None
        self._Log: tk.Text | None = None
        self._Entry: ttk.Entry | None = None

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

    def _FormatDisplay(self, Line: ChatLine) -> str:
        if Line.Kind == "join":
            return f"● {Line.Body}\n"
        if Line.Kind == "leave":
            return f"◌ {Line.Body}\n"
        if Line.Kind == "error":
            return f"! {Line.Body}\n"
        return f"{Line.Body}\n"

    def _TagForKind(self, Kind: str) -> str:
        return {
            "join": "join",
            "leave": "leave",
            "chat": "chat",
            "error": "error",
        }.get(Kind, "system")

    def _AppendNewLines(self) -> None:
        if not self._Log:
            return

        while self._RenderedCount < len(self._Lines):
            Line = self._Lines[self._RenderedCount]
            Tag = self._TagForKind(Line.Kind)
            self._Log.configure(state="normal")
            self._Log.insert(END, self._FormatDisplay(Line), Tag)
            self._Log.configure(state="disabled")
            self._Log.see(END)
            self._RenderedCount += 1

    def _PublishOutgoing(self, Text: str) -> None:
        """Send to the network; players echo locally as [Username] lines."""
        self._SendMessage(Text)
        if self._ShowLocalEcho:
            self._Lines.append(ChatLine("chat", f"[{self._Username}] {Text}"))
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

        Message = DiceRoller.RollAndFormat(DiceLabel, Sides, Count)
        self._PublishOutgoing(Message)

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

        LogFrame = ttk.Frame(Win, padding=(12, 6, 12, 6))
        LogFrame.grid(row=3, column=0, sticky=NSEW)
        LogFrame.grid_rowconfigure(0, weight=1)
        LogFrame.grid_columnconfigure(0, weight=1)

        Log = tk.Text(
            LogFrame,
            wrap="word",
            font=FONT_CHAT,
            state="disabled",
            bg=BG_CHAT_LOG,
            fg=FG_CHAT_DEFAULT,
            insertbackground=FG_CHAT_DEFAULT,
            selectbackground="#3d4f6f",
            selectforeground=FG_CHAT_DEFAULT,
            relief="flat",
            padx=10,
            pady=8,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#3d4658",
            highlightcolor="#5a9fd4",
        )
        Scroll = ttk.Scrollbar(LogFrame, orient="vertical", command=Log.yview)
        Log.configure(yscrollcommand=Scroll.set)
        Log.grid(row=0, column=0, sticky=NSEW)
        Scroll.grid(row=0, column=1, sticky=NS)

        Log.tag_configure("join", foreground=COLOR_JOIN, font=FONT_UI_BOLD)
        Log.tag_configure("leave", foreground=COLOR_LEAVE)
        Log.tag_configure("chat", foreground=COLOR_CHAT)
        Log.tag_configure("error", foreground=COLOR_ERROR, font=FONT_UI_BOLD)
        Log.tag_configure("system", foreground=COLOR_SYSTEM)
        self._Log = Log

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
