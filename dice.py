import random


MAX_DICE_PER_ROLL = 100

DICE_TYPES: list[tuple[str, int]] = [
    ("D4", 4),
    ("D6", 6),
    ("D8", 8),
    ("D10", 10),
    ("D12", 12),
    ("D20", 20),
    ("D100", 100),
]


class DiceRoller:
    """Roll polyhedral dice and format results for campaign chat."""

    @staticmethod
    def Roll(Sides: int, Count: int) -> list[int]:
        return [random.randint(1, Sides) for _ in range(Count)]

    @staticmethod
    def FormatResult(DiceLabel: str, Sides: int, Count: int, Rolls: list[int]) -> str:
        Total = sum(Rolls)
        RollsText = ", ".join(str(Value) for Value in Rolls)
        if Count == 1:
            return f"🎲 {DiceLabel}: {RollsText}"
        return f"🎲 {Count}×{DiceLabel}: {RollsText} (total {Total})"

    @classmethod
    def RollAndFormat(cls, DiceLabel: str, Sides: int, Count: int) -> str:
        Rolls = cls.Roll(Sides, Count)
        return cls.FormatResult(DiceLabel, Sides, Count, Rolls)
