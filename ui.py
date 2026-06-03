"""ttkbootstrap-based GUI: themed windows, menus, and dialogs."""

import threading
import tkinter as tk
from collections.abc import Callable
import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, BOTTOM, END, LEFT, RIGHT, TOP, W, X, Y
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame

from gui_theme import (
    BOOT_FOOTER,
    BOOT_MENU_BACK,
    BOOT_MENU_DEFAULT,
    BOOT_MENU_EXIT,
    BOOT_SUBTITLE,
    BOOT_TITLE,
    FONT_FOOTER,
    FONT_SUBTITLE,
    FONT_TITLE,
    FONT_UI,
    THEME_NAME,
)


class AppUI:
    """Main application window and navigation."""

    _Root: ttk.Window | None = None
    _Content: ttk.Frame | None = None
    _HeaderTitle: ttk.Label | None = None
    _HeaderSubtitle: ttk.Label | None = None
    _OnAction: Callable[[object], None] | None = None

    @classmethod
    def Initialize(cls, Title: str = "D&D Dice Roller") -> ttk.Window:
        if cls._Root is not None:
            return cls._Root

        Root = ttk.Window(
            title=Title,
            themename=THEME_NAME,
            size=(520, 580),
            minsize=(420, 480),
        )
        cls._Root = Root

        Header = ttk.Frame(Root, padding=(24, 20, 24, 8))
        Header.pack(fill=X)

        cls._HeaderTitle = ttk.Label(
            Header,
            text=Title,
            font=FONT_TITLE,
            bootstyle=BOOT_TITLE,
        )
        cls._HeaderTitle.pack(anchor=W)

        cls._HeaderSubtitle = ttk.Label(
            Header,
            text="",
            font=FONT_SUBTITLE,
            bootstyle=BOOT_SUBTITLE,
        )
        cls._HeaderSubtitle.pack(anchor=W, pady=(6, 0))

        ttk.Separator(Root, bootstyle="light").pack(fill=X, padx=16)

        cls._Content = ttk.Frame(Root, padding=24)
        cls._Content.pack(fill=BOTH, expand=True)

        Footer = ttk.Label(
            Root,
            text="LAN campaigns · Roll for initiative",
            font=FONT_FOOTER,
            bootstyle=BOOT_FOOTER,
        )
        Footer.pack(side=BOTTOM, pady=12)

        return Root

    @classmethod
    def Root(cls) -> ttk.Window:
        if cls._Root is None:
            cls.Initialize()
        assert cls._Root is not None
        return cls._Root

    @classmethod
    def ShowMenu(
        cls,
        Title: str,
        Subtitle: str,
        Actions: list,
        OnAction: Callable[[object], None],
    ) -> None:
        """Render a vertical list of menu buttons."""
        cls._OnAction = OnAction
        Root = cls.Root()

        if cls._HeaderTitle:
            cls._HeaderTitle.configure(text=Title)
        if cls._HeaderSubtitle:
            cls._HeaderSubtitle.configure(text=Subtitle or "")

        assert cls._Content is not None
        for Child in cls._Content.winfo_children():
            Child.destroy()

        Scroll = ScrolledFrame(cls._Content, autohide=True, bootstyle="round")
        Scroll.pack(fill=BOTH, expand=True)
        Inner = Scroll.container

        for Index, Action in enumerate(Actions):
            Label = Action.Label
            if Action.Icon:
                Label = f"{Action.Icon}  {Label}"

            Style = BOOT_MENU_DEFAULT
            if getattr(Action, "IsBack", False):
                Style = BOOT_MENU_BACK
            elif Action.Label == "Exit":
                Style = BOOT_MENU_EXIT

            Button = ttk.Button(
                Inner,
                text=Label,
                bootstyle=Style,
                command=lambda A=Action: cls._InvokeAction(A),
                width=36,
            )
            Button.pack(fill=X, pady=6, ipady=10)

        Root.update_idletasks()

    @classmethod
    def _InvokeAction(cls, Action: object) -> None:
        if cls._OnAction:
            cls._OnAction(Action)

    @classmethod
    def AskString(cls, Title: str, Prompt: str, Default: str = "") -> str | None:
        """Modal string input; None if cancelled."""
        Root = cls.Root()
        Dialog = ttk.Toplevel(Root)
        Dialog.title(Title)
        Dialog.transient(Root)
        Dialog.grab_set()
        Dialog.geometry("+%d+%d" % (Root.winfo_rootx() + 60, Root.winfo_rooty() + 120))

        Result: list[str | None] = [None]

        Frame = ttk.Frame(Dialog, padding=20)
        Frame.pack(fill=BOTH, expand=True)

        ttk.Label(Frame, text=Prompt, font=FONT_UI, bootstyle=BOOT_TITLE).pack(
            anchor=W, pady=(0, 8)
        )
        Entry = ttk.Entry(Frame, width=40, font=FONT_UI)
        Entry.pack(fill=X, ipady=6)
        Entry.insert(0, Default)
        Entry.focus_set()

        def Submit() -> None:
            Result[0] = Entry.get()
            Dialog.destroy()

        def Cancel() -> None:
            Result[0] = None
            Dialog.destroy()

        Buttons = ttk.Frame(Frame)
        Buttons.pack(fill=X, pady=(16, 0))
        ttk.Button(Buttons, text="OK", bootstyle="success", command=Submit).pack(
            side=LEFT, padx=(0, 8)
        )
        ttk.Button(Buttons, text="Cancel", bootstyle="secondary", command=Cancel).pack(
            side=LEFT
        )

        Entry.bind("<Return>", lambda _e: Submit())
        Dialog.protocol("WM_DELETE_WINDOW", Cancel)
        Dialog.wait_window()
        return Result[0]

    @classmethod
    def ShowNotice(cls, Message: str, Bootstyle: str = "info") -> None:
        if Bootstyle == "success":
            Messagebox.show_info(Message, title="Notice", parent=cls.Root())
        else:
            Messagebox.show_info(Message, title="Notice", parent=cls.Root())

    @classmethod
    def ShowError(cls, Message: str) -> None:
        Messagebox.show_error(Message, title="Error", parent=cls.Root())

    @classmethod
    def ShowProgress(cls, Message: str) -> Callable[[], None]:
        """Show a small busy dialog; call the returned function to close it."""
        Root = cls.Root()
        Dialog = ttk.Toplevel(Root)
        Dialog.title("Please wait")
        Dialog.transient(Root)
        Dialog.grab_set()
        Dialog.resizable(False, False)
        Dialog.geometry("+%d+%d" % (Root.winfo_rootx() + 80, Root.winfo_rooty() + 160))

        Frame = ttk.Frame(Dialog, padding=24)
        Frame.pack()
        ttk.Label(Frame, text=Message, font=FONT_UI, bootstyle=BOOT_TITLE).pack(
            pady=(0, 12)
        )
        Bar = ttk.Progressbar(Frame, mode="indeterminate", bootstyle="info-striped")
        Bar.pack(fill=X, ipady=4)
        Bar.start(12)

        def Close() -> None:
            try:
                Bar.stop()
                Dialog.grab_release()
                Dialog.destroy()
            except tk.TclError:
                pass

        Dialog.update()
        return Close

    @classmethod
    def RunOnMainThread(cls, Callback: Callable[[], None]) -> None:
        cls.Root().after(0, Callback)

    @classmethod
    def RunInBackground(
        cls,
        Worker: Callable[[], None],
        OnDone: Callable[[], None],
    ) -> None:
        def ThreadMain() -> None:
            Worker()
            cls.RunOnMainThread(OnDone)

        threading.Thread(target=ThreadMain, daemon=True).start()

    @classmethod
    def OpenChatWindow(
        cls,
        Title: str,
        Username: str,
        EventQueue,
        SendMessage: Callable[[str], None],
        HeaderLines: list[str] | None = None,
        OnLeave: Callable[[], None] | None = None,
        ShouldContinue: Callable[[], bool] | None = None,
        ShowLocalEcho: bool = True,
    ) -> None:
        from chat import CampaignChatWindow

        CampaignChatWindow(
            Parent=cls.Root(),
            Title=Title,
            Username=Username,
            EventQueue=EventQueue,
            SendMessage=SendMessage,
            HeaderLines=HeaderLines or [],
            OnLeave=OnLeave,
            ShouldContinue=ShouldContinue,
            ShowLocalEcho=ShowLocalEcho,
        ).Run()
