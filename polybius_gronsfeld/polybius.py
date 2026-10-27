"""Два різні алгоритми на квадраті Полібія: координати та циклічний зсув за рядками."""
from __future__ import annotations

import re
from collections import Counter
from typing import Dict, NamedTuple

from .errors import InvalidCiphertextError, UnsupportedCharacterError
from .square import SIDE, Square
from .text import describe, normalize, prepare

STRICT = "strict"
STRIP = "strip"
ESCAPE = "escape"
COORDINATE_MODES = (STRICT, STRIP, ESCAPE)

_COORDINATE_TOKEN = re.compile(r"[1-6][1-6]")
_ESCAPE_TOKEN = re.compile(r"U\+[0-9A-F]{4,6}")


class Prepared(NamedTuple):
    text: str
    removed: Dict[str, int]  # які символи і скільки разів вилучено в режимі strip


# ---------------------------------------------------------------- координати

def prepare_coordinates(text: str, square: Square, mode: str = STRICT) -> Prepared:
    """Видалення сторонніх символів — окрема видима операція (режим strip)."""
    if mode not in COORDINATE_MODES:
        raise ValueError(f"невідомий режим координат {mode!r}")
    normalized = normalize(text, square.alphabet)
    if mode == ESCAPE:
        return Prepared(normalized, {})
    if mode == STRIP:
        kept = "".join(char for char in normalized if char in square)
        removed = Counter(char for char in normalized if char not in square)
        return Prepared(kept, dict(removed))
    for position, char in enumerate(normalized, start=1):
        if char not in square:
            raise UnsupportedCharacterError(
                f"символ {describe(char)} у позиції {position} відсутній у квадраті. "
                "Режим strict приймає лише символи квадрата. Щоб вилучити інші символи, "
                "оберіть режим strip (--strip), щоб закодувати їх — режим escape (--escape)."
            )
    return Prepared(normalized, {})


def encrypt_coordinates(text: str, square: Square, mode: str = STRICT) -> str:
    """Кожен символ -> «рядок стовпець»; токени розділено одним пробілом.

    У режимі escape символ поза квадратом записується токеном U+XXXX: він
    відрізняється від координат за формою, тож розбір залишається однозначним.
    """
    prepared = prepare_coordinates(text, square, mode).text
    tokens = []
    for char in prepared:
        if char in square:
            row, column = square.coordinates[char]
            tokens.append(f"{row}{column}")
        else:
            tokens.append(f"U+{ord(char):04X}")
    return " ".join(tokens)


def decrypt_coordinates(ciphertext: str, square: Square, allow_escapes: bool = False) -> str:
    """Суворий розбір: кожен токен — дві цифри 1..6 (або канонічний U+XXXX)."""
    chars = []
    for number, token in enumerate(ciphertext.split(), start=1):
        if _COORDINATE_TOKEN.fullmatch(token):
            chars.append(square.at(int(token[0]), int(token[1])))
        elif allow_escapes and _ESCAPE_TOKEN.fullmatch(token):
            chars.append(_decode_escape(token, number, square))
        else:
            raise InvalidCiphertextError(_explain_bad_token(token, number, allow_escapes))
    return "".join(chars)


def _decode_escape(token: str, number: int, square: Square) -> str:
    value = int(token[2:], 16)
    if value > 0x10FFFF or 0xD800 <= value <= 0xDFFF:
        raise InvalidCiphertextError(f"токен №{number} {token!r} не є допустимою кодовою точкою.")
    # Канонічна форма гарантує взаємно однозначне кодування.
    if token != f"U+{value:04X}":
        raise InvalidCiphertextError(
            f"токен №{number} {token!r} не в канонічній формі U+{value:04X}."
        )
    char = chr(value)
    if char in square:
        raise InvalidCiphertextError(
            f"токен №{number} {token!r} екранує символ квадрата {char!r}, "
            "який має кодуватися координатами."
        )
    return char


def _explain_bad_token(token: str, number: int, allow_escapes: bool) -> str:
    expected = "дві цифри від 1 до 6" + (" або U+XXXX" if allow_escapes else "")
    ascii_digits = token.isascii() and token.isdigit()
    if len(token) == 2 and ascii_digits:
        reason = "координата поза діапазоном 1..6"
    elif ascii_digits:
        reason = f"{len(token)} цифр замість двох"
    elif token.startswith("U+") and not allow_escapes:
        reason = "екранований символ без режиму --escape"
    else:
        reason = "сторонній текст"
    return f"некоректний токен №{number} {token!r}: {reason}. Очікується {expected}."


# ------------------------------------------------------- циклічний зсув рядків

def encrypt_row_shift(text: str, square: Square) -> str:
    """Символ замінюється символом під ним; після 6-го рядка — 1-й.

    У лінійному записі квадрата це зсув індексу на +6 за модулем 36,
    тобто проста одноалфавітна підстановка.
    """
    return prepare(text, square.alphabet).translate(_row_shift_table(square, +1))


def decrypt_row_shift(text: str, square: Square) -> str:
    return prepare(text, square.alphabet).translate(_row_shift_table(square, -1))


def _row_shift_table(square: Square, direction: int) -> Dict[int, int]:
    total = SIDE * SIDE
    shifted = "".join(
        square.symbols[(index + direction * SIDE) % total] for index in range(total)
    )
    return str.maketrans(square.symbols, shifted)
