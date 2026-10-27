"""Узгоджені набори символів. Алфавіт завжди обирається явно, мова не вгадується."""
from __future__ import annotations

from typing import Dict, NamedTuple

from .errors import CipherError


class Alphabet(NamedTuple):
    code: str
    name: str
    letters: str
    digits: str

    @property
    def square_symbols(self) -> str:
        """36 символів квадрата 6×6: літери, потім цифри."""
        return self.letters + self.digits

    @property
    def size(self) -> int:
        return len(self.letters)


UKRAINIAN = Alphabet("uk", "український", "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ", "012")
LATIN = Alphabet("en", "латинський", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789")

ALPHABETS: Dict[str, Alphabet] = {alphabet.code: alphabet for alphabet in (UKRAINIAN, LATIN)}


def get_alphabet(code: str) -> Alphabet:
    try:
        return ALPHABETS[code]
    except KeyError:
        raise CipherError(
            f"невідомий алфавіт {code!r}; підтримуються: {', '.join(ALPHABETS)}."
        ) from None
