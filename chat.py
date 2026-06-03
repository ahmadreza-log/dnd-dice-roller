"""Campaign chat: player colors, bubble feed, and chat window."""

import queue
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from tkinter import scrolledtext

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, E, END, EW, NSEW, W, X, Y

from dice import DICE_TYPES, MAX_DICE_PER_ROLL, DiceRollResult, DiceRoller
from network import DM_DISPLAY_NAME, JOIN_ANNOUNCEMENT_SUFFIX, WHISPER_LOG_PREFIX
from ui import (
    BG_CHAT_LOG,
    BOOT_CHAT_META,
    BOOT_CHAT_TITLE,
    BOOT_CHAT_USER,
    BUBBLE_MAX_WIDTH,
    BUBBLE_PAD_X,
    BUBBLE_PAD_Y,
    BUBBLE_RADIUS,
    BUBBLE_ROW_PAD_Y,
    BUBBLE_SIDE_MARGIN,
    COLOR_BUBBLE_ERROR,
    COLOR_BUBBLE_ERROR_TEXT,
    COLOR_BUBBLE_LEAVE,
    COLOR_BUBBLE_LEAVE_TEXT,
    COLOR_BUBBLE_SYSTEM,
    COLOR_BUBBLE_SYSTEM_TEXT,
    COLOR_DICE_NAT1,
    COLOR_DICE_NAT20,
    COLOR_DICE_TOTAL,
    COLOR_DICE_VALUE,
    FONT_BUBBLE_META,
    FONT_BUBBLE_NAME,
    FONT_BUBBLE_TEXT,
    FONT_CHAT_HEADER,
    FONT_DICE_LABEL,
    FONT_DICE_TOTAL,
    FONT_DICE_VALUE,
    FONT_UI,
    FONT_UI_BOLD,
)

# ---------------------------------------------------------------------------
# Per-player bubble colors
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlayerColorScheme:
    """Background and text colors tuned for contrast (light text on dark fill)."""

    Bg: str
    Text: str
    Name: str
    DiceLabel: str = "#ffe08a"
    DiceSep: str = "#c5cedd"


# DM always uses the royal purple scheme.
DM_COLOR_SCHEME = PlayerColorScheme(
    Bg="#3a2d5a",
    Text="#f7f2ff",
    Name="#d4b8ff",
    DiceLabel="#ffe08a",
    DiceSep="#c8bddf",
)

# Hidden DM rolls: deeper fill, same accent family.
PRIVATE_ROLL_SCHEME = PlayerColorScheme(
    Bg="#2a2040",
    Text="#f3eaff",
    Name="#c9a8ff",
    DiceLabel="#e9a8ff",
    DiceSep="#b8a8cf",
)

WHISPER_SCHEME = PlayerColorScheme(
    Bg="#3d2a4a",
    Text="#fce8ff",
    Name="#e8a8ff",
)

DM_WHISPER_COMMAND = "/dm"

# Rotating palette for adventurers (each pair tested for contrast on #0e1621).
PLAYER_COLOR_PALETTE: list[PlayerColorScheme] = [
    PlayerColorScheme("#1a3d5c", "#f2f8ff", "#7ec8ff"),
    PlayerColorScheme("#1a4a38", "#effef5", "#72e8a8"),
    PlayerColorScheme("#4a2a52", "#fdf2ff", "#e2a8ff"),
    PlayerColorScheme("#5a3a18", "#fff8ec", "#ffc966"),
    PlayerColorScheme("#5a2438", "#fff2f6", "#ff93b8"),
    PlayerColorScheme("#164650", "#effcff", "#66d9ef"),
    PlayerColorScheme("#3a4220", "#f8fbe8", "#d8e878"),
    PlayerColorScheme("#2a3550", "#f0f4fa", "#a8bce8"),
    PlayerColorScheme("#4a2020", "#fff0f0", "#ff9898"),
    PlayerColorScheme("#1a4548", "#ecfcfc", "#6ee7e7"),
]


class PlayerColorRegistry:
    """Assign and remember a stable color scheme for each username."""

    def __init__(self) -> None:
        self._Schemes: dict[str, PlayerColorScheme] = {}
        self._NextPaletteIndex = 0

    def Register(self, Username: str) -> PlayerColorScheme:
        Clean = Username.strip()
        if not Clean:
            return PLAYER_COLOR_PALETTE[0]

        Existing = self._Schemes.get(Clean)
        if Existing is not None:
            return Existing

        if Clean == DM_DISPLAY_NAME:
            Scheme = DM_COLOR_SCHEME
        else:
            Scheme = PLAYER_COLOR_PALETTE[
                self._NextPaletteIndex % len(PLAYER_COLOR_PALETTE)
            ]
            self._NextPaletteIndex += 1

        self._Schemes[Clean] = Scheme
        return Scheme

    def Get(self, Username: str) -> PlayerColorScheme:
        return self.Register(Username)

    def Has(self, Username: str) -> bool:
        return Username.strip() in self._Schemes


