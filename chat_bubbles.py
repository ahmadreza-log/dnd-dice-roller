"""Telegram-style rounded chat bubbles for the campaign log."""

import tkinter as tk
from tkinter import ttk

from dice import DiceRollResult
from gui_theme import (
    BG_CHAT_LOG,
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
    FONT_DICE_LABEL,
    FONT_DICE_TOTAL,
    FONT_DICE_VALUE,
    FONT_UI,
)
from player_colors import PRIVATE_ROLL_SCHEME, PlayerColorRegistry, PlayerColorScheme


class ChatLineView:
    """Minimal protocol for lines rendered into the bubble feed."""

    Kind: str
    Body: str
    Roll: DiceRollResult | None
    Username: str


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

    def Append(self, Line: ChatLineView) -> None:
        if Line.Kind in ("dice_roll", "private_dice_roll") and Line.Roll is not None:
            self._AppendDiceRoll(
                Line.Username,
                Line.Roll,
                Private=Line.Kind == "private_dice_roll",
            )
            return

        Handlers = {
            "chat": self._AppendChat,
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

    def _AppendJoin(self, Line: ChatLineView) -> None:
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

    def _AppendLeave(self, Line: ChatLineView) -> None:
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

    def _AppendChat(self, Line: ChatLineView) -> None:
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
