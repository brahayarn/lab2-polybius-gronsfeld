"""Шифр Гронсфельда.

C_i = (P_i + d_(j(i) mod t)) mod m,  P_i = (C_i - d_(j(i) mod t)) mod m,
де j(i) рахує лише літери вибраного алфавіту: інші символи копіюються
і не споживають цифру ключа.
"""
from __future__ import annotations

import unicodedata
from typing import List

from .alphabets import Alphabet
from .errors import InvalidKeyError
from .text import prepare

_DIGITS = "0123456789"


def parse_key(key: str) -> List[int]:
    """Ключ — рядок цифр, а не число: початкові нулі мають значення."""
    digits = unicodedata.normalize("NFC", key).strip()
    if not digits:
        raise InvalidKeyError("цифровий ключ порожній.")
    for char in digits:
        # str.isdigit() прийняв би й «²» чи арабсько-індійські цифри.
        if char not in _DIGITS:
            raise InvalidKeyError(
                f"цифровий ключ містить {char!r}; дозволено лише цифри 0–9 без пробілів."
            )
    if set(digits) == {"0"}:
        raise InvalidKeyError("цифровий ключ складається лише з нулів і не змінює текст.")
    return [int(char) for char in digits]


def encrypt(text: str, key: str, alphabet: Alphabet) -> str:
    return _shift(text, parse_key(key), alphabet, direction=1)


def decrypt(text: str, key: str, alphabet: Alphabet) -> str:
    return _shift(text, parse_key(key), alphabet, direction=-1)


def _shift(text: str, shifts: List[int], alphabet: Alphabet, direction: int) -> str:
    index = {letter: i for i, letter in enumerate(alphabet.letters)}
    m = alphabet.size
    result = []
    letter_number = 0
    for char in prepare(text, alphabet):
        position = index.get(char)
        if position is None:
            result.append(char)
            continue
        shift = shifts[letter_number % len(shifts)]
        # Остача від додатного модуля в Python завжди в [0, m).
        result.append(alphabet.letters[(position + direction * shift) % m])
        letter_number += 1
    return "".join(result)
