"""Спільні тестові дані."""
from polybius_gronsfeld.alphabets import LATIN, UKRAINIAN
from polybius_gronsfeld.square import build_square

UK_SQUARE = build_square(UKRAINIAN, "БЕЗПЕКА")
EN_SQUARE = build_square(LATIN, "SECURITY")

# Повідомлення для зворотності: по 10+ на мову, з Ґ Є І Ї / A Z, цифрами,
# розділовими знаками, переносами рядків.
UK_MESSAGES = [
    "СЛАВА УКРАЇНІ",
    "ґанок і їжак єднає ґудзик",
    "Їжачок їв яблука, а ґава — горіхи!",
    "Є 24 області та 1 АР, 2026 рік.",
    "П'ять ящиків, сімʼя, м’ята.",
    "Рядок перший\nрядок другий\n",
    "Табуляція\tі\r\nвіндовий перенос",
    "А",
    "ЩЬЮЯ012",
    "  пробіли на краях  ",
    "Чому? Тому що: (дужки) «лапки» і №5.",
]
EN_MESSAGES = [
    "HELLO WORLD",
    "Attack at dawn, 0600!",
    "The quick brown fox jumps over the lazy dog.",
    "Zebra & yak: 42 + 7 = 49",
    "Line one\nline two\n",
    "a",
    "ZZZZ",
    "  spaced  ",
    "It's (not) \"quoted\"?",
    "MIXED Case 123",
    "",
]