@dataclass
class ChatLine:
    """One row in the chat log."""

    Kind: str
    Body: str
    Roll: DiceRollResult | None = None
    Username: str = ""


class RoomSessionLog:
    """Timestamped plain-text log for the current campaign room."""

    def __init__(self) -> None:
        self._Entries: list[str] = []

    def Append(self, Message: str) -> None:
        Text = Message.strip()
        if not Text:
            return
        Stamp = datetime.now().strftime("%H:%M:%S")
        self._Entries.append(f"[{Stamp}] {Text}")

    @property
    def Count(self) -> int:
        return len(self._Entries)

    def EntryAt(self, Index: int) -> str:
        return self._Entries[Index]

    def Entries(self) -> list[str]:
        return list(self._Entries)


FONT_ROOM_LOG = ("Consolas", 10)
FG_ROOM_LOG = "#c5d0de"


# ---------------------------------------------------------------------------
# Telegram-style bubbles
# ---------------------------------------------------------------------------

def _DrawRoundRect(
    Canvas: tk.Canvas,
    X1: int,
    Y1: int,
    X2: int,
    Y2: int,
    Radius: int,
    Fill: str,
    Tag: str = "bubble_shape",
) -> None:
    Canvas.create_rectangle(
        X1 + Radius,
        Y1,
        X2 - Radius,
        Y2,
        fill=Fill,
        outline=Fill,
        tags=Tag,
    )
    Canvas.create_rectangle(
        X1,
        Y1 + Radius,
        X2,
        Y2 - Radius,
        fill=Fill,
        outline=Fill,
        tags=Tag,
    )
    Canvas.create_arc(
        X1,
        Y1,
        X1 + 2 * Radius,
        Y1 + 2 * Radius,
        start=90,
        extent=90,
        fill=Fill,
        outline=Fill,
        tags=Tag,
        style="pieslice",
    )
    Canvas.create_arc(
        X2 - 2 * Radius,
        Y1,
        X2,
        Y1 + 2 * Radius,
        start=0,
        extent=90,
        fill=Fill,
        outline=Fill,
        tags=Tag,
        style="pieslice",
    )
    Canvas.create_arc(
        X1,
        Y2 - 2 * Radius,
        X1 + 2 * Radius,
        Y2,
        start=180,
        extent=90,
        fill=Fill,
        outline=Fill,
        tags=Tag,
        style="pieslice",
    )
    Canvas.create_arc(
        X2 - 2 * Radius,
        Y2 - 2 * Radius,
        X2,
        Y2,
        start=270,
        extent=90,
        fill=Fill,
        outline=Fill,
        tags=Tag,
        style="pieslice",
    )


class _BubbleCanvas(tk.Canvas):
    """Canvas that wraps content in a solid rounded background (no border stroke)."""

    def __init__(self, Parent: tk.Misc, BubbleBg: str) -> None:
        super().__init__(
            Parent,
            bg=BG_CHAT_LOG,
            highlightthickness=0,
            borderwidth=0,
        )
        self._BubbleBg = BubbleBg
        self._Inner = tk.Frame(self, bg=BubbleBg)
        self._WindowId = self.create_window(0, 0, window=self._Inner, anchor="nw")

    @property
    def Inner(self) -> tk.Frame:
        return self._Inner

    def Finalize(self, MaxWidth: int = BUBBLE_MAX_WIDTH) -> None:
        Wrap = MaxWidth - 2 * BUBBLE_PAD_X
        for Child in self._Inner.winfo_children():
            if isinstance(Child, tk.Label):
                Child.configure(wraplength=Wrap)

        self._Inner.update_idletasks()
        InnerW = min(max(self._Inner.winfo_reqwidth(), 36), MaxWidth)
        InnerH = self._Inner.winfo_reqheight()
        TotalW = InnerW + 2 * BUBBLE_PAD_X
        TotalH = InnerH + 2 * BUBBLE_PAD_Y

        self.delete("bubble_shape")
        _DrawRoundRect(self, 0, 0, TotalW, TotalH, BUBBLE_RADIUS, self._BubbleBg)
        self.tag_lower("bubble_shape")
        self.configure(width=TotalW, height=TotalH)
        self.coords(self._WindowId, BUBBLE_PAD_X, BUBBLE_PAD_Y)


