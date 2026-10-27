"""Ключовий квадрат 6×6 і таблиці пошуку, побудовані один раз."""
from __future__ import annotations

from typing import Dict, List, Tuple

from .alphabets import Alphabet
from .errors import InvalidKeyError
from .text import normalize

SIDE = 6


class Square:
    """Квадрат Полібія: 36 унікальних символів, записаних по рядках.

    Координати (рядок, стовпець) нумеруються від 1 до 6.
    """

    def __init__(self, alphabet: Alphabet, symbols: str):
        _validate_symbols(alphabet, symbols)
        self.alphabet = alphabet
        self.symbols = symbols
        self.coordinates: Dict[str, Tuple[int, int]] = {
            symbol: (index // SIDE + 1, index % SIDE + 1) for index, symbol in enumerate(symbols)
        }

    def __contains__(self, char: str) -> bool:
        return char in self.coordinates

    def at(self, row: int, column: int) -> str:
        return self.symbols[(row - 1) * SIDE + (column - 1)]

    @property
    def rows(self) -> List[str]:
        return [self.symbols[i:i + SIDE] for i in range(0, SIDE * SIDE, SIDE)]

    def format(self) -> str:
        header = "    " + " ".join(str(column) for column in range(1, SIDE + 1))
        lines = [header] + [
            f"{number}   " + " ".join(row) for number, row in enumerate(self.rows, start=1)
        ]
        return "\n".join(lines)


def build_square(alphabet: Alphabet, keyword: str) -> Square:
    """Унікальні символи ключа в порядку першої появи, далі решта базового набору."""
    key = normalize(keyword, alphabet).strip()
    if not key:
        raise InvalidKeyError("ключове слово порожнє.")
    base = alphabet.square_symbols
    for char in key:
        if char not in base:
            raise InvalidKeyError(
                f"ключове слово містить {char!r}, якого немає в квадраті «{alphabet.name}» "
                f"({base})."
            )
    if not any(char in alphabet.letters for char in key):
        raise InvalidKeyError("ключове слово має містити щонайменше одну літеру.")
    head = "".join(dict.fromkeys(key))
    return Square(alphabet, head + "".join(symbol for symbol in base if symbol not in head))


def _validate_symbols(alphabet: Alphabet, symbols: str) -> None:
    if len(symbols) != SIDE * SIDE:
        raise InvalidKeyError(f"квадрат має містити {SIDE * SIDE} символи, а містить {len(symbols)}.")
    if sorted(symbols) != sorted(alphabet.square_symbols):
        raise InvalidKeyError(
            "квадрат має містити кожен символ базового набору рівно один раз."
        )
