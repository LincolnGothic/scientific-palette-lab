from dataclasses import dataclass, asdict
from pathlib import Path

JOURNALS = {
    "Nature": ("0028-0836", "1476-4687"),
    "Science": ("0036-8075", "1095-9203"),
    "Cell": ("0092-8674", "1097-4172"),
}
KINDS = ("data", "flowchart", "other", "unknown")
PALETTE_TYPES = ("categorical", "sequential", "diverging", "roles", "unknown")
ROLES = ("unassigned", "fill", "border", "text", "connector", "decision", "group")


@dataclass
class Study:
    start_year: int = 2021
    end_year: int = 2025
    journals: tuple = tuple(JOURNALS)
    delta_e: float = 8.0
    reviewed_only: bool = True

    def validate(self):
        if not (1900 <= self.start_year <= self.end_year <= 2100):
            raise ValueError("Enter a valid year range.")
        if not self.journals or any(j not in JOURNALS for j in self.journals):
            raise ValueError("Only Nature, Science, and Cell are supported.")
        if not 1 <= self.delta_e <= 25:
            raise ValueError("Color similarity threshold must be between 1 and 25 ΔE76.")
        return self

    def to_dict(self):
        return asdict(self)


def data_root(value=None):
    return Path(value or Path.cwd() / "data").expanduser().resolve()
