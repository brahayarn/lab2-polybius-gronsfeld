"""Консольний інтерфейс. Уся криптографія — у модулях пакета, тут лише введення/виведення."""
from __future__ import annotations

import argparse
import sys
from typing import Callable, List, Optional, Tuple

from . import __version__, analysis, gronsfeld, polybius
from .alphabets import ALPHABETS, get_alphabet
from .errors import CipherError
from .fileio import read_text, write_text_atomic
from .square import build_square
from .text import describe

EXIT_OK = 0
EXIT_ERROR = 1

COORDINATES = "coordinates"
ROW_SHIFT = "row-shift"
GRONSFELD = "gronsfeld"
CIPHERS = {
    COORDINATES: "квадрат Полібія, координати рядок-стовпець (ключ: ключове слово)",
    ROW_SHIFT: "квадрат Полібія, циклічний зсув за рядками (ключ: ключове слово)",
    GRONSFELD: "шифр Гронсфельда (ключ: рядок цифр, напр. 31415)",
}

RULES = """\
Правила підготовки тексту
  Кодування:    файли читаються і записуються як UTF-8 (BOM на вході ігнорується).
  Нормалізація: Unicode NFC перед перевіркою ключа і тексту.
  Регістр:      до верхнього регістру переводяться лише літери вибраного алфавіту.
  Алфавіт:      обирається явно (--alphabet uk | en), не вгадується.
    uk: 33 літери АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ, квадрат = літери + 0 1 2
    en: 26 літер ABCDEFGHIJKLMNOPQRSTUVWXYZ,        квадрат = літери + 0..9
  Квадрат:      унікальні символи ключа, далі решта набору; 6 рядків по 6.
  coordinates:  кожен символ -> «рядок стовпець» (1..6), токени через пробіл.
                strict (типово): лише символи квадрата, інакше помилка;
                --strip: видимо вилучає символи поза квадратом (звіт у stderr);
                --escape: символ поза квадратом -> токен U+XXXX (повна зворотність).
  row-shift:    символ квадрата -> символ рядком нижче (6-й -> 1-й);
                інші символи без змін. Цифри квадрата теж зсуваються.
  gronsfeld:    змінюються лише літери алфавіту (mod 33 або 26); пробіли, цифри,
                розділові знаки не змінюються і не споживають цифру ключа.
  Сторонні літери (інша абетка, напр. латинська I серед українських) — помилка.
"""

Transform = Callable[[str], Tuple[str, List[str]]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m polybius_gronsfeld",
        description="Квадрат Полібія та шифр Гронсфельда для українського і латинського "
        "тексту. Навчальні алгоритми — не для захисту реальних даних.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Приклади:\n"
        "  python -m polybius_gronsfeld encrypt -a uk -c coordinates -k БЕЗПЕКА -t СЛАВА\n"
        "  python -m polybius_gronsfeld decrypt -a en -c row-shift -k SECURITY -t OYVVZ\n"
        "  python -m polybius_gronsfeld encrypt -a uk -c gronsfeld -k 31415 -i in.txt -o out.txt\n"
        "  python -m polybius_gronsfeld square -a uk -k БЕЗПЕКА",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True, metavar="КОМАНДА")

    for name, title in (("encrypt", "зашифрувати"), ("decrypt", "розшифрувати")):
        command = commands.add_parser(name, help=title, description=f"{title.capitalize()} текст.")
        _add_alphabet(command)
        command.add_argument("-c", "--cipher", required=True, choices=CIPHERS,
                             help="; ".join(f"{k} — {v}" for k, v in CIPHERS.items()))
        command.add_argument("-k", "--key", required=True,
                             help="ключове слово (Полібій) або рядок цифр (Гронсфельд)")
        modes = command.add_mutually_exclusive_group()
        if name == "encrypt":
            modes.add_argument("--strip", action="store_true",
                               help="coordinates: вилучити символи поза квадратом (видимо)")
        modes.add_argument("--escape", action="store_true",
                           help="coordinates: кодувати символи поза квадратом токенами U+XXXX")
        command.add_argument("--show-square", action="store_true",
                             help="показати активний квадрат (у stderr)")
        _add_io(command, with_output=True)

    square = commands.add_parser("square", help="показати ключовий квадрат 6×6")
    _add_alphabet(square)
    square.add_argument("-k", "--key", required=True, help="ключове слово")

    commands.add_parser("rules", help="показати правила підготовки тексту")

    analyze = commands.add_parser("analyze",
                                  help="частоти тексту, row shift і координат (додаткове завдання)")
    _add_alphabet(analyze)
    analyze.add_argument("-k", "--key", required=True, help="ключове слово квадрата")
    analyze.add_argument("--top", type=int, default=10, help="кількість рядків (типово %(default)s)")
    _add_io(analyze, with_output=False)
    return parser


