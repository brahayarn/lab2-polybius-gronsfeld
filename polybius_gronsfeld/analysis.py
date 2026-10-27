"""Додаткове завдання: частоти відкритого тексту та результатів обох режимів Полібія."""
from __future__ import annotations

from collections import Counter
from typing import List, Tuple

from .polybius import STRIP, encrypt_coordinates, encrypt_row_shift, prepare_coordinates
from .square import Square

Frequencies = List[Tuple[str, int]]


def top(counter: Counter, limit: int) -> Frequencies:
    # Сортування за спаданням, а за рівної частоти — за символом, для відтворюваності.
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]


def compare_polybius_modes(text: str, square: Square, limit: int = 10) -> Tuple[Frequencies, ...]:
    """Частоти символів квадрата у тексті, row shift і токенів координат."""
    plain = prepare_coordinates(text, square, STRIP).text
    shifted = encrypt_row_shift(plain, square)
    tokens = encrypt_coordinates(plain, square).split()
    return (
        top(Counter(plain), limit),
        top(Counter(shifted), limit),
        top(Counter(tokens), limit),
    )


def format_table(text: str, square: Square, limit: int = 10) -> str:
    plain, shifted, tokens = compare_polybius_modes(text, square, limit)
    lines = [f"{'Ранг':>4}  {'Текст':<10}{'Row shift':<12}{'Координати':<12}"]
    for rank, (p, s, t) in enumerate(zip(plain, shifted, tokens), start=1):
        lines.append(f"{rank:>4}  {p[0]} {p[1]:<8}{s[0]} {s[1]:<10}{t[0]} {t[1]:<9}")
    return "\n".join(lines)
