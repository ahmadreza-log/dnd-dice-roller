import random
from dataclasses import dataclass


MAX_DICE_PER_ROLL = 100
ROLL_WIRE_PREFIX = "🎲ROLL|"

DICE_TYPES: list[tuple[str, int]] = [
    ("D4", 4),
    ("D6", 6),
    ("D8", 8),
    ("D10", 10),
    ("D12", 12),
    ("D20", 20),
    ("D100", 100),
]


@dataclass(frozen=True)
class DiceRollResult:
    """Outcome of one dice roll action."""

    DiceLabel: str
    Sides: int
    Count: int
    Rolls: list[int]

    @property
    def Total(self) -> int:
        return sum(self.Rolls)

    def IsNat20(self, Value: int) -> bool:
        return self.Sides == 20 and self.Count == 1 and Value == 20

    def IsNat1(self, Value: int) -> bool:
        return self.Sides == 20 and self.Count == 1 and Value == 1


class DiceRoller:
    """Roll polyhedral dice and format results for campaign chat."""

    @staticmethod
    def Roll(Sides: int, Count: int) -> list[int]:
        return [random.randint(1, Sides) for _ in range(Count)]

    @classmethod
    def RollDice(cls, DiceLabel: str, Sides: int, Count: int) -> DiceRollResult:
        return DiceRollResult(DiceLabel, Sides, Count, cls.Roll(Sides, Count))

    @staticmethod
    def FormatWireMessage(Result: DiceRollResult) -> str:
        """Compact network payload parsed back for rich chat rendering."""
        RollsText = ",".join(str(Value) for Value in Result.Rolls)
        return (
            f"{ROLL_WIRE_PREFIX}{Result.DiceLabel}|{Result.Sides}|"
            f"{Result.Count}|{RollsText}"
        )

    @staticmethod
    def ParseWireMessage(Text: str) -> DiceRollResult | None:
        Text = Text.strip()
        if not Text.startswith(ROLL_WIRE_PREFIX):
            return None

        Parts = Text[len(ROLL_WIRE_PREFIX) :].split("|")
        if len(Parts) != 4:
            return None

        DiceLabel, SidesText, CountText, RollsText = Parts
        try:
            Sides = int(SidesText)
            Count = int(CountText)
            Rolls = [int(Value) for Value in RollsText.split(",") if Value]
        except ValueError:
            return None

        if Count < 1 or len(Rolls) != Count:
            return None

        return DiceRollResult(DiceLabel, Sides, Count, Rolls)

    @staticmethod
    def ParseBracketedMessage(Text: str) -> tuple[str, DiceRollResult] | None:
        """Parse '[Username] 🎲ROLL|...' from the chat log."""
        Text = Text.strip()
        if not Text.startswith("[") or "]" not in Text:
            return None

        BracketEnd = Text.index("]")
        Username = Text[1:BracketEnd].strip()
        Body = Text[BracketEnd + 1 :].strip()
        Result = DiceRoller.ParseWireMessage(Body)
        if not Username or Result is None:
            return None

        return Username, Result
