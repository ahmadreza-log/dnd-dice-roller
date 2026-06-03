"""Per-player bubble colors with readable contrast on dark chat backgrounds."""

from dataclasses import dataclass

from network import DM_DISPLAY_NAME


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