class ChatBubbleFeed:
    """Scrollable message list with left/right/center Telegram-style bubbles."""

    def __init__(self, Parent: tk.Misc) -> None:
        self._SelfUsername = ""
        self._Colors = PlayerColorRegistry()

        Shell = tk.Frame(Parent, bg=BG_CHAT_LOG)
        Shell.pack(fill="both", expand=True)

        self._Canvas = tk.Canvas(
            Shell,
            bg=BG_CHAT_LOG,
            highlightthickness=0,
            borderwidth=0,
        )
        Scroll = ttk.Scrollbar(Shell, orient="vertical", command=self._Canvas.yview)
        self._Canvas.configure(yscrollcommand=Scroll.set)
        Scroll.pack(side="right", fill="y")
        self._Canvas.pack(side="left", fill="both", expand=True)

        self._Feed = tk.Frame(self._Canvas, bg=BG_CHAT_LOG)
        self._WindowId = self._Canvas.create_window((0, 0), window=self._Feed, anchor="nw")
        self._Feed.bind(
            "<Configure>",
            lambda _e: self._Canvas.configure(scrollregion=self._Canvas.bbox("all")),
        )
        self._Canvas.bind(
            "<Configure>",
            lambda e: self._Canvas.itemconfigure(self._WindowId, width=e.width),
        )

        for Widget in (self._Canvas, self._Feed):
            Widget.bind("<Enter>", self._BindWheel, add="+")
            Widget.bind("<Leave>", self._UnbindWheel, add="+")

    def _BindWheel(self, _event: tk.Event) -> None:
        self._Canvas.bind_all("<MouseWheel>", self._OnWheel)

    def _UnbindWheel(self, _event: tk.Event) -> None:
        self._Canvas.unbind_all("<MouseWheel>")

    def _OnWheel(self, Event: tk.Event) -> None:
        self._Canvas.yview_scroll(int(-1 * (Event.delta / 120)), "units")

    def SetSelfUsername(self, Username: str) -> None:
        self._SelfUsername = Username.strip()
        if self._SelfUsername:
            self._Colors.Register(self._SelfUsername)

    def ScrollToBottom(self) -> None:
        self._Canvas.update_idletasks()
        self._Canvas.yview_moveto(1.0)

    def Append(self, Line: ChatLine) -> None:
        if Line.Kind in ("dice_roll", "private_dice_roll") and Line.Roll is not None:
            self._AppendDiceRoll(
                Line.Username,
                Line.Roll,
                Private=Line.Kind == "private_dice_roll",
            )
            return

        Handlers = {
            "chat": self._AppendChat,
            "whisper_to_dm": self._AppendWhisperToDm,
            "whisper_from_player": self._AppendWhisperFromPlayer,
            "system": lambda L: self._AppendCenter(
                L.Body, COLOR_BUBBLE_SYSTEM, COLOR_BUBBLE_SYSTEM_TEXT
            ),
            "join": self._AppendJoin,
            "leave": self._AppendLeave,
            "error": lambda L: self._AppendCenter(
                f"! {L.Body}", COLOR_BUBBLE_ERROR, COLOR_BUBBLE_ERROR_TEXT
            ),
        }
        Handler = Handlers.get(Line.Kind)
        if Handler:
            Handler(Line)

    def _AddRow(self, Align: str) -> tk.Frame:
        Row = tk.Frame(self._Feed, bg=BG_CHAT_LOG)
        Row.pack(fill="x", padx=6, pady=BUBBLE_ROW_PAD_Y)
        Row.columnconfigure(0, weight=1)
        Row.columnconfigure(1, weight=0)
        Row.columnconfigure(2, weight=1)

        if Align == "right":
            Column, Sticky = 2, "e"
            PadX = (BUBBLE_SIDE_MARGIN, 8)
        elif Align == "center":
            Column, Sticky = 1, "n"
            PadX = (12, 12)
        else:
            Column, Sticky = 0, "w"
            PadX = (8, BUBBLE_SIDE_MARGIN)

        Slot = tk.Frame(Row, bg=BG_CHAT_LOG)
        Slot.grid(row=0, column=Column, sticky=Sticky, padx=PadX)
        return Slot

    def _MakeBubble(self, Parent: tk.Misc, BubbleBg: str) -> _BubbleCanvas:
        Bubble = _BubbleCanvas(Parent, BubbleBg)
        Bubble.pack()
        return Bubble

    def _PlayerAlign(self, Username: str) -> str:
        return "right" if Username == self._SelfUsername else "left"

    def _MakePlayerBlock(
        self,
        Slot: tk.Frame,
        Username: str,
        Scheme: PlayerColorScheme,
        NameSuffix: str = "",
    ) -> _BubbleCanvas:
        """Stack username above the bubble, outside the rounded background."""
        Align = self._PlayerAlign(Username)
        Anchor = "e" if Align == "right" else "w"

        Block = tk.Frame(Slot, bg=BG_CHAT_LOG)
        Block.pack(anchor=Anchor)

        DisplayName = Username
        if NameSuffix:
            DisplayName = f"{Username}{NameSuffix}"

        tk.Label(
            Block,
            text=DisplayName,
            font=FONT_BUBBLE_NAME,
            fg=Scheme.Name,
            bg=BG_CHAT_LOG,
            anchor=Anchor,
        ).pack(anchor=Anchor, pady=(0, 5))

        Bubble = self._MakeBubble(Block, Scheme.Bg)
        Bubble.pack(anchor=Anchor)
        return Bubble

    def _AppendCenter(self, Text: str, BubbleBg: str, TextColor: str) -> None:
        Slot = self._AddRow("center")
        Bubble = self._MakeBubble(Slot, BubbleBg)
        tk.Label(
            Bubble.Inner,
            text=Text,
            font=FONT_BUBBLE_META,
            fg=TextColor,
            bg=BubbleBg,
            justify="center",
        ).pack(anchor="center")
        Bubble.Finalize(max(BUBBLE_MAX_WIDTH // 2, 180))
        self.ScrollToBottom()

    def _AppendJoin(self, Line: ChatLine) -> None:
        Username = Line.Username.strip()
        if Username:
            Scheme = self._Colors.Register(Username)
            self._AppendCenter(
                f"● {Username} joined the campaign",
                Scheme.Bg,
                Scheme.Text,
            )
        else:
            self._AppendCenter(f"● {Line.Body}", COLOR_BUBBLE_SYSTEM, COLOR_BUBBLE_SYSTEM_TEXT)

    def _AppendLeave(self, Line: ChatLine) -> None:
        Username = Line.Username.strip()
        if Username and self._Colors.Has(Username):
            Scheme = self._Colors.Get(Username)
            self._AppendCenter(
                f"◌ {Username} left the campaign",
                Scheme.Bg,
                Scheme.Text,
            )
        else:
            self._AppendCenter(
                f"◌ {Line.Body}",
                COLOR_BUBBLE_LEAVE,
                COLOR_BUBBLE_LEAVE_TEXT,
            )

    def _AppendChat(self, Line: ChatLine) -> None:
        if not Line.Username:
            self._AppendCenter(Line.Body, COLOR_BUBBLE_SYSTEM, COLOR_BUBBLE_SYSTEM_TEXT)
            return

        Scheme = self._Colors.Get(Line.Username)
        Slot = self._AddRow(self._PlayerAlign(Line.Username))
        Bubble = self._MakePlayerBlock(Slot, Line.Username, Scheme)

        tk.Label(
            Bubble.Inner,
            text=Line.Body,
            font=FONT_BUBBLE_TEXT,
            fg=Scheme.Text,
            bg=Scheme.Bg,
            justify="left",
            anchor="w",
        ).pack(anchor="w")

        Bubble.Finalize()
        self.ScrollToBottom()

    def _DiceValueColor(self, Roll: DiceRollResult, Value: int) -> str:
        if Roll.IsNat20(Value):
            return COLOR_DICE_NAT20
        if Roll.IsNat1(Value):
            return COLOR_DICE_NAT1
        return COLOR_DICE_VALUE

    def _AppendDiceSegment(
        self,
        Parent: tk.Frame,
        Text: str,
        BubbleBg: str,
        Font: tuple,
        Fg: str,
    ) -> None:
        tk.Label(
            Parent,
            text=Text,
            font=Font,
            fg=Fg,
            bg=BubbleBg,
        ).pack(side="left")

    def _AppendDiceRoll(
        self,
        Username: str,
        Roll: DiceRollResult,
        Private: bool = False,
    ) -> None:
        if Private:
            Scheme = PRIVATE_ROLL_SCHEME
            NameSuffix = "  🔒"
        else:
            Scheme = self._Colors.Get(Username)
            NameSuffix = ""

        Slot = self._AddRow(self._PlayerAlign(Username))
        Bubble = self._MakePlayerBlock(Slot, Username, Scheme, NameSuffix=NameSuffix)
        Inner = Bubble.Inner
        BubbleBg = Scheme.Bg
        LabelColor = Scheme.DiceLabel
        TextBase = Scheme.Text
        SepColor = Scheme.DiceSep

        if Roll.Count == 1:
            Line = tk.Frame(Inner, bg=BubbleBg)
            Line.pack(anchor="w")
            self._AppendDiceSegment(Line, "🎲  ", BubbleBg, FONT_DICE_LABEL, TextBase)
            self._AppendDiceSegment(Line, Roll.DiceLabel, BubbleBg, FONT_DICE_LABEL, LabelColor)
            self._AppendDiceSegment(Line, "   →   ", BubbleBg, FONT_UI, SepColor)
            Value = Roll.Rolls[0]
            self._AppendDiceSegment(
                Line,
                str(Value),
                BubbleBg,
                FONT_DICE_VALUE,
                self._DiceValueColor(Roll, Value),
            )
        else:
            HeaderLine = tk.Frame(Inner, bg=BubbleBg)
            HeaderLine.pack(anchor="w")
            self._AppendDiceSegment(HeaderLine, "🎲  ", BubbleBg, FONT_DICE_LABEL, TextBase)
            self._AppendDiceSegment(
                HeaderLine,
                f"{Roll.Count}×{Roll.DiceLabel}",
                BubbleBg,
                FONT_DICE_LABEL,
                LabelColor,
            )
            self._AppendDiceSegment(HeaderLine, "   →", BubbleBg, FONT_UI, SepColor)

            ValuesWrap = tk.Frame(Inner, bg=BubbleBg)
            ValuesWrap.pack(anchor="w", pady=(4, 0))

            ChunkSize = 6
            for ChunkStart in range(0, Roll.Count, ChunkSize):
                ValueRow = tk.Frame(ValuesWrap, bg=BubbleBg)
                ValueRow.pack(anchor="w", pady=(2, 0))
                Chunk = Roll.Rolls[ChunkStart : ChunkStart + ChunkSize]
                for Index, Value in enumerate(Chunk):
                    if Index > 0:
                        self._AppendDiceSegment(ValueRow, " + ", BubbleBg, FONT_UI, SepColor)
                    self._AppendDiceSegment(
                        ValueRow,
                        str(Value),
                        BubbleBg,
                        FONT_DICE_VALUE,
                        self._DiceValueColor(Roll, Value),
                    )

            TotalLine = tk.Frame(Inner, bg=BubbleBg)
            TotalLine.pack(anchor="w", pady=(6, 0))
            self._AppendDiceSegment(TotalLine, "=   ", BubbleBg, FONT_UI, SepColor)
            self._AppendDiceSegment(
                TotalLine,
                str(Roll.Total),
                BubbleBg,
                FONT_DICE_TOTAL,
                COLOR_DICE_TOTAL,
            )

        Bubble.Finalize()
        self.ScrollToBottom()

    def _AppendWhisperToDm(self, Line: ChatLine) -> None:
        Scheme = WHISPER_SCHEME
        Slot = self._AddRow("right")
        Bubble = self._MakePlayerBlock(Slot, Line.Username, Scheme, NameSuffix=" → DM")
        tk.Label(
            Bubble.Inner,
            text=f"🔒 {Line.Body}",
            font=FONT_BUBBLE_TEXT,
            fg=Scheme.Text,
            bg=Scheme.Bg,
            justify="left",
            anchor="w",
        ).pack(anchor="w")
        Bubble.Finalize()
        self.ScrollToBottom()

    def _AppendWhisperFromPlayer(self, Line: ChatLine) -> None:
        if not Line.Username:
            self._AppendCenter(
                f"🔒 {Line.Body}",
                WHISPER_SCHEME.Bg,
                WHISPER_SCHEME.Text,
            )
            return

        self._Colors.Register(Line.Username)
        Slot = self._AddRow("left")
        Bubble = self._MakePlayerBlock(
            Slot,
            Line.Username,
            WHISPER_SCHEME,
            NameSuffix=" 🔒",
        )
        tk.Label(
            Bubble.Inner,
            text=Line.Body,
            font=FONT_BUBBLE_TEXT,
            fg=WHISPER_SCHEME.Text,
            bg=WHISPER_SCHEME.Bg,
            justify="left",
            anchor="w",
        ).pack(anchor="w")
        Bubble.Finalize()
        self.ScrollToBottom()


# ---------------------------------------------------------------------------
# Campaign chat window
# ---------------------------------------------------------------------------


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
        SendWhisper: Callable[[str], None] | None = None,
    ) -> None:
        self._Parent = Parent
        self._Title = Title
        self._Username = Username
        self._EventQueue = EventQueue
        self._SendMessage = SendMessage
        self._SendWhisper = SendWhisper
        self._HeaderLines = HeaderLines or []
        self._OnLeave = OnLeave
        self._ShouldContinue = ShouldContinue
        self._ShowLocalEcho = ShowLocalEcho
        self._PrivateDiceRolls = PrivateDiceRolls
        self._Lines: list[ChatLine] = []
        self._RenderedCount = 0
        self._SessionLog = RoomSessionLog()
        self._LogWindow: ttk.Toplevel | None = None
        self._LogText: tk.Text | None = None
        self._LogRenderedCount = 0
        self._Window: ttk.Toplevel | None = None
        self._Feed: ChatBubbleFeed | None = None
        self._Entry: ttk.Entry | None = None

    @property
    def _CanWhisperToDm(self) -> bool:
        return (
            self._SendWhisper is not None
            and self._Username.strip() != DM_DISPLAY_NAME
        )

    def _IsDmCommand(self, Text: str) -> bool:
        Text = Text.strip()
        Lower = Text.lower()
        Prefix = DM_WHISPER_COMMAND
        if not Lower.startswith(Prefix):
            return False
        if len(Text) == len(Prefix):
            return True
        return Text[len(Prefix)] in (" ", ":", "\t")

    def _ParseDmCommand(self, Text: str) -> str:
        Text = Text.strip()
        Rest = Text[len(DM_WHISPER_COMMAND) :].strip()
        if Rest.startswith(":"):
            Rest = Rest[1:].strip()
        return Rest

    def _FormatLogMessage(self, Raw: str) -> str:
        Text = Raw.strip()
        if not Text:
            return ""

        if Text.startswith(WHISPER_LOG_PREFIX):
            Body = Text[len(WHISPER_LOG_PREFIX) :].strip()
            return f"🔒 whisper {Body}" if Body else "🔒 whisper"

        ParsedRoll = DiceRoller.ParseBracketedMessage(Text)
        if ParsedRoll is not None:
            Username, Roll = ParsedRoll
            return DiceRoller.FormatLogLine(Username, Roll)

        return Text

    def _RecordLog(self, Message: str) -> None:
        Text = self._FormatLogMessage(Message)
        if not Text:
            return
        self._SessionLog.Append(Text)
        self._SyncLogWindow()

    def _LogWindowOpen(self) -> bool:
        return (
            self._LogWindow is not None
            and self._LogText is not None
            and self._LogWindow.winfo_exists()
        )

    def _ReloadLogWindow(self) -> None:
        if not self._LogWindowOpen():
            return

        assert self._LogText is not None
        Content = "\n".join(self._SessionLog.Entries())
        self._LogText.configure(state=tk.NORMAL)
        self._LogText.delete("1.0", tk.END)
        if Content:
            self._LogText.insert("1.0", Content + "\n")
        self._LogText.configure(state=tk.DISABLED)
        self._LogText.see(tk.END)
        self._LogRenderedCount = self._SessionLog.Count

    def _SyncLogWindow(self) -> None:
        if not self._LogWindowOpen():
            return

        assert self._LogText is not None
        if self._LogRenderedCount > self._SessionLog.Count:
            self._ReloadLogWindow()
            return

        while self._LogRenderedCount < self._SessionLog.Count:
            Line = self._SessionLog.EntryAt(self._LogRenderedCount)
            self._LogText.configure(state=tk.NORMAL)
            self._LogText.insert(tk.END, Line + "\n")
            self._LogText.configure(state=tk.DISABLED)
            self._LogRenderedCount += 1

        self._LogText.see(tk.END)

    def _OpenRoomLog(self) -> None:
        if not self._Window or not self._Window.winfo_exists():
            return

        if self._LogWindowOpen():
            self._ReloadLogWindow()
            self._LogWindow.lift()
            self._LogWindow.focus_force()
            return

        LogWin = ttk.Toplevel(self._Window)
        LogWin.title("Room Log")
        LogWin.transient(self._Window)
        LogWin.minsize(480, 360)
        self._LogWindow = LogWin

        LogWin.grid_columnconfigure(0, weight=1)
        LogWin.grid_rowconfigure(0, weight=1)

        Body = ttk.Frame(LogWin, padding=(12, 12, 12, 12))
        Body.grid(row=0, column=0, sticky=NSEW)
        Body.grid_columnconfigure(0, weight=1)
        Body.grid_rowconfigure(1, weight=1)

        ttk.Label(
            Body,
            text="Session activity for this room (newest at bottom)",
            font=FONT_UI,
            bootstyle=BOOT_CHAT_META,
        ).grid(row=0, column=0, sticky=W, pady=(0, 8))

        LogText = scrolledtext.ScrolledText(
            Body,
            wrap=tk.WORD,
            font=FONT_ROOM_LOG,
            bg=BG_CHAT_LOG,
            fg=FG_ROOM_LOG,
            insertbackground=FG_ROOM_LOG,
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=10,
            height=18,
            width=72,
            state=tk.DISABLED,
        )
        LogText.grid(row=1, column=0, sticky=NSEW)
        self._LogText = LogText

        Actions = ttk.Frame(Body)
        Actions.grid(row=2, column=0, sticky=EW, pady=(10, 0))
        Actions.grid_columnconfigure(0, weight=1)

        ttk.Button(
            Actions,
            text="Close",
            bootstyle="secondary",
            command=self._CloseRoomLog,
            width=10,
        ).grid(row=0, column=1, sticky=E)

        LogWin.update_idletasks()
        ParentX = self._Window.winfo_rootx()
        ParentY = self._Window.winfo_rooty()
        ParentW = self._Window.winfo_width()
        LogWin.geometry(f"560x420+{ParentX + max(ParentW - 580, 24)}+{ParentY + 48}")
        LogWin.protocol("WM_DELETE_WINDOW", self._CloseRoomLog)

        self._LogRenderedCount = 0
        self._ReloadLogWindow()
        LogWin.lift()
        LogWin.focus_force()

    def _CloseRoomLog(self) -> None:
        if self._LogWindow and self._LogWindow.winfo_exists():
            self._LogWindow.destroy()
        self._LogWindow = None
        self._LogText = None
        self._LogRenderedCount = 0

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

        if Text.startswith(WHISPER_LOG_PREFIX):
            Body = Text[len(WHISPER_LOG_PREFIX) :].strip()
            ParsedWhisper = self._ParseBracketChat(Body)
            if ParsedWhisper is not None:
                return ChatLine(
                    "whisper_from_player",
                    ParsedWhisper.Body,
                    Username=ParsedWhisper.Username,
                )
            return ChatLine("whisper_from_player", Body)

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

    def _ShouldSkipNetworkSessionLog(self, Raw: str) -> bool:
        """Avoid duplicate log lines already recorded locally."""
        if not self._ShowLocalEcho:
            return False

        ParsedRoll = DiceRoller.ParseBracketedMessage(Raw.strip())
        if ParsedRoll is not None:
            Username, _Roll = ParsedRoll
            return Username == self._Username

        ParsedChat = self._ParseBracketChat(Raw.strip())
        if ParsedChat is not None and ParsedChat.Username == self._Username:
            return True

        return False

    def _DrainNetworkEvents(self) -> None:
        while True:
            try:
                Raw = self._EventQueue.get_nowait()
            except queue.Empty:
                break
            self._Lines.append(self._ClassifyIncoming(Raw))
            if not self._ShouldSkipNetworkSessionLog(Raw):
                self._RecordLog(Raw)

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
            self._RecordLog(
                DiceRoller.FormatLogLine(self._Username, Roll, Private=Private)
            )
        self._AppendNewLines()

    def _PublishOutgoing(self, Text: str) -> None:
        """Send to the network; players echo locally as chat bubbles."""
        self._SendMessage(Text)
        if self._ShowLocalEcho:
            self._Lines.append(ChatLine("chat", Text, Username=self._Username))
            self._RecordLog(f"[{self._Username}] {Text}")
        self._AppendNewLines()

    def _PublishWhisper(self, Text: str) -> None:
        """Send a private message to the DM; visible only to sender and host."""
        if not self._CanWhisperToDm or not self._SendWhisper:
            return

        Text = Text.strip()
        if not Text:
            return

        self._SendWhisper(Text)
        self._Lines.append(ChatLine("whisper_to_dm", Text, Username=self._Username))
        self._RecordLog(f"🔒 whisper to DM [{self._Username}]: {Text}")
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

    def _OpenWhisperDialog(self) -> None:
        if not self._Window or not self._CanWhisperToDm:
            return

        Dialog = ttk.Toplevel(self._Window)
        Dialog.title("Whisper to DM")
        Dialog.transient(self._Window)
        Dialog.resizable(False, False)
        Dialog.minsize(420, 240)

        Frame = ttk.Frame(Dialog, padding=20)
        Frame.pack(fill=BOTH, expand=True)
        Frame.grid_columnconfigure(0, weight=1)

        ttk.Label(
            Frame,
            text="Private message to the Dungeon Master",
            font=FONT_UI_BOLD,
            bootstyle=BOOT_CHAT_TITLE,
        ).grid(row=0, column=0, sticky=W, pady=(0, 4))

        ttk.Label(
            Frame,
            text="Only you and the DM will see this message.",
            font=FONT_UI,
            bootstyle=BOOT_CHAT_META,
        ).grid(row=1, column=0, sticky=W, pady=(0, 12))

        Entry = ttk.Entry(Frame, font=FONT_UI, bootstyle="light")
        Entry.grid(row=2, column=0, sticky=EW, ipady=8)

        Hint = ttk.Label(
            Frame,
            text="Enter to send · Esc to cancel",
            font=FONT_UI,
            bootstyle=BOOT_CHAT_META,
        )
        Hint.grid(row=3, column=0, sticky=W, pady=(8, 0))

        Actions = ttk.Frame(Frame)
        Actions.grid(row=4, column=0, sticky=EW, pady=(16, 0))
        Actions.grid_columnconfigure(0, weight=1)

        def Cancel(_event=None) -> None:
            Dialog.destroy()

        def Submit(_event=None) -> str:
            Text = Entry.get().strip()
            if not Text:
                Hint.configure(text="Write a message first.", bootstyle="danger")
                return "break"
            Dialog.destroy()
            self._PublishWhisper(Text)
            return "break"

        ttk.Button(
            Actions,
            text="Cancel",
            bootstyle="secondary",
            command=Cancel,
            width=10,
        ).grid(row=0, column=0, sticky=W)

        ttk.Button(
            Actions,
            text="Send whisper",
            bootstyle="info",
            command=Submit,
            width=14,
        ).grid(row=0, column=1, sticky=E)

        Entry.bind("<Return>", Submit)
        Entry.bind("<KP_Enter>", Submit)
        Dialog.bind("<Escape>", lambda _e: Cancel())
        Dialog.protocol("WM_DELETE_WINDOW", Cancel)

        Dialog.update_idletasks()
        PosX = self._Window.winfo_rootx() + 60
        PosY = self._Window.winfo_rooty() + 100
        Dialog.geometry(f"420x240+{PosX}+{PosY}")
        Dialog.grab_set()
        Entry.focus_force()

        Dialog.wait_window()

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
        if self._CanWhisperToDm and self._IsDmCommand(Text):
            WhisperText = self._ParseDmCommand(Text)
            if WhisperText:
                self._PublishWhisper(WhisperText)
            else:
                self._OpenWhisperDialog()
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
        if self._LogWindowOpen():
            self._SyncLogWindow()
        self._Window.after(self._PollMs, self._Poll)

    def _Close(self) -> None:
        self._CloseRoomLog()
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
            text="Room Log",
            bootstyle="info-outline",
            command=self._OpenRoomLog,
            width=10,
        ).grid(row=0, column=1, sticky=E, padx=(12, 0))

        ttk.Button(
            TopBar,
            text="Leave chat",
            bootstyle="danger-outline",
            command=self._Close,
            width=12,
        ).grid(row=0, column=2, sticky=E, padx=(8, 0))

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

        self._Entry = ttk.Entry(InputRow, font=FONT_UI, bootstyle="light")
        self._Entry.grid(row=0, column=0, sticky=EW, padx=(0, 6), ipady=8)
        self._Entry.bind("<Return>", lambda _e: self._SendCurrent())

        NextColumn = 1
        if self._CanWhisperToDm:
            ttk.Button(
                InputRow,
                text="Whisper DM",
                bootstyle="info-outline",
                command=self._OpenWhisperDialog,
                width=11,
            ).grid(row=0, column=NextColumn, sticky=EW, padx=(0, 6), ipady=8)
            NextColumn += 1
            ttk.Label(
                Win,
                text=f"Tip: type {DM_WHISPER_COMMAND} your message for a private note to the DM",
                font=FONT_UI,
                bootstyle=BOOT_CHAT_META,
            ).grid(row=6, column=0, sticky=W, padx=14, pady=(0, 8))

        ttk.Button(
            InputRow,
            text="Send",
            bootstyle="success",
            command=self._SendCurrent,
        ).grid(row=0, column=NextColumn, sticky=EW, ipady=8)

        Win.protocol("WM_DELETE_WINDOW", self._Close)
        self._AutoSizeWindow()

    def Run(self) -> None:
        """Open chat and block until the window closes."""
        self._DrainNetworkEvents()
        self._BuildWindow()
        self._RecordLog("Session started.")
        for Line in self._HeaderLines:
            self._RecordLog(Line)
        self._Lines.append(ChatLine("system", "You joined the chat."))
        self._RecordLog("You joined the chat.")
        self._AppendNewLines()

        assert self._Window is not None
        self._Window.after(80, self._AutoSizeWindow)
        self._Window.after(self._PollMs, self._Poll)
        self._Entry.focus_set()
        self._Parent.wait_window(self._Window)

        self._DrainNetworkEvents()
        if self._OnLeave:
            self._OnLeave()
