"""Підготовка тексту: NFC і верхній регістр лише для літер вибраного алфавіту."""
from __future__ import annotations

import unicodedata

from .alphabets import Alphabet
from .errors import UnsupportedCharacterError

# Український апостроф U+02BC формально є літерою-модифікатором (Lm),
# але в тексті відіграє роль розділового знака.
_APOSTROPHES = frozenset("'ʼ’`")


def normalize(text: str, alphabet: Alphabet) -> str:
    """NFC, далі верхній регістр тільки для підтримуваних літер.

    Інші символи не змінюються: str.upper() для всього тексту могла б
    перетворити, наприклад, турецьку «ı» на латинську «I» або «ß» на «SS».
    """
    to_upper = str.maketrans(alphabet.letters.lower(), alphabet.letters)
    return unicodedata.normalize("NFC", text).translate(to_upper)


def validate_foreign_letters(text: str, alphabet: Alphabet) -> None:
    """Відхиляє літери інших алфавітів і окремі комбіновані знаки.

    Так ловиться типова помилка: латинська «I» чи «A» серед українських
    літер (омогліфи) або забутий параметр вибору алфавіту.
    """
    for position, char in enumerate(text, start=1):
        if char in alphabet.letters or char in _APOSTROPHES:
            continue
        category = unicodedata.category(char)
        if category[0] in "LM":
            name = unicodedata.name(char, "без назви")
            raise UnsupportedCharacterError(
                f"символ {char!r} (U+{ord(char):04X}, {name}) у позиції {position} "
                f"не є літерою алфавіту «{alphabet.name}». Перевірте вибір алфавіту "
                "(--alphabet) або чи не вставлено схожу літеру з іншої абетки."
            )


def prepare(text: str, alphabet: Alphabet) -> str:
    """Підготовка для row shift і Гронсфельда: сторонні не-літери зберігаються."""
    prepared = normalize(text, alphabet)
    validate_foreign_letters(prepared, alphabet)
    return prepared


def describe(char: str) -> str:
    """Читабельна назва символу для повідомлень (пробіл і перенос видно явно)."""
    return f"{char!r} (U+{ord(char):04X})"