def _add_alphabet(command: argparse.ArgumentParser) -> None:
    command.add_argument("-a", "--alphabet", required=True, choices=ALPHABETS,
                         help="uk — український, en — латинський (обов'язково, не вгадується)")


def _add_io(command: argparse.ArgumentParser, with_output: bool) -> None:
    source = command.add_mutually_exclusive_group()
    source.add_argument("-t", "--text", help="текст у командному рядку")
    source.add_argument("-i", "--input", metavar="ФАЙЛ", help="вхідний UTF-8 файл")
    if with_output:
        command.add_argument("-o", "--output", metavar="ФАЙЛ",
                             help="вихідний UTF-8 файл (інакше результат виводиться на екран)")


def build_transform(args: argparse.Namespace) -> Transform:
    """Перевіряє алфавіт, ключ і режим ще до читання тексту."""
    alphabet = get_alphabet(args.alphabet)
    encrypting = args.command == "encrypt"
    strip = getattr(args, "strip", False)
    if (strip or args.escape) and args.cipher != COORDINATES:
        raise CipherError("параметри --strip і --escape застосовуються лише до coordinates.")
    if args.show_square and args.cipher == GRONSFELD:
        raise CipherError("у шифрі Гронсфельда немає квадрата; --show-square недоступний.")

    if args.cipher == GRONSFELD:
        gronsfeld.parse_key(args.key)
        operation = gronsfeld.encrypt if encrypting else gronsfeld.decrypt
        return lambda text: (operation(text, args.key, alphabet), [])

    square = build_square(alphabet, args.key)
    notes = [f"Активний квадрат ({alphabet.name}):\n{square.format()}"] if args.show_square else []

    if args.cipher == ROW_SHIFT:
        operation = polybius.encrypt_row_shift if encrypting else polybius.decrypt_row_shift
        return lambda text: (operation(text, square), notes)

    if not encrypting:
        return lambda text: (polybius.decrypt_coordinates(text, square, args.escape), notes)

    mode = polybius.STRIP if strip else polybius.ESCAPE if args.escape else polybius.STRICT

    def encrypt_coordinates(text: str) -> Tuple[str, List[str]]:
        removed = polybius.prepare_coordinates(text, square, mode).removed
        extra = [_describe_removed(removed)] if mode == polybius.STRIP else []
        return polybius.encrypt_coordinates(text, square, mode), notes + extra
    return encrypt_coordinates


def _describe_removed(removed: dict) -> str:
    if not removed:
        return "Підготовка strip: жодного символу не вилучено."
    parts = ", ".join(f"{describe(char)} ×{count}" for char, count in sorted(removed.items()))
    return f"Підготовка strip: вилучено символів — {sum(removed.values())}: {parts}."


def read_input(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.input is not None:
        return read_text(args.input)
    if sys.stdin.isatty():
        print("Введіть текст і завершіть введення Ctrl-D (Windows: Ctrl-Z, Enter):",
              file=sys.stderr)
    return sys.stdin.read()


def write_output(args: argparse.Namespace, result: str) -> None:
    if args.output is not None:
        write_text_atomic(args.output, result)
        print(f"Результат записано у {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(result if result.endswith("\n") else result + "\n")


def run_cipher(args: argparse.Namespace) -> None:
    transform = build_transform(args)
    result, notes = transform(read_input(args))
    for note in notes:
        print(note, file=sys.stderr)
    write_output(args, result)


def run_square(args: argparse.Namespace) -> None:
    alphabet = get_alphabet(args.alphabet)
    print(f"Квадрат ({alphabet.name}), ключ {args.key}:")
    print(build_square(alphabet, args.key).format())


def run_analyze(args: argparse.Namespace) -> None:
    if args.top < 1:
        raise CipherError("--top має бути додатним.")
    square = build_square(get_alphabet(args.alphabet), args.key)
    print(analysis.format_table(read_input(args), square, args.top))


def _use_utf8_streams() -> None:
    # Консоль Windows може мати іншу кодову сторінку; вимога роботи — UTF-8.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    _use_utf8_streams()
    args = build_parser().parse_args(argv)
    handlers = {"rules": lambda _: print(RULES, end=""), "square": run_square,
                "analyze": run_analyze, "encrypt": run_cipher, "decrypt": run_cipher}
    try:
        handlers[args.command](args)
    except CipherError as error:
        print(f"Помилка: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK
